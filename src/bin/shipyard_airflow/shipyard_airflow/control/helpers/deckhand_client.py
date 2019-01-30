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
"""Enacapsulates a deckhand API client"""
# TODO(bryan-strassner) replace this functionality with a real Deckhand client
import enum
import logging

from oslo_config import cfg
import requests
from requests.exceptions import RequestException
import yaml

from shipyard_airflow.control.service_endpoints import (Endpoints,
                                                        get_endpoint,
                                                        get_token)
from shipyard_airflow.shipyard_const import CustomHeaders

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class DeckhandPaths(enum.Enum):
    """
    Enumeration of the paths to deckhand
    """
    BUCKET_DOCS = '/buckets/{}/documents'
    RENDERED_REVISION_DOCS = '/revisions/{}/rendered-documents'
    REVISION = '/revisions/{}'
    REVISION_DIFF = '/revisions/{}/diff/{}'
    REVISION_DOCS = '/revisions/{}/documents'
    REVISION_LIST = '/revisions'
    REVISION_TAG_LIST = '/revisions/{}/tags'
    REVISION_TAG = '/revisions/{}/tags/{}'
    REVISION_VALIDATIONS_LIST = '/revisions/{}/validations/detail'
    ROLLBACK = '/rollback/{}'


class DeckhandClient(object):
    """
    A rudimentary client for deckhand in lieu of a provided client
    """
    def __init__(self, context_marker, end_user=None):
        """
        Sets up this Deckhand client with the supplied context marker
        """
        self.context_marker = context_marker
        self.end_user = end_user

    _deckhand_svc_url = None

    @staticmethod
    def get_path(path):
        """
        Looks up and returns the Deckhand path as a full url pattern
        string if passed a value from DeckhandPaths
        """
        if not DeckhandClient._deckhand_svc_url:
            DeckhandClient._deckhand_svc_url = get_endpoint(
                Endpoints.DECKHAND
            )
        return DeckhandClient._deckhand_svc_url + path.value

    def get_latest_revision(self):
        """
        Retrieve the latest revision object, or raise a
        NoRevisionsExistError if there are no revisions
        """
        revision_list = self.get_revision_list()
        if revision_list:
            return revision_list[-1]
        else:
            raise NoRevisionsExistError()

    def get_revision_list(self):
        """
        Returns the list of revision dictionary objects
        """
        response = self._get_request(
            DeckhandClient.get_path(DeckhandPaths.REVISION_LIST)
        )
        self._handle_bad_response(response)
        revisions = yaml.safe_load(response.text)
        return revisions.get('results', [])

    def get_revision_count(self):
        """
        Returns the count of revisions in deckhand
        """
        response = self._get_request(
            DeckhandClient.get_path(DeckhandPaths.REVISION_LIST)
        )
        self._handle_bad_response(response)
        revisions = yaml.safe_load(response.text)
        return revisions['count']

    def get_latest_rev_id(self):
        """
        Returns the latest revision's id
        """
        try:
            return self.get_latest_revision().get('id', 0)
        except NoRevisionsExistError:
            return 0

    def put_bucket(self, bucket_name, documents):
        """
        Issues a put against deckhand to store a bucket
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.BUCKET_DOCS
        ).format(bucket_name)

        response = self._put_request(url, document_data=documents)
        if response.status_code == 400:
            # bad input
            raise DeckhandRejectedInputError(
                # TODO (bryan-strassner) The response from DH is json and
                # should probably be picked apart into a message here instead
                # of being escaped json when it's done
                response_message=response.text,
                status_code=response.status_code
            )
        if response.status_code == 409:
            # conflicting bucket
            raise DocumentExistsElsewhereError(
                # TODO (bryan-strassner) The response from DH is json and
                # should probably be picked apart into a message here instead
                # of being escaped json when it's done
                response_message=response.text
            )
        self._handle_bad_response(response)

    def tag_revision(self, revision_id, tag):
        """
        Adds the supplied tag to the specified revision
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_TAG
        ).format(revision_id, tag)

        response = self._post_request(url)
        self._handle_bad_response(response)
        return yaml.safe_load(response.text)

    def rollback(self, target_revision_id):
        """
        Triggers deckhand to make a new revision that matches exactly
        the state of documents/buckets of a prior revision.
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.ROLLBACK
        ).format(target_revision_id)

        response = self._post_request(url)
        self._handle_bad_response(response)

    def reset_to_empty(self):
        """
        Warning, this will prompt deckhand to delete everything. gone.
        """
        url = DeckhandClient.get_path(DeckhandPaths.REVISION_LIST)
        response = self._delete_request(url)
        self._handle_bad_response(response)

    def get_diff(self, old_revision_id, new_revision_id):
        """
        Retrieves the bucket-based difference between revisions.
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_DIFF
        ).format(old_revision_id, new_revision_id)

        response = self._get_request(url)
        self._handle_bad_response(response)
        diff = yaml.safe_load(response.text)
        return diff

    def get_docs_from_revision(self, revision_id, bucket_id=None,
                               cleartext_secrets=False):
        """
        Retrieves the collection of docs from the revision specified
        for the bucket_id specified
        cleartext_secrets: Should deckhand show or redact secrets.
        :returns: a string representing the response.text from Deckhand
        """

        url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_DOCS
        ).format(revision_id)

        # if a bucket_id is specified, limit the response to a bucket
        query = {}
        if bucket_id is not None:
            query = {'status.bucket': bucket_id}
        if cleartext_secrets is True:
            query['cleartext-secrets'] = 'true'
        response = self._get_request(url, params=query)
        self._handle_bad_response(response)
        return response.text

    def get_render_errors(self, revision_id):
        """Retrieve any error messages from rendering configdocs or []

        Entries in the list returned are {error: ..., message: ...} format.
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.RENDERED_REVISION_DOCS
        ).format(revision_id)

        errors = []

        LOG.debug("Retrieving rendered docs checking for validation messages")
        response = self._get_request(url)
        if response.status_code >= 400:
            err_resp = yaml.safe_load(response.text)
            errors = err_resp.get('details', {}).get('messageList', [])
            if not errors:
                # default message if none were specified.
                errors.append({
                    "error": True,
                    "message": ("Deckhand has reported an error but did not "
                                "specify messages. Response: {}".format(
                                    response.text))})
        return errors

    def get_rendered_docs_from_revision(self, revision_id, bucket_id=None,
                                        cleartext_secrets=False):
        """
        Returns the full set of rendered documents for a revision
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.RENDERED_REVISION_DOCS
        ).format(revision_id)

        query = {}
        if bucket_id is not None:
            query = {'status.bucket': bucket_id}
        if cleartext_secrets is True:
            query['cleartext-secrets'] = 'true'
        response = self._get_request(url, params=query)
        self._handle_bad_response(response)
        return response.text

    def get_all_revision_validations(self, revision_id):
        """
        Collects a YAML document containing a list of validation results
        corresponding to a Deckhand revision ID.

        :param revision_id: A Deckhand revision ID corresponding to a set of
            documents.
        :returns: A YAML document containing a results key mapped to a list of
            validation results.
        """
        # TODO(@drewwalters96): This method should be replaced with usage of
        #     the official Deckhand client.
        url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_VALIDATIONS_LIST
        ).format(revision_id)

        response = self._get_request(url)
        self._handle_bad_response(response)

        return yaml.safe_load(response.text)

    @staticmethod
    def _handle_bad_response(response, threshold=400):
        # common handler for bad responses from invoking Deckhand
        # rasises a DeckhandResponseError if the response status
        # is >= threshold
        if response.status_code >= threshold:
            LOG.error(
                ('An undesired response was returned by Deckhand. '
                 'Status: %s above threshold %s. Response text: %s'),
                response.status_code,
                threshold,
                response.text
            )
            raise DeckhandResponseError(
                status_code=response.status_code,
                response_message=response.text
            )

    # the _get, _put, _post functions below automatically supply
    # the following headers:
    # content-type: application/x-yaml
    # X-Context-Marker: {the context marker}
    # X-Auth-Token: {a current auth token}
    # X-End-User: {current Shipyard user}

    def _get_headers(self):
        # Populate HTTP headers
        headers = {
            CustomHeaders.CONTEXT_MARKER.value: self.context_marker,
            CustomHeaders.END_USER.value: self.end_user,
            'X-Auth-Token': get_token()
        }

        return headers

    @staticmethod
    def _log_request(method, url, params=None):
        # logs the details of a request being made
        LOG.info('Invoking %s %s', method, url)
        param_str = ''
        if params:
            param_str = ', '.join(
                "{}={}".format(key, val) for (key, val) in params.items()
            )
            LOG.info('Including parameters: %s', param_str)

    def _put_request(self, url, document_data=None, params=None):
        # invokes a PUT against the specified URL with the
        # supplied document_data body
        try:
            headers = self._get_headers()

            if document_data is not None:
                headers['content-type'] = 'application/x-yaml'

            DeckhandClient._log_request('PUT', url, params)
            response = requests.put(
                url,
                params=params,
                headers=headers,
                data=document_data,
                timeout=(
                    CONF.requests_config.deckhand_client_connect_timeout,
                    CONF.requests_config.deckhand_client_read_timeout))
            return response
        except RequestException as rex:
            LOG.error(rex)
            raise DeckhandAccessError(
                response_message=(
                    'Unable to Invoke deckhand: {}'.format(str(rex)),
                )
            )

    def _get_request(self, url, params=None):
        # invokes a GET against the specified URL
        try:
            headers = self._get_headers()
            headers['content-type'] = 'application/x-yaml'

            if not params:
                params = None

            DeckhandClient._log_request('GET', url, params)
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=(
                    CONF.requests_config.deckhand_client_connect_timeout,
                    CONF.requests_config.deckhand_client_read_timeout))
            return response
        except RequestException as rex:
            LOG.error(rex)
            raise DeckhandAccessError(
                response_message=(
                    'Unable to Invoke deckhand: {}'.format(str(rex)),
                )
            )

    def _post_request(self, url, document_data=None, params=None):
        # invokes a POST against the specified URL with the
        # supplied document_data body
        try:
            headers = self._get_headers()

            if document_data is not None:
                headers['content-type'] = 'application/x-yaml'

            DeckhandClient._log_request('POST', url, params)
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data=document_data,
                timeout=(
                    CONF.requests_config.deckhand_client_connect_timeout,
                    CONF.requests_config.deckhand_client_read_timeout))
            return response
        except RequestException as rex:
            LOG.error(rex)
            raise DeckhandAccessError(
                response_message=(
                    'Unable to Invoke deckhand: {}'.format(str(rex)),
                )
            )

    def _delete_request(self, url, params=None):
        # invokes a DELETE against the specified URL
        try:
            headers = self._get_headers()

            DeckhandClient._log_request('DELETE', url, params)
            response = requests.delete(
                url,
                params=params,
                headers=headers,
                timeout=(
                    CONF.requests_config.deckhand_client_connect_timeout,
                    CONF.requests_config.deckhand_client_read_timeout))
            return response
        except RequestException as rex:
            LOG.error(rex)
            raise DeckhandAccessError(
                response_message=(
                    'Unable to Invoke deckhand: {}'.format(str(rex)),
                )
            )

