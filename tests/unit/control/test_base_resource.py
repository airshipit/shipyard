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
from mock import patch
import pytest

import falcon
from falcon import testing

from shipyard_airflow.control.base import BaseResource, ShipyardRequestContext
from shipyard_airflow.control.json_schemas import ACTION
from shipyard_airflow.errors import InvalidFormatError


def create_req(ctx, body):
    '''creates a falcon request'''
    env = testing.create_environ(
        path='/',
        query_string='',
        protocol='HTTP/1.1',
        scheme='http',
        host='falconframework.org',
        port=None,
        headers={'Content-Type': 'application/json'},
        app='',
        body=body,
        method='POST',
        wsgierrors=None,
        file_wrapper=None)
    req = falcon.Request(env)
    req.context = ctx
    return req


def create_resp():
    '''creates a falcon response'''
    resp = falcon.Response()
    return resp


def test_on_options():
    '''tests on_options'''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()

    req = create_req(ctx, body=None)
    resp = create_resp()

    baseResource.on_options(req, resp)
    assert 'OPTIONS' in resp.get_header('Allow')
    assert resp.status == '200 OK'


def test_req_json_no_body():
    '''test req_json when there is no body in the request'''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()

    req = create_req(ctx, body=None)

    with pytest.raises(InvalidFormatError) as expected_exc:
        baseResource.req_json(req, validate_json_schema=ACTION)
    assert 'Json body is required' in str(expected_exc)
    assert str(req.path) in str(expected_exc)

    result = baseResource.req_json(req, validate_json_schema=None)
    assert result is None


@patch('shipyard_airflow.control.base.BaseResource.log_message')
def test_req_json_with_body(mock_logger):
    '''test req_json when there is a body'''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()

    json_body = json.dumps({
        'user': "test_user",
        'req_id': "test_req_id",
        'external_ctx': "test_ext_ctx",
        'name': "test_name"
    }).encode('utf-8')

    req = create_req(ctx, body=json_body)

    result = baseResource.req_json(req, validate_json_schema=ACTION)
    mock_logger.assert_called_with(
        ctx, logging.INFO,
        'Input message body: b\'' + json_body.decode('utf-8') + '\'')
    assert result == json.loads(json_body.decode('utf-8'))

    req = create_req(ctx, body=json_body)

    json_body = ('testing json').encode('utf-8')
    req = create_req(ctx, body=json_body)

    with pytest.raises(InvalidFormatError) as expected_exc:
        baseResource.req_json(req)
    mock_logger.assert_called_with(
        ctx, logging.ERROR,
        'Invalid JSON in request: \n' + json_body.decode('utf-8'))
    assert 'JSON could not be decoded' in str(expected_exc)
    assert str(req.path) in str(expected_exc)


def test_to_json():
    '''test to_json'''
    baseResource = BaseResource()
    body_dict = {
        'user': 'test_user',
        'req_id': 'test_req_id',
        'external_ctx': 'test_ext_ctx',
        'name': 'test_name'
    }
    results = baseResource.to_json(body_dict)
    assert results == json.dumps(body_dict)


@patch('logging.Logger.log')
def test_log_message(mock_log):
    '''test log_message'''
    baseResource = BaseResource()
    ctx = None
    level = logging.ERROR
    msg = 'test_message'
    extra = {'user': 'N/A', 'req_id': 'N/A', 'external_ctx': 'N/A'}
    baseResource.log_message(ctx, level, msg)
    mock_log.assert_called_with(level, msg, extra=extra)

    ctx = ShipyardRequestContext()
    extra = {
        'user': ctx.user,
        'req_id': ctx.request_id,
        'external_ctx': ctx.external_marker,
    }
    baseResource.log_message(ctx, level, msg)
    mock_log.assert_called_with(level, msg, extra=extra)


def test_debug():
    '''test debug'''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()
    msg = 'test_msg'
    with patch.object(BaseResource, 'log_message') as mock_method:
        baseResource.debug(ctx, msg)
    mock_method.assert_called_once_with(ctx, logging.DEBUG, msg)


def test_info():
    '''test info'''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()
    msg = 'test_msg'
    with patch.object(BaseResource, 'log_message') as mock_method:
        baseResource.info(ctx, msg)
    mock_method.assert_called_once_with(ctx, logging.INFO, msg)


def test_warn():
    '''test warn '''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()
    msg = 'test_msg'
    with patch.object(BaseResource, 'log_message') as mock_method:
        baseResource.warn(ctx, msg)
    mock_method.assert_called_once_with(ctx, logging.WARN, msg)


def test_error():
    '''test error'''
    baseResource = BaseResource()
    ctx = ShipyardRequestContext()
    msg = 'test_msg'
    with patch.object(BaseResource, 'log_message') as mock_method:
        baseResource.error(ctx, msg)
    mock_method.assert_called_once_with(ctx, logging.ERROR, msg)
