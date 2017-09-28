# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import traceback

import falcon


def get_version_from_request(req):
    """
    Attempt to extract the api version string
    """
    for part in req.path.split('/'):
        if '.' in part and part.startswith('v'):
            return part
    return 'N/A'


# Standard error handler
def format_resp(req,
                resp,
                status_code,
                message="",
                reason="",
                error_type="Unspecified Exception",
                retry=False,
                error_list=None):
    """
    Write a error message body and throw a Falcon exception to trigger
    an HTTP status
    :param req: Falcon request object
    :param resp: Falcon response object to update
    :param status_code: Falcon status_code constant
    :param message: Optional error message to include in the body
    :param reason: Optional reason code to include in the body
    :param retry: Optional flag whether client should retry the operation.
    :param error_list: option list of errors
    Can ignore if we rely solely on 4XX vs 5xx status codes
    """
    if error_list is None:
        error_list = [{'message': 'An error ocurred, but was not specified'}]
    error_response = {
        'kind': 'status',
        'apiVersion': get_version_from_request(req),
        'metadata': {},
        'status': 'Failure',
        'message': message,
        'reason': reason,
        'details': {
            'errorType': error_type,
            'errorCount': len(error_list),
            'errorList': error_list
        },
        'code': status_code
    }

    resp.body = json.dumps(error_response, default=str)
    resp.content_type = 'application/json'
    resp.status = status_code


def default_error_serializer(req, resp, exception):
    """
    Writes the default error message body, when we don't handle it otherwise
    """
    format_resp(
        req,
        resp,
        status_code=exception.status,
        message=exception.description,
        reason=exception.title,
        error_type=exception.__class__.__name__,
        error_list=[{'message': exception.description}]
    )


def default_exception_handler(ex, req, resp, params):
    """
    Catch-all execption handler for standardized output.
    If this is a standard falcon HTTPError, rethrow it for handling
    """
    if isinstance(ex, falcon.HTTPError):
        # allow the falcon http errors to bubble up and get handled
        raise ex
    else:
        # take care of the uncaught stuff
        exc_string = traceback.format_exc()
        logging.error('Unhanded Exception being handled: \n%s', exc_string)
        format_resp(
            req,
            resp,
            falcon.HTTP_500,
            error_type=ex.__class__.__name__,
            message="Unhandled Exception raised: %s" % str(ex),
            retry=True
        )


class AppError(Exception):
    """
    Base error containing enough information to make a shipyard formatted error
    """

    def __init__(self,
                 title='Internal Server Error',
                 description=None,
                 error_list=None,
                 status=falcon.HTTP_500,
                 retry=False):
        """
        :param description: The internal error description
        :param error_list: The list of errors
        :param status: The desired falcon HTTP resposne code
        :param title: The title of the error message
        :param retry: Optional retry directive for the consumer
        """
        self.title = title
        self.description = description
        self.error_list = massage_error_list(error_list, description)
        self.status = status
        self.retry = retry

    @staticmethod
    def handle(ex, req, resp, params):
        format_resp(
            req,
            resp,
            ex.status,
            message=ex.title,
            reason=ex.description,
            error_list=ex.error_list,
            error_type=ex.__class__.__name__,
            retry=ex.retry)


class AirflowError(AppError):
    """
    An error to handle errors returned by the Airflow API
    """

    def __init__(self, description=None, error_list=None):
        super().__init__(
            title='Error response from Airflow',
            description=description,
            error_list=error_list,
            status=falcon.HTTP_400,
            retry=False
        )


class DatabaseError(AppError):
    """
    An error to handle general api errors.
    """

    def __init__(self,
                 description=None,
                 error_list=None,
                 status=falcon.HTTP_500,
                 title='Database Access Error',
                 retry=False):
        super().__init__(
            status=status,
            title=title,
            description=description,
            error_list=error_list,
            retry=retry
        )


class ApiError(AppError):
    """
    An error to handle general api errors.
    """

    def __init__(self,
                 description="",
                 error_list=None,
                 status=falcon.HTTP_400,
                 title="",
                 retry=False):
        super().__init__(
            status=status,
            title=title,
            description=description,
            error_list=error_list,
            retry=retry
        )


class InvalidFormatError(AppError):
    """
    An exception to cover invalid input formatting
    """

    def __init__(self, title, description="Not Specified", error_list=None):

        super().__init__(
            title=title,
            description='Validation has failed',
            error_list=error_list,
            status=falcon.HTTP_400,
            retry=False
        )


def massage_error_list(error_list, placeholder_description):
    """
    Returns a best-effort attempt to make a nice error list
    """
    output_error_list = []
    if error_list:
        for error in error_list:
            if not error['message']:
                output_error_list.append({'message': error})
            else:
                output_error_list.append(error)
    if not output_error_list:
        output_error_list.append({'message': placeholder_description})
    return output_error_list
