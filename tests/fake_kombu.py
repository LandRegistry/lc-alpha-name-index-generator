from application.listener import NamesError, message_received


class FakeConnection(object):
    def drain_events(self):
        pass

    def SimpleQueue(self):
        return FakeQueue()

    def Queue(self):
        return FakeQueue()

    def connect(self):
        pass

    def channel(self):
        return FakeChannel()


class FakeMessage(object):
    def __init__(self, data):
        self.acked = False
        self.data = data

    def ack(self):
        self.acked = True


class FakeWorkingConnection(FakeConnection):
    def __init__(self, fake_data):
        self.fake_message = FakeMessage(fake_data)

    def drain_events(self):
        message_received(self.fake_message.data, self.fake_message)
        pass


class FakeFailingConnection(object):
    def drain_events(self):
        raise NamesError("Search API non-201 response: 500")


class FakeQueue(object):
    def __init__(self):
        self.data = None

    def maybe_bind(self, *args):
        pass

    def declare(self):
        pass

    def put(self, data):
        self.data = data


class FakeChannel(object):
    pass


class FakeExchange(object):
    def maybe_bind(self):
        self


class FakeConsumer(object):
    def consume(self):
        pass