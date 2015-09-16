

class Config(object):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    MQ_USERNAME = "mquser"
    MQ_PASSWORD = "mqpassword"
    MQ_HOSTNAME = "localhost"
    MQ_PORT = "5672"
    SEARCH_API_URI = "http://localhost:5013"


class PreviewConfig(Config):
    MQ_USERNAME = "mquser"
    MQ_PASSWORD = "mqpassword"
    MQ_HOSTNAME = "localhost"
    MQ_PORT = "5672"
    SEARCH_API_URI = "http://localhost:5013"
