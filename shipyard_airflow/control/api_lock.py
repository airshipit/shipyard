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
"""
api_lock provides for a rudimentary lock mechanism using
the database to sync across multiple shipyard instances.
Also provided is the api_lock decorator to allow for resources
to easily declare the lock they should be able to acquire before
executing.
"""
from enum import Enum
import logging
from functools import wraps

import falcon
import ulid

from shipyard_airflow.db.db import SHIPYARD_DB
from shipyard_airflow.errors import ApiError

LOG = logging.getLogger(__name__)


def api_lock(api_lock_type):
    """
    Decorator to handle allowing a resource method to institute a lock
    based on the specified lock type.
    These locks are intended for use around methods such as on_post
    and on_get, etc...
    """
    def lock_decorator(func):
        @wraps(func)
        def func_wrapper(self, req, resp, *args, **kwargs):
            lock = ApiLock(api_lock_type,
                           req.context.external_marker,
                           req.context.user)
            try:
                lock.acquire()
                return func(self, req, resp, *args, **kwargs)
            except ApiLockAcquireError:
                raise ApiError(
                    title='Blocked by another process',
                    description=(
                        'Another process is currently blocking this request '
                        'with a lock for {}. Lock expires in not more '
                        'than {} seconds'.format(
                            lock.lock_type_name,
                            lock.expires
                        )
                    ),
                    status=falcon.HTTP_409,
                    retry=False,
                )
            finally:
                lock.release()
        return func_wrapper
    return lock_decorator


class ApiLockType(Enum):
    """
    ApiLockType defines the kinds of locks that can be set up using
    this locking mechanism.
    """
    CONFIGDOCS_UPDATE = {'name': 'configdocs_update', 'expires': 60}


class ApiLock(object):
    """
    Api Lock provides for a simple locking mechanism for shipyard's
    API classes.  The lock provided is intended to block conflicting
    activity across containers by using the backing database
    to calculate if a lock is currently held.

    The mechanism is as follows:
    1) Attempt to write a lock record to the database such that:
       there is no lock in the database of the same kind already that
       is not either released or expired
       1a) If the insert fails, the lock is not acquired.
    2) Query the database for the latest lock of the type provided.
       If the lock's id matches the ID of the process trying to
       acquire the lock, the process should succeed.
       If the lock ID doesn't match the record returned, the
       process attempting to acquire a lock is blocked/failed.
       (Note that the intended use is not to queue requests, but
       rather fail them if something else holds the lock)
    3) Upon completion of the activity, the lock holder will update
       the lock record to indicate that it is released.

    The database query used for insert will only insert if there
    is not already an active lock record for the given type.
    If the insert inserts zero rows, this indicates that the lock
    is not acquired, and does not require a subsequent query.

    The subsequent query is always used when the lock record insert
    has been succesful, to handle race conditions. The select query
    orders by both date and id, Whereby the randomness of the id
    provides for a tiebreaker.

    All locks expire based on their lock type, and default to
    60 seconds
    """

    def __init__(self,
                 api_lock_type,
                 reference_id,
                 user,
                 lock_db=SHIPYARD_DB):
        """
        Set up the Api Lock, using the input ApiLockType.
        Generates a ULID to represent this lock
        :param api_lock_type: the ApiLockType for this lock
        :param reference_id: the calling process' id provided for
            purposes of correlation
        :param user: the calling process' user for purposes of
            tracking
        """
        if (not isinstance(api_lock_type, ApiLockType) or
                api_lock_type.value.get('name') is None):
            raise ApiLockSetupError(
                message='ApiLock requires a valid ApiLockType'
            )
        self.lock_id = ulid.ulid()
        self.lock_type_name = api_lock_type.value.get('name')
        self.expires = api_lock_type.value.get('expires', 60)
        self.reference_id = reference_id
        self.user = user
        self.lock_db = lock_db

    def acquire(self):
        """
        Acquires a lock
        Responds with an ApiLockAcquireError if the lock is not
        acquired
        """
        LOG.info('Acquiring lock type: %s. Lock id: %s.',
                 self.lock_type_name,
                 self.lock_id)

        holds_lock = False
        insert_worked = self.lock_db.insert_api_lock(
            lock_id=self.lock_id,
            lock_type=self.lock_type_name,
            expires=self.expires,
            user=self.user,
            reference_id=self.reference_id
        )
        LOG.info('Insert lock %s %s',
                 self.lock_id,
                 'succeeded' if insert_worked else 'failed')

        if insert_worked:
            lock_retrieved = self.lock_db.get_api_lock(
                lock_type=self.lock_type_name
            )
            holds_lock = lock_retrieved == self.lock_id
            LOG.info(
                'Lock %s is currently held. This lock is %s. Match=%s',
                lock_retrieved,
                self.lock_id,
                holds_lock
            )

        if not holds_lock:
            LOG.info('Api Lock not acquired')
            raise ApiLockAcquireError()

    def release(self):
        """
        Release the lock
        """
        try:
            self.lock_db.release_api_lock(self.lock_id)
        except Exception as error:
            # catching Exception because this is a non-fatal case
            # and has no expected action to be taken.
            LOG.error('Exception raised during release of api lock: %s. '
                      'Unreleased lock for %s will expire in not more than '
                      '%s seconds. Exception: %s',
                      self.lock_id,
                      self.lock_type_name,
                      self.expires,
                      str(error))


class ApiLockError(Exception):
    """
    Base exception for all api lock exceptions
    """

    def __init__(self, message=None):
        self.message = message
        super().__init__()


class ApiLockSetupError(ApiLockError):
    """
    Specifies that there was a problem during setup of the lock
    """
    pass


class ApiLockAcquireError(ApiLockError):
    """
    Signals to the calling process that this lock was not acquired
    """
    pass
