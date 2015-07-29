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


class FakeQueue(object):
    def maybe_bind(self, *args):
        pass

    def declare(self):
        pass


class FakeChannel(object):
    pass


class FakeExchange(object):
    def maybe_bind(self):
        self


class FakeConsumer(object):
    def consume(self):
        pass