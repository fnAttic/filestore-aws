#!/usr/bin/env python
from runtime_context import LOGGER
import boto3
from lib import ddb


DDB_CLIENT = boto3.client('dynamodb')


class FileModel(ddb.Model):
    """file model"""

    _TABLE_NAME = 'Files'
    _FIELDS = [
        ('id', ddb.StringAttribute),
        ('uploaded_at', ddb.DateTimeAttribute),
        ('stored_at', ddb.DateTimeAttribute),
        ('deleted_at', ddb.DateTimeAttribute),
        ('name', ddb.StringAttribute),
        ('type', ddb.StringAttribute),
        ('size', ddb.IntegerAttribute),
        ('meta', ddb.JsonAttribute)
    ]

    @classmethod
    def create(cls, data, **kwargs):
        """create file item"""
        put_data = cls.serialize(data)
        response = DDB_CLIENT.put_item(
            TableName=cls._TABLE_NAME,
            Item=put_data
        )
        return response

    @classmethod
    def get_by_id(cls, id):
        """get item with id"""
        response = DDB_CLIENT.get_item(
            TableName=cls._TABLE_NAME,
            Key={
                'id': {
                    'S': id
                }
            }
        )
        get_data = cls.deserialize(response['Item'])
        return get_data

    @classmethod
    def get_by_ids(cls, id_list):
        """get list of files by ids
        supports up to 20 ids
        """
        id_list = id_list[:20]  # shorten the list to 20
        request_items = {
            'Files': {
                'Keys': []
            }
        }
        for id_item in id_list:
            request_items['Files']['Keys'].append({
                'id': {
                    'S': id_item
                }
            })
        response = DDB_CLIENT.batch_get_item(RequestItems=request_items)
        get_data = []
        for file in response['Responses']['Files']:
            get_data.append(cls.deserialize(file))
        return get_data

    @classmethod
    def update(cls, data):
        """update an item, it only supports setting attribute (not removing)"""
        id = data.pop('id')
        ref = 65
        attr_names = {}
        attr_values = {}
        expressions = []
        for field_name, (field_serializer, field_deserializer) in cls._FIELDS:
            value = data.get(field_name)
            if value is not None:
                ref_chr = chr(ref)
                attr_names['#' + ref_chr] = field_name
                attr_values[':' + ref_chr] = field_serializer(value)
                expressions.append('#{} = :{}'.format(ref_chr, ref_chr))
                ref += 1
        response = DDB_CLIENT.update_item(
            TableName=cls._TABLE_NAME,
            Key={
                'id': {
                    'S': id
                }
            },
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            UpdateExpression='SET ' + ','.join(expressions)
        )
        return response

    @classmethod
    def list_expired(cls, expiry_at):
        """list expired files"""
        response = DDB_CLIENT.scan(
            TableName=cls._TABLE_NAME,
            ExpressionAttributeNames={
                '#ID': 'id'
            },
            ProjectionExpression='#ID',
            ExpressionAttributeValues={
                ':expiry_at': {
                    'S': expiry_at.isoformat()
                }
            },
            FilterExpression='uploaded_at < :expiry_at and attribute_not_exists(stored_at)'
        )
        return response.get('Items')

    @classmethod
    def delete_by_id(cls, id):
        """delete item by id"""
        response = DDB_CLIENT.delete_item(
            TableName=cls._TABLE_NAME,
            Key={
                'id': {
                    'S': id
                }
            }
        )
        return response