#
# Exceptions
#


class DeckhandError(Exception):
    """Base exception for all exceptions raised by this client"""
    def __init__(self, response_message=None):
        super().__init__()
        self.response_message = response_message

#
# Deckhand stateful messages wrapped as exceptions
#


class DeckhandStatefulError(DeckhandError):
    """Base exception for errors for stateful-based conflicts in Deckhand."""
    pass


class NoRevisionsExistError(DeckhandStatefulError):
    """
    Indicates that no revisions exist when trying to retrieve the latest
    revision (Deckhand is empty)
    """
    pass


class DocumentExistsElsewhereError(DeckhandStatefulError):
    """
    Indicates that a document being added is active in
    a bucket that doesn't match the bucket currently
    being added to deckhand.
    """
    pass

#
# Deckhand processing failures reported by Deckhand
#


class DeckhandResponseError(DeckhandError):
    """
    Indicates that a response was returned from
    Deckhand that was not expected
    """
    def __init__(self, status_code, response_message=None):
        super().__init__(response_message)
        self.status_code = status_code


class DeckhandRejectedInputError(DeckhandResponseError):
    """
    Indicates that Deckhand has rejected input for some reason
    This is usually accompanied by a 400 status code from Deckhand
    """
    pass

#
# Errors accessing Deckhand
#


class DeckhandAccessError(DeckhandError):
    """
    Used to indicate that accessing Deckhand has failed.
    This is not the same as a bad response from Deckhand:
    See DeckhandResponseError
    """
    pass
