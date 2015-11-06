from flask import Flask, Response
from log.logger import setup_logging
import os
import threading
import logging
import requests
import json


app = Flask(__name__)
app.config.from_object(os.getenv('SETTINGS', "config.DevelopmentConfig"))

setup_logging(app.config['DEBUG'])


def check_names_search_health():
    return requests.get(app.config['NAMES_SEARCH_URI'] + '/health')


application_dependencies = [
    {
        "name": "names-search",
        "check": check_names_search_health
    }
]


def healthcheck():
    result = {
        'status': 'OK',
        'dependencies': {}
    }

    logging.info('Enumerate Threads')
    for t in threading.enumerate():
        logging.info(t.name)

    threads = [t for t in threading.enumerate() if t.name == 'name-listener']
    alive = "Alive" if (len(threads) > 0 and threads[0].is_alive()) else "Failed"
    result['dependencies']['listener-thread'] = alive

    status = 200
    for dependency in application_dependencies:
        response = dependency["check"]()
        result['dependencies'][dependency['name']] = str(response.status_code) + ' ' + response.reason
        data = json.loads(response.content.decode('utf-8'))
        print(data)
        for key in data['dependencies']:
            result['dependencies'][key] = data['dependencies'][key]

    return Response(json.dumps(result), status=status, mimetype='application/json')


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


@app.route('/health', methods=['GET'])
def get_health():
    return healthcheck()