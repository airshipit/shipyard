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
from shipyard_airflow import errors


def test_app_error():
    """
    test app error for status and title overrides
    """

    err = errors.AppError()
    assert err.status == errors.AppError.status
    assert err.title == errors.AppError.title

    err = errors.AppError(title='Unfortunate News Everyone', status=999)
    assert err.status == 999
    assert err.title == 'Unfortunate News Everyone'


def test_api_error():
    """
    test api error
    """

    err = errors.ApiError()
    assert err.status == errors.ApiError.status
    assert err.title == errors.ApiError.title

    err = errors.ApiError(title='It was the worst of times', status=1)
    assert err.title == 'It was the worst of times'
    assert err.status == 1


def test_database_error():
    """
    test database error
    """

    err = errors.DatabaseError()
    assert err.status == errors.DatabaseError.status
    assert err.title == errors.DatabaseError.title

    err = errors.DatabaseError(title='Stuff Happens', status=1990)
    assert err.status == 1990
    assert err.title == 'Stuff Happens'


def test_airflow_error():
    """
    test airflow error
    """

    err = errors.AirflowError()
    assert err.status == errors.AirflowError.status
    assert err.title == errors.AirflowError.title

    err = errors.AirflowError(title='cron save us', status=500)
    assert err.status == 500
    assert err.title == 'cron save us'
