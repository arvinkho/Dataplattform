import json
import logging

from botocore.exceptions import ClientError
from common_lib.common.repositories.catalogue import GlueRepositoryNotFoundException
from flask import jsonify
from werkzeug.exceptions import HTTPException


# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html#parsing-error-responses-and-catching-exceptions-from-aws-services
def handle_client_error(error: ClientError):
    error_code = error.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)
    error_message = error.response.get('Error', {'Message': 'Unknown error'})
    error_message['RequestId'] = error.response.get('ResponseMetadata', {}).get('RequestId')
    logging.getLogger().error(str(error_message), exc_info=error)

    if error_message['Code'] == 'AccessDeniedException':  # Obfuscate internal information
        error_message['Message'] = 'User does not have access to resource'

    return format_error(error_message, error_code)


def handle_value_error(e: ValueError):
    return format_error({'Message': str(e)}, 400)


def handle_not_found(e: GlueRepositoryNotFoundException):
    return format_error({'Message': str(e)}, 404)


def handle_any(e: Exception):
    logging.getLogger().error(str(e), exc_info=e)

    if isinstance(e, HTTPException):
        return format_error({
            'code': e.code,
            'name': e.name,
            'description': e.description,
        }, e.code)
    else:
        return format_error({'Message': 'Internal Server Error'}, 500)


# ApiGateway demands error objects to be formatted a certain way
# https://docs.aws.amazon.com/apigateway/latest/developerguide/handle-errors-in-lambda-integration.html
def format_error(response: object, code: int):
    logging.getLogger().info("Formatting error message")

    return jsonify({
        'statusCode': code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'isBase64Encoded': False,
        'body': json.dumps(response)
    }), code
