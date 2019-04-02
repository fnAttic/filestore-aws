#!/usr/bin/env python
import unittest
import json
from botocore.stub import Stubber
from functions import file as file_functions
from models import file as file_models
from lib import utils
import runtime_context


# https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html
ddb_stubber = Stubber(file_models.DDB_CLIENT)
s3_stubber = Stubber(file_functions.S3_CLIENT)


def generate_id():
    return 'abcd'
utils.generate_id = generate_id


class FileTest(unittest.TestCase):

    def test_preprocess(self):
        # setting the environment variables
        runtime_context.BUCKET_NAME = 'test-bucket'
        runtime_context.EXPIRATION = 3600
        runtime_context.STORE = False

        ddb_expected = {
            'TableName': file_models.FileModel._TABLE_NAME,
            'Item': {
                'id': {
                    'S': 'abcd'
                },
                'name': {
                    'S': 'test_file.txt'
                }
            }
        }
        ddb_response = {
            'Attributes': {
                'id': {
                    'S': 'abcd'
                },
                'name': {
                    'S': 'test_file.txt'
                }
            }
        }
        ddb_stubber.add_response('put_item', ddb_response, ddb_expected)
        ddb_stubber.activate()
        response = file_functions.preprocess({
            'body': json.dumps({
                'id': 'abcd',
                'name': 'test_file.txt'
            })
        }, None)
        self.assertEqual(response.get('statusCode'), 200)


if __name__ == '__main__':
    unittest.main()
