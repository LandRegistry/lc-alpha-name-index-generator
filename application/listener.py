from application.routes import app
import kombu
import socket
import logging
from kombu.common import maybe_declare
from amqp import AccessRefused
import requests
import json


class NamesError(Exception):
    def __init__(self, value):
        self.value = value
        super(NamesError, self).__init__(value)

    def __str__(self):
        return repr(self.value)


def setup_incoming(hostname): # pragma: no cover
    connection = kombu.Connection(hostname=hostname)
    connection.connect()
    exchange = kombu.Exchange(type="direct", name="register_queue")
    channel = connection.channel()
    exchange.maybe_bind(channel)
    maybe_declare(exchange, channel)

    queue = kombu.Queue(name='register_queue', exchange=exchange, routing_key='#')
    queue.maybe_bind(channel)
    try:
        queue.declare()
    except AccessRefused:
        logging.error("Access Refused")

    consumer = kombu.Consumer(channel, queues=queue, callbacks=[message_received], accept=['json'])
    consumer.consume()
    return connection, consumer


def setup_error_queue(hostname):
    connection = kombu.Connection(hostname=hostname)
    producer = connection.SimpleQueue('names_error')
    return producer


def extract_name(proprietor):
    name = proprietor['name']
    prop_name = {'forenames': [], 'surname': '', 'full_name': ''}

    if 'name_category' in name:
        if name['name_category'] == 'PRIVATE INDIVIDUAL':
            prop_name['forenames'] = name['forename'].split()
            prop_name['surname'] = name['surname']
            prop_name['full_name'] = "{} {}".format(name['forename'], name['surname'])
            prop_type = 'Private'
            if 'title' in name:
                prop_name['title'] = name['title']
                prop_name['full_name'] = " ".join([prop_name['title'], prop_name['full_name']])

            if 'decoration' in name:
                prop_name['decoration'] = name['decoration']
                prop_name['full_name'] = " ".join([prop_name['full_name'], prop_name['decoration']])

        elif name['name_category'] == 'LIMITED COMPANY OR PUBLIC LIMITED COMPANY':
            prop_name['full_name'] = name['non_private_individual_name']
            prop_type = 'Non-Private'  # TODO: don't really need non-PI names for April...
        # Have seen example with no category
    elif 'non_private_individual_name' in name:
        prop_name['full_name'] = name['non_private_individual_name']
        prop_type = 'Non-Private'
    else:
        raise NamesError("Unable to parse name from {}".format(json.dumps(proprietor)))
    return prop_name, prop_type


def extract_ownership_records(data):
    office = data['data']['dlr']
    title_no = data['data']['title_number']
    sub_reg = 'Proprietorship'

    records = []
    for group in (g for g in data['data']['groups'] if g['category'] == 'OWNERSHIP'):
        for entry in (e for e in group['entries'] if e['role_code'] == 'RPRO' and e['status'] == 'Current'):
            for infill in (i for i in entry['infills'] if i['type'] == 'Proprietor'):
                proprietors = infill['proprietors']
                for proprietor in proprietors:
                    prop_name, prop_type = extract_name(proprietor)
                    records.append({
                        'title_number': title_no,
                        'registered_proprietor': prop_name,
                        'office': office,
                        'sub_register': sub_reg,
                        'name_type': prop_type
                    })
    return records


def extract_charge_records(data):
    # TODO: Get some data created by the legacy systems
    office = data['data']['dlr']
    title_no = data['data']['title_number']
    sub_reg = 'Charge'

    records = []
    for group in (g for g in data['data']['groups'] if g['category'] == 'CHARGE'):
        for entry in (e for e in group['entries'] if e['role_code'] == 'CCHR' and e['status'] == 'Current'):
            for infill in (i for i in entry['infills'] if i['type'] == 'Charge Proprietor'):
                for proprietor in infill['proprietors']:
                    prop_name, prop_type = extract_name(proprietor)
                    records.append({
                        'title_number': title_no,
                        'registered_proprietor': prop_name,
                        'office': office,
                        'sub_register': sub_reg,
                        'name_type': prop_type
                    })
    return records


def get_iopn_records(data):
    records = extract_ownership_records(data)
    records += extract_charge_records(data)

    url = app.config['NAMES_SEARCH_URI'] + '/names'
    headers = {'Content-Type': 'application/json'}

    logging.info('%s POST', url)
    response = requests.post(url, data=json.dumps(records), headers=headers)
    logging.info('%s response %d', url, response.status_code)

    if response.status_code != 201:
        raise NamesError("Search API non-201 response: {}".format(response.status_code))

    return records


def message_received(body, message):
    logging.info("Received new registrations: %s", str(body))
    get_iopn_records(body)
    message.ack()


def listen(incoming_connection, error_producer, run_forever=True):
    logging.info('Listening for new registrations')

    while True:
        try:
            incoming_connection.drain_events()
        except KeyboardInterrupt:  # pragma: no cover
            logging.info("Interrupted")
            break
        except (socket.error, socket.timeout, NamesError) as exception:  # pragma: no cover
            logging.error('Exception %s: %s', type(exception).__name__, str(exception))
            error = {
                'exception_class': type(exception).__name__,
                'error_message': str(exception)
            }
            error_producer.put(error)
        if not run_forever:
            break


def run():
    hostname = "amqp://{}:{}@{}:{}".format(app.config['MQ_USERNAME'], app.config['MQ_PASSWORD'],
                                           app.config['MQ_HOSTNAME'], app.config['MQ_PORT'])
    incoming_connection, incoming_consumer = setup_incoming(hostname)
    error_producer = setup_error_queue(hostname)

    listen(incoming_connection, error_producer)
    incoming_consumer.close()
