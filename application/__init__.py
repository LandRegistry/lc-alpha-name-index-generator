import os
from flask import Flask
import threading
from log.logger import setup_logging
from application.listener import run


process_thread = threading.Thread(name='synchroniser', target=run)
process_thread.daemon = True
process_thread.start()
