from application import app
import kombu
import logging
from kombu.common import maybe_declare
from amqp import AccessRefused
from flask import Response


def setup_incoming(hostname):
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
    # logging.debug("queue name, exchange, binding_key: {}, {}, {}".format(queue.name, queue.exchange, queue.routing_key))

    consumer = kombu.Consumer(channel, queues=queue, callbacks=[message_received], accept=['json'])
    consumer.consume()

    # logging.debug('channel_id: {}'.format(consumer.channel.channel_id))
    # logging.debug('queue(s): {}'.format(consumer.queues))
    return connection, consumer


def setup_error_queue(hostname):
    connection = kombu.Connection(hostname=hostname)
    producer = connection.SimpleQueue('names_error')
    return connection, producer


def extract_ownership_records(data):
    office = data['data']['dlr']
    title_no = data['data']['title_number']
    sub_reg = 'Proprietorship'
    name_type = 'Standard'

    records = []
    for group in (g for g in data['data']['groups'] if g['category'] == 'OWNERSHIP'):
        for entry in group['entries']:
            if entry['role_code'] == 'RPRO' and entry['status'] == 'Current':
                proprietors = entry['infills'][0]['proprietors']  # TODO: unsafe assumption?
                for proprietor in proprietors:
                    name = proprietor['name']
                    if name['name_category'] == 'PRIVATE INDIVIDUAL':
                        prop_name = "{} {}".format(name['forename'], name['surname'])
                        records.append({
                            'title_number': title_no,
                            'registered_proprietor': prop_name,
                            'office': office,
                            'sub_register': sub_reg,
                            'name_type': name_type
                        })
    return records


def extract_charge_records(data):
    # TODO: Get some data created by the legacy systems
    return []


def get_iopn_records(data):
    records = extract_ownership_records(data)
    records += extract_charge_records(data)
    print(records)
    return records


def message_received(body, message):
    logging.info("Received new registrations: {}".format(str(body)))
    get_iopn_records(body)
    message.ack()


def listen(incoming_connection, error_producer, run_forever=True):
    logging.info('Listening for new registrations')

    while True:
        try:
            incoming_connection.drain_events()
        except KeyboardInterrupt:
            logging.info("Interrupted")
            break

        if not run_forever:
            break


def run():
    hostname = "amqp://{}:{}@{}:{}".format(app.config['MQ_USERNAME'], app.config['MQ_PASSWORD'],
                                           app.config['MQ_HOSTNAME'], app.config['MQ_PORT'])
    incoming_connection, incoming_consumer = setup_incoming(hostname)
    error_connection, error_producer = setup_error_queue(hostname)

    listen(incoming_connection, error_producer)
    incoming_consumer.close()


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)
