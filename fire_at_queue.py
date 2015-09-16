import kombu
import sys
import os
import json


def setup_queue(hostname):
    conn = kombu.Connection(hostname=hostname)
    producer = conn.SimpleQueue('register_queue')
    return conn, producer

if len(sys.argv) != 2:
    print("Invalid arguments", file=sys.stderr)
    sys.exit(2)

filename = sys.argv[1]
if not os.path.exists(filename):
    print("File not found", file=sys.stderr)
    sys.exit(2)

data = json.loads(open(filename, 'r').read())
connection, queue = setup_queue("amqp://mquser:mqpassword@localhost:5672")
queue.put(data)
queue.close()
