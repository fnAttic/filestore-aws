#!/usr/bin/env python
import random
import string
from datetime import datetime
import json


def generate_id(length=16):
    """generate random IDs"""
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


class DateTimeEncoder(json.JSONEncoder):
    """datetime support in json"""

    def default(self, obj):
        """encoder"""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            return super(DateTimeEncoder, self).default(obj)


class DateTimeDecoder(json.JSONDecoder):
    """datetime support in json"""

    def __init__(self, *args, **kargs):
        json.JSONDecoder.__init__(self, object_hook=self.decoder, *args, **kargs)

    def decoder(self, d):
        """decoder"""
        return datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
