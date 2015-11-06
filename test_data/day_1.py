# Will throw the JSON from directory 1 at the name index
# This is a data load.
import kombu
import os
import json


def setup_queue(hostname):
    conn = kombu.Connection(hostname=hostname)
    producer = conn.SimpleQueue('register_queue')
    return conn, producer


here = os.path.dirname(os.path.realpath(__file__))
path = os.path.join(here, "1")
files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

connection, queue = setup_queue("amqp://mquser:mqpassword@localhost:5672")

for file in files:
    data = json.loads(open(os.path.join(path, file)).read())
    queue.put(data)

queue.close()
