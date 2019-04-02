#!/usr/bin/env python
import os
from lib import vendor
vendor.add(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ext'))

# logging
import logging
from datetime import timedelta
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

# environment variables
BUCKET_NAME = os.environ.get('BUCKET_NAME')
EXPIRATION = os.environ.get('EXPIRATION')
STORE = os.environ.get('STORE') == 'True'

# static configuration
QUERY_LIMIT = 10
NONSTORED_TIMEOUT = timedelta(hours=1)
