import zmq
import time
import json
import socket
import logging

try:
    from unittest.mock import Mock, create_autospec
except ImportError:
    from mock import Mock, create_autospec


from zeroservices.exceptions import ServiceUnavailable
from zeroservices.ressources import RessourceCollection, Ressource
from zeroservices.medium import BaseMedium
from zeroservices import BaseService


def test_medium():
    return Mock(spec_set=BaseMedium)


class ServiceRegistry(object):
    SERVICES = {}
    SERVICES_RESSOURCES = {}


def sample_collection(sample_ressource_name):

    collection = create_autospec(RessourceCollection, True)
    collection.ressource_name = sample_ressource_name

    return collection


def sample_ressource():
    ressource_class = create_autospec(Ressource, True)
    ressource_instance = create_autospec(Ressource, True, instance=True)
    ressource_class.return_value = ressource_instance
    return ressource_class, ressource_instance


def base_ressource():

    class BaseRessource(Ressource):

        def add_link(self):
            pass

        def create(self):
            pass

        def delete(self):
            pass

        def get(self):
            pass

        def patch(self):
            pass

    return BaseRessource


class TestService(BaseService):

    def __init__(self, *args, **kwargs):
        super(TestService, self).__init__(*args, **kwargs)
        self.on_message = create_autospec(self.on_message, return_value=None)
        self.on_event = create_autospec(self.on_event, return_value=None)

# Test memory medium

SERVICES = {}
SERVICES_LIST = []

class MemoryMedium(BaseMedium):

    def __init__(self, node_id):
        super(MemoryMedium, self).__init__(node_id)

    def register(self):
        # Register myself to global
        SERVICES[self.node_id] = self
        SERVICES_LIST.append(self)

        self.publish('register', self.get_node_info())

    def start(self):
        pass

    def close(self):
        del SERVICES[self.node_id]
        SERVICES_LIST.remove(self)

    def connect_to_node(self, peer_info):
        pass

    def subscribe(self, topic):
        self.topics.append(topic)

    def process_sub(self, message_type, data):
        self.logger.info('Process sub, message_type: %s, data: %s' %
            (message_type, data))
        self.event_callback(message_type, data)

    def process_raw_query(self, message_type, message):
        self.logger.info('Process raw query, message_type: %s, message: %s' %
            (message_type, message))

        return self.msg_callback(message_type, **message)

    def publish(self, event_type, event_data):
        for service in [s for s in SERVICES_LIST if s.node_id != self.node_id]:
            service.process_event(event_type, event_data)

    def send(self, peer_info, message, message_type="message", callback=None,
             wait_response=True):
        try:
            service = SERVICES[peer_info['node_id']]
        except KeyError:
            raise ServiceUnavailable('Service %s is unavailable.' % service_id)

        return service.process_message(message, message_type)
