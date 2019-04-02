#!/usr/bin/env python
import runtime_context
from runtime_context import LOGGER
from datetime import datetime, timedelta
import boto3
from botocore.config import Config
from lib import utils
from models.file import FileModel
import json


S3_CLIENT = boto3.client('s3', config=Config(s3={'addressing_style': 'path'},
                                             signature_version='s3v4'))


def preprocess(event, context):
    """Sample pure Lambda function
    event: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format
    context: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    Returns: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    # create file in DDB
    file_id = utils.generate_id()
    file_request = json.loads(event.get('body'))
    FileModel.create({
        'id': file_id,
        'name': file_request.get('name')
    })
    LOGGER.debug('Files item created. service=ddb method=put_item id={}'.format(file_id))
    # generate signed URL for posting file
    url = S3_CLIENT.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': runtime_context.BUCKET_NAME,
            'Key': file_id
        },
        ExpiresIn=runtime_context.EXPIRATION
    )
    LOGGER.debug('Presigned URL generated. service=s3 method=put_object id={}'.format(file_id))
    # send back the signed url
    return {
        "statusCode": 200,
        "body": json.dumps({
            'id': file_id,
            'url': url
        }),
        # CORS header
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }


def get_s3_file_type(file_id):
    """find out the mime type of a file (object) on S3"""
    file_object = S3_CLIENT.get_object(Bucket=runtime_context.BUCKET_NAME,
                                       Key=file_id)
    ct = file_object.get('ContentType')
    return ct.split(';')[0] if ct else 'application/octet-stream'


def uploaded(event, context):
    """S3 event triggers when file is uploaded
    event: https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """
    dt = datetime.utcnow()
    # NOTE: the event might include multiple records
    for r in event['Records']:
        file_id = r['s3']['object']['key']
        file = {
            'id': file_id,
            'size': r['s3']['object']['size'],
            'type': get_s3_file_type(file_id),
            'uploaded_at': dt,
        }
        if runtime_context.STORE:
            file['stored_at'] = dt
        FileModel.update(file)
        LOGGER.debug('Files item updated (uploaded). service=ddb method=update_item id={}'.format(file_id))
    return {
        "statusCode": 200
    }


def store(event, context):
    """store file"""
    # check the store on load configuration
    if runtime_context.STORE:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Configured to store files at the time of upload.'
            })
        }
    # get the list of files from the request
    file_ids = json.loads(event.get('body'))
    file_ids = file_ids[:runtime_context.QUERY_LIMIT]  # limit the number of files to store
    stored_file_ids = []
    dt = datetime.utcnow()
    for file_id in file_ids:
        FileModel.update({
            'id': file_id,
            'stored_at': dt,
        })
        LOGGER.debug('Files item updated (stored). service=ddb method=update_item id={}'.format(file_id))
        stored_file_ids.append(file_id)
    return {
        "statusCode": 200,
        "body": json.dumps(stored_file_ids)
    }


def get_presigned_url_for_download(file):
    """get presigned url for download"""
    url = S3_CLIENT.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': runtime_context.BUCKET_NAME,
            'Key': file['id'],
            'ResponseContentDisposition': 'attachment; filename="{}"'.format(file['name']),
            'ResponseContentType': file['type']
        },
        ExpiresIn=runtime_context.EXPIRATION
    )
    LOGGER.debug('Presigned URL generated. service=s3 method=get_object id={}'.format(file['id']))
    return url


def info(event, context):
    """get the info for a list of files"""
    query_string_parameters = event.get('queryStringParameters') or {}
    include_deleted = query_string_parameters.get('deleted') == 'yes'
    include_nonstored = query_string_parameters.get('nonstored') == 'yes'
    LOGGER.debug('File info includes deleted={} includes non-stored={}'.format(include_deleted, include_nonstored))
    file_ids = json.loads(event.get('body'))
    file_ids = file_ids[:runtime_context.QUERY_LIMIT]  # limit the number of files queried
    files = FileModel.get_by_ids(file_ids)
    for file in files:
        if not file.get('deleted_at') and file.get('stored_at'):  # only return not deleted and stored
            file['url'] = get_presigned_url_for_download(file)
        else:
            if (file.get('deleted_at') and include_deleted) or (not file.get('stored_at') and include_nonstored):
                pass
            else:  # remove deleted or non-stored
                files.remove(file)
    return {
        "statusCode": 200,
        "body": json.dumps(files, cls=utils.DateTimeEncoder)
    }


def delete(event, context):
    """delete files"""
    file_ids = json.loads(event.get('body'))
    deleted_file_ids = []
    for file_id in file_ids:
        # NOTE: there is no check if file has already been deleted
        FileModel.update({
            'id': file_id,
            'deleted_at': datetime.utcnow()
        })
        LOGGER.debug('Files item updated (deleted). service=ddb method=update_item id={}'.format(file_id))
        S3_CLIENT.delete_object(
            Bucket=runtime_context.BUCKET_NAME,
            Key=file_id
        )
        LOGGER.debug('S3 object deleted. service=s3 method=delete_object id={}'.format(file_id))
        deleted_file_ids.append(file_id)
    return {
        "statusCode": 200,
        "body": json.dumps(deleted_file_ids)
    }


def expire(event, context):
    """remove files that are uploaded, not stored, and older than the expiration time
    scheduled event
    """
    # scan the database for expired files
    expiry_at = datetime.utcnow() - runtime_context.NONSTORED_TIMEOUT
    files = FileModel.list_expired(expiry_at)
    # remove all files and all items one-by-one
    for file in files:
        file_id = file['id']['S']
        FileModel.update({
            'id': file_id,
            'deleted_at': datetime.utcnow()
        })
        LOGGER.debug('Files item updated (expired). service=ddb method=update_item id={}'.format(file_id))
        S3_CLIENT.delete_object(
            Bucket=runtime_context.BUCKET_NAME,
            Key=file_id
        )
        LOGGER.debug('S3 object deleted. service=s3 method=delete_object id={}'.format(file_id))
