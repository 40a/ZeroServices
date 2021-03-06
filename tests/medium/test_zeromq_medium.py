import zmq
import json
import time
import socket
import asyncio

from datetime import timedelta
from time import sleep, time

try:
    from unittest.mock import Mock, call
except ImportError:
    from mock import Mock, call

from zeroservices.medium.zeromq import ZeroMQMedium
from zeroservices.discovery import MemoryDiscoveryMedium
from .utils import generate_zeromq_medium
from ..utils import TestCase, _async_test, TestService

from . import _BaseMediumTestCase


class ZeroMQMediumTestCase(_BaseMediumTestCase):

    @asyncio.coroutine
    def get_medium(self, loop):
        medium = ZeroMQMedium(loop=loop, discovery_class=MemoryDiscoveryMedium)
        medium.set_service(TestService('test_service', medium))
        yield from medium.start()
        return medium


if __name__ == '__main__':
    unittest.main()
