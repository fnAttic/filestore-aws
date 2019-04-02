#!/usr/bin/env python
from datetime import datetime
import json


StringAttribute = (
    lambda x: {'S': x},
    lambda x: x['S']
)

DateTimeAttribute = (
    # datetime assumed to be in UTC
    lambda x: {'S': x.strftime("%Y-%m-%dT%H:%M:%S")},
    lambda x: datetime.strptime(x['S'], "%Y-%m-%dT%H:%M:%S")
)

IntegerAttribute = (
    lambda x: {'N': str(x)},
    lambda x: int(x['N'])
)

FloatAttribute = (
    lambda x: {'N': str(x)},
    lambda x: float(x['N'])
)

JsonAttribute = (
    lambda x: {'S': json.dumps(x)},
    lambda x: json.loads(x['S'])
)


class Model(object):
    """DDB model"""

    _TABLE_NAME = None
    _FIELDS = []

    @classmethod
    def serialize(cls, data):
        """serialize data"""
        stored_data = {}
        for field_name, (field_serializer, field_deserializer) in cls._FIELDS:
            value = data.get(field_name)
            if value is not None:
                stored_data[field_name] = field_serializer(value)
        return stored_data

    @classmethod
    def deserialize(cls, stored_data):
        """deserialize data"""
        data = {}
        for field_name, (field_serializer, field_deserializer) in cls._FIELDS:
            value = stored_data.get(field_name)
            if value is not None:
                data[field_name] = field_deserializer(value)
        return data
