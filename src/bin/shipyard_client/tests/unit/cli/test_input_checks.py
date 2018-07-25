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
from unittest import mock

from shipyard_client.cli import input_checks


def test_check_workflow_id_valid():
    """Check that a valid formatted id passes"""
    ctx = mock.Mock(side_effect=Exception("failed"))
    input_checks.check_workflow_id(
        ctx, 'something__2017-01-01T12:34:56.000000')
    ctx.fail.assert_not_called()


def test_check_workflow_id_valid_tricky():
    """Check that a valid formatted id passes.

    This test provides something that arrow will parse as an invalid
    date if the code is not properly set up to separate the date
    first.
    """
    ctx = mock.Mock(side_effect=Exception("failed"))
    input_checks.check_workflow_id(
        ctx, '2017-01-01T12:34:99.000__2017-01-01T12:34:56.000000')
    ctx.fail.assert_not_called()


def test_check_workflow_id_no_date():
    """Check tha a missing date portion of the string is rejected."""
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_workflow_id(ctx, 'something__')
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'date portion' in str(ctx.mock_calls[0])
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_workflow_id_none():
    """Check that the workflow id check invokes the context.fail on None"""
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_workflow_id(
            ctx, None)
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_workflow_id_invalid_separator():
    """Check that the separator check invokes the context.fail"""
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_workflow_id(
            ctx, 'something20170101T12:34:56.000000')
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_workflow_id_invalid_date():
    """Check that the date format check invokes the context.fail"""
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_workflow_id(
            ctx, 'something__blah0101 12:34:56.000000')
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_workflow_id_invalid_date_format():
    """Check that the date format check invokes the context.fail"""
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_workflow_id(
            ctx, 'something__2017-01-01T12:34:56')
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_id_valid():
    ctx = mock.Mock(side_effect=Exception("failed"))
    input_checks.check_id(ctx, "12345678901234567890123456")
    ctx.fail.assert_not_called()


def test_check_id_too_long():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_id(ctx, "TOOLONGTOOLONGTOOLONGTOOLONGTOOLONG")
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_id_too_short():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_id(ctx, "TOOSHORT")
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_id_bad_chars():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_id(ctx, "_ARENOTALLOWED-")
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_id_none():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_id(ctx, None)
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_control_action_valid():
    ctx = mock.Mock(side_effect=Exception("failed"))
    input_checks.check_control_action(ctx, 'pause')
    input_checks.check_control_action(ctx, 'unpause')
    input_checks.check_control_action(ctx, 'stop')
    ctx.fail.assert_not_called()


def test_check_control_action_invalid():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_control_action(ctx, 'completely_bogus')
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_control_action_none():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_control_action(ctx, None)
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_action_commands():
    ctx = mock.Mock(side_effect=Exception("failed"))
    input_checks.check_action_command(ctx, 'deploy_site')
    input_checks.check_action_command(ctx, 'update_site')
    input_checks.check_action_command(ctx, 'update_software')
    input_checks.check_action_command(ctx, 'redeploy_server')
    ctx.fail.assert_not_called()


def test_check_action_commands_invalid():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_action_command(ctx, "burger_and_fries")
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_action_commands_none():
    ctx = mock.Mock(side_effect=Exception("failed"))
    try:
        input_checks.check_action_command(ctx, None)
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_reformat_parameter_valid():
    ctx = mock.Mock(side_effect=Exception("failed"))
    param = ['this=that']
    input_checks.check_reformat_parameter(ctx, param)
    param = []
    input_checks.check_reformat_parameter(ctx, param)
    param = ['this=that', 'some=another']
    o_params = input_checks.check_reformat_parameter(ctx, param)
    assert 'this' in o_params
    assert 'some' in o_params
    assert 'that' not in o_params
    assert 'another' not in o_params
    assert o_params['this'] == 'that'
    assert o_params['some'] == 'another'
    ctx.fail.assert_not_called()


def test_check_reformat_parameter_no_equals_second():
    ctx = mock.Mock(side_effect=Exception("failed"))
    param = ['this=that', 'someanother']
    try:
        input_checks.check_reformat_parameter(ctx, param)
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])


def test_check_reformat_parameter_no_equals_first():
    ctx = mock.Mock(side_effect=Exception("failed"))
    param = ['thisthat', 'some=another']
    try:
        input_checks.check_reformat_parameter(ctx, param)
    except Exception:
        pass
    # py 3.6: ctx.fail.assert_called()
    assert 'call.fail(' in str(ctx.mock_calls[0])
