from flask import Flask, Response
from log.logger import setup_logging
import os


app = Flask(__name__)
app.config.from_object(os.getenv('SETTINGS', "config.DevelopmentConfig"))

setup_logging(app.config['DEBUG'])


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)
