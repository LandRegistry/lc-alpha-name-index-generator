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


def message_received(body, message):
    logging.info("Received new registrations: {}".format(str(body)))


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
