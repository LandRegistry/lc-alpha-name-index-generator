import pytest
from application.listener import app, get_iopn_records, NamesError, listen
from unittest import mock
import os
import json
from tests.fake_kombu import FakeConnection, FakeExchange, FakeConsumer, FakeQueue, FakeFailingConnection, \
                             FakeWorkingConnection


class FakeResponse(object):
    def __init__(self, content=None, status_code=200):
        super(FakeResponse, self).__init__()
        self.data = content
        self.status_code = status_code


directory = os.path.dirname(__file__)
single_PI_proprietor = json.loads(open(os.path.join(directory, 'data/single_PI_proprietor.json'), 'r').read())
has_charge = json.loads(open(os.path.join(directory, 'data/simple_PI_has_charge.json'), 'r').read())


class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def mock_kombu(function):
        @mock.patch('kombu.Connection', return_value=FakeConnection())
        @mock.patch('kombu.common.maybe_declare')
        @mock.patch('kombu.Exchange', return_value=FakeExchange())
        @mock.patch('kombu.Consumer', return_value=FakeConsumer())
        def wrapped(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
            return function(self, mock_consumer, mock_exchange, mock_declare, mock_connection)
        return wrapped

    @mock_kombu
    def test_health_check(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock_kombu
    @mock.patch('requests.post', return_value=FakeResponse(status_code=201))
    def test_simple_proprietor_conversion(self, mock_post, mock_consumer, mock_exchange, mock_declare, mock_connection):
        output = get_iopn_records(single_PI_proprietor)
        assert len(output) == 1
        assert output[0]['title_number'] == 'LK31302'
        assert output[0]['registered_proprietor']['surname'] == 'Ullrich'
        assert output[0]['registered_proprietor']['forenames'][0] == 'Murl'
        assert output[0]['registered_proprietor']['forenames'][1] == 'Lenora'
        assert output[0]['registered_proprietor']['full_name'] == 'Murl Lenora Ullrich'
        assert output[0]['office'] == 'Peytonland Office'
        assert output[0]['sub_register'] == 'Proprietorship'
        assert output[0]['name_type'] == 'Private'

    @mock_kombu
    @mock.patch('requests.post', return_value=FakeResponse(status_code=201))
    def test_simple_charge_conversion(self, mock_post, mock_consumer, mock_exchange, mock_declare, mock_connection):
        output = get_iopn_records(has_charge)
        assert len(output) == 2
        assert output[0]['title_number'] == 'TR123456'
        assert output[1]['title_number'] == 'TR123456'
        assert output[0]['registered_proprietor']['surname'] == 'HOWARD'
        assert output[0]['registered_proprietor']['forenames'][0] == 'BOB'
        assert output[1]['registered_proprietor']['full_name'] == 'High Street Bank PLC'
        assert output[0]['sub_register'] == 'Proprietorship'
        assert output[1]['sub_register'] == 'Charge'
        assert output[0]['name_type'] == 'Private'
        assert output[1]['name_type'] == 'Non-Private'

    @mock_kombu
    @mock.patch('requests.post', return_value=FakeResponse(status_code=500))
    def test_simple_proprietor_conversion_insert_failed(self, mock_post, mock_consumer, mock_exchange, mock_declare, mock_connection):
        with pytest.raises(NamesError) as excinfo:
            get_iopn_records(single_PI_proprietor)
        print(excinfo.value.value)
        assert excinfo.value.value == "Search API non-201 response: 500"

    @mock_kombu
    def test_exception_handled(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
        queue = FakeQueue()
        listen(FakeFailingConnection(), queue, False)
        assert queue.data['exception_class'] == "NamesError"

    @mock_kombu
    @mock.patch('requests.post', return_value=FakeResponse(status_code=201))
    def test_subscribe_and_send_on(self, mock_consumer, mock_exchange, mock_declare, mock_connection, mock_post):
        conn = FakeWorkingConnection(single_PI_proprietor)
        listen(conn, FakeQueue(), False)
        assert mock_post.call_count == 1
        name, args, kwargs = mock_post.mock_calls[0]
        data = json.loads(kwargs['data'])
        assert data[0]['title_number'] == 'LK31302'
        assert data[0]['registered_proprietor']['surname'] == 'Ullrich'
        assert data[0]['registered_proprietor']['forenames'][0] == 'Murl'
        assert data[0]['registered_proprietor']['forenames'][1] == 'Lenora'
        assert data[0]['registered_proprietor']['full_name'] == 'Murl Lenora Ullrich'
        assert data[0]['office'] == 'Peytonland Office'
        assert data[0]['sub_register'] == 'Proprietorship'
        assert data[0]['name_type'] == 'Private'
