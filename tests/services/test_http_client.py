import sys
import json
import responses
from mock import sentinel
from base64 import b64encode
from requests.exceptions import HTTPError

from zeroservices.services import BaseHTTPClient, BasicAuthHTTPClient
from zeroservices.services import get_http_interface, BasicAuth
from ..utils import TestCase


class BaseHttpClientTestCase(TestCase):

    def setUp(self):
        self.old_argv = sys.argv
        sys.argv = []

        self.base_url = "http://localhost"
        self.collection_name = "collection"
        self.resource_id = "1"
        self.resource_body = {'_id': self.resource_id, 'key': 'value'}
        self.client = BaseHTTPClient(self.base_url)
        self.app = get_http_interface(sentinel.SERVICE, bind=False)

        # URLS
        self.collection_url = self.base_url + \
            self.app.reverse_url("collection", self.collection_name)
        self.resource_url = self.base_url + \
            self.app.reverse_url("resource", self.collection_name,
                self.resource_id)

    def tearDown(self):
        sys.argv = self.old_argv

    @responses.activate
    def test_main(self):
        expected_body = "Hello world from api"
        responses.add(
            responses.GET, self.base_url + self.app.reverse_url("main"),
            body=expected_body, status=200)

        response = self.client.hello_world()

        self.assertEquals(response, expected_body)

    @responses.activate
    def test_list_on_collection(self):
        expected_body = [self.resource_body]

        responses.add(
            responses.GET, self.collection_url,
            body=json.dumps(expected_body), status=200)

        response = self.client[self.collection_name].list()

        self.assertEquals(response, expected_body)

    @responses.activate
    def test_custom_action_on_collection(self):
        expected_body = [self.resource_body]

        responses.add(
            responses.POST, self.collection_url,
            body=json.dumps(expected_body), status=200)

        response = self.client[self.collection_name].custom_action()

        self.assertEquals(response, expected_body)
        self.assertEquals(len(responses.calls), 1)
        request_headers = responses.calls[0].request.headers
        self.assertEquals(request_headers['X-CUSTOM-ACTION'],
            'custom_action')

    @responses.activate
    def test_get_on_resource(self):
        expected_body = self.resource_body

        responses.add(
            responses.GET, self.resource_url,
            body=json.dumps(expected_body), status=200)

        response = self.client[self.collection_name][self.resource_id].get()

        self.assertEquals(response, expected_body)

    @responses.activate
    def test_post_on_resource(self):
        expected_body = {'_id': self.resource_id}

        responses.add(
            responses.POST, self.resource_url,
            body=json.dumps(expected_body), status=201)

        response = self.client[self.collection_name][self.resource_id].create(**self.resource_body)

        self.assertEquals(response, expected_body)

        self.assertEquals(len(responses.calls), 1)
        request_body = responses.calls[0].request.body
        self.assertEquals(request_body, json.dumps(self.resource_body))

    @responses.activate
    def test_delete_on_resource(self):
        expected_response = 'OK'

        responses.add(
            responses.DELETE, self.resource_url,
            body=json.dumps(expected_response), status=200)

        response = self.client[self.collection_name][self.resource_id].delete()

        self.assertEquals(response, expected_response)

    @responses.activate
    def test_patch_on_resource(self):
        expected_response = {'_id': self.resource_id, 'key': 'value2'}
        patch = {"$set": {"key": "value2"}}

        responses.add(
            responses.PATCH, self.resource_url,
            body=json.dumps(expected_response), status=200)

        response = self.client[self.collection_name][self.resource_id].patch(**patch)

        self.assertEquals(response, expected_response)
        self.assertEquals(len(responses.calls), 1)
        request_body = responses.calls[0].request.body
        self.assertEquals(request_body, json.dumps(patch))

    @responses.activate
    def test_custom_action_on_resource(self):
        expected_body = {'_id': self.resource_id}

        responses.add(
            responses.POST, self.resource_url,
            body=json.dumps(expected_body), status=201)

        response = self.client[self.collection_name][self.resource_id].custom_action()

        self.assertEquals(response, expected_body)
        self.assertEquals(len(responses.calls), 1)
        request_headers = responses.calls[0].request.headers
        self.assertEquals(request_headers['X-CUSTOM-ACTION'],
            'custom_action')

    @responses.activate
    def test_404(self):
        responses.add(
            responses.GET, self.resource_url,
            body="", status=404)

        with self.assertRaises(HTTPError):
            response = self.client[self.collection_name][self.resource_id].get()

    @responses.activate
    def test_multiples_requests(self):
        # First 404
        responses.add(
            responses.GET, self.resource_url,
            body="", status=404)

        with self.assertRaises(HTTPError):
            response = self.client[self.collection_name][self.resource_id].get()

        # Then list
        expected_body = [self.resource_body]

        responses.add(
            responses.GET, self.collection_url,
            body=json.dumps(expected_body), status=200)

        response = self.client[self.collection_name].list()

        self.assertEquals(response, expected_body)


class BasicAuthClientTestCase(TestCase):

    def setUp(self):
        self.old_argv = sys.argv
        sys.argv = []

        self.base_url = "http://localhost"
        self.collection_name = "collection"
        self.resource_id = "1"
        self.resource_body = {'_id': self.resource_id, 'key': 'value'}
        self.auth_tuple = ('login', 'password')
        self.client = BasicAuthHTTPClient(self.base_url, self.auth_tuple)
        self.app = get_http_interface(sentinel.SERVICE, bind=False)

        # URLS
        self.collection_url = self.base_url + \
            self.app.reverse_url("collection", self.collection_name)
        self.resource_url = self.base_url + \
            self.app.reverse_url("resource", self.collection_name,
                self.resource_id)


    def tearDown(self):
        sys.argv = self.old_argv


    @responses.activate
    def test_main(self):
        expected_body = "Hello world from api"
        responses.add(
            responses.GET, self.base_url + self.app.reverse_url("main"),
            body=expected_body, status=200)

        response = self.client.hello_world()

        # Check auth header
        auth_value = b64encode('{0}:{1}'.format(*self.auth_tuple).encode('latin1'))
        expected_authorization_header = 'Basic {0}'.format(auth_value.decode('latin1'))

        self.assertEquals(response, expected_body)
        self.assertEquals(len(responses.calls), 1)
        request_headers = responses.calls[0].request.headers
        self.assertEquals(request_headers['Authorization'],
            expected_authorization_header)

    @responses.activate
    def test_list_on_collection(self):
        expected_body = [self.resource_body]

        responses.add(
            responses.GET, self.collection_url,
            body=json.dumps(expected_body), status=200)

        response = self.client[self.collection_name].list()

        self.assertEquals(response, expected_body)

        # Check auth header
        auth_value = b64encode('{0}:{1}'.format(*self.auth_tuple).encode('latin1'))
        expected_authorization_header = 'Basic {0}'.format(auth_value.decode('latin1'))

        self.assertEquals(response, expected_body)
        self.assertEquals(len(responses.calls), 1)
        request_headers = responses.calls[0].request.headers
        self.assertEquals(request_headers['Authorization'],
            expected_authorization_header)
