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
Enacapsulates a deckhand API client
"""
import enum
import logging

from oslo_config import cfg
import requests
from requests.exceptions import RequestException
import yaml

from shipyard_airflow.control.service_endpoints import (Endpoints,
                                                        get_endpoint,
                                                        get_token)

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class DeckhandPaths(enum.Enum):
    """
    Enumeration of the paths to deckhand
    """
    BUCKET_DOCS = '/bucket/{}/documents'
    RENDERED_REVISION_DOCS = '/revisions/{}/rendered-documents'
    REVISION = '/revisions/{}'
    REVISION_DIFF = '/revisions/{}/diff/{}'
    REVISION_DOCS = '/revisions/{}/documents'
    REVISION_LIST = '/revisions'
    REVISION_TAG_LIST = '/revisions/{}/tags'
    REVISION_TAG = '/revisions/{}/tags/{}'
    REVISION_VALIDATION_LIST = '/revisions/{}/validations'
    REVISION_VALIDATION = '/revisions/{}/validations/{}'
    REVISION_VALIDATION_ENTRY = (
        '/revisions/{}/validations/{}/entries/{}'
    )
    ROLLBACK = '/rollback/{}'


class DeckhandClient(object):
    """
    A rudimentary client for deckhand in lieu of a provided client
    """
    def __init__(self, context_marker):
        """
        Sets up this Deckhand client with the supplied context marker
        """
        self.context_marker = context_marker

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
        revisions = yaml.load(response.text)
        return revisions.get('results', [])

    def get_revision_count(self):
        """
        Returns the count of revisions in deckhand
        """
        response = self._get_request(
            DeckhandClient.get_path(DeckhandPaths.REVISION_LIST)
        )
        self._handle_bad_response(response)
        revisions = yaml.load(response.text)
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
        response.raise_for_status()
        return yaml.load(response.text)

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
        diff = yaml.load(response.text)
        return diff

    def get_docs_from_revision(self, revision_id, bucket_id=None):
        """
        Retrieves the collection of docs from the revision specified
        for the bucket_id specified
        :returns: a string representing the response.text from Deckhand
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_DOCS
        ).format(revision_id)

        # if a bucket_id is specified, limit the response to a bucket
        query = None
        if bucket_id is not None:
            query = {'status.bucket': bucket_id}
        response = self._get_request(url, params=query)
        self._handle_bad_response(response)
        return response.text

    def get_rendered_docs_from_revision(self, revision_id, bucket_id=None):
        """
        Returns the full set of rendered documents for a revision
        """
        url = DeckhandClient.get_path(
            DeckhandPaths.RENDERED_REVISION_DOCS
        ).format(revision_id)

        query = None
        if bucket_id is not None:
            query = {'status.bucket': bucket_id}
        response = self._get_request(url, params=query)
        self._handle_bad_response(response)
        return response.text

    @staticmethod
    def _build_validation_base(dh_validation):
        # creates the base structure for validation response
        return {
            'count': dh_validation.get('count'),
            'results': []
        }

    @staticmethod
    def _build_validation_entry(dh_val_entry):
        # creates a validation entry by stripping off the URL
        # that the end user can't use anyway.
        dh_val_entry.pop('url', None)
        return dh_val_entry

    def get_all_revision_validations(self, revision_id):
        """
        Collects and returns the yamls of the validations for a
        revision
        """
        val_resp = {}
        response = self._get_base_validation_resp(revision_id)
        # if the base call is no good, stop.
        self._handle_bad_response(response)
        all_validation_resp = yaml.load(response.text)
        if all_validation_resp:
            val_resp = DeckhandClient._build_validation_base(
                all_validation_resp
            )
            validations = all_validation_resp.get('results')
            for validation_subset in validations:
                subset_name = validation_subset.get('name')
                subset_response = self._get_subset_validation_response(
                    revision_id,
                    subset_name
                )
                # don't fail hard on a single subset not replying
                # TODO (bryan-strassner) maybe this should fail hard?
                #                        what if they all fail?
                if subset_response.status_code >= 400:
                    LOG.error(
                        'Failed to retrieve %s validations for revision %s',
                        subset_name, revision_id
                    )
                val_subset = yaml.load(subset_response.text)
                entries = val_subset.get('results')
                for entry in entries:
                    entry_id = entry.get('id')
                    e_resp = self._get_entry_validation_response(revision_id,
                                                                 subset_name,
                                                                 entry_id)
                    if e_resp.status_code >= 400:
                        # don't fail hard on a single entry not working
                        # TODO (bryan-strassner) maybe this should fail hard?
                        #                        what if they all fail?
                        LOG.error(
                            'Failed to retrieve entry %s for category %s '
                            'for revision %s',
                            entry_id, subset_name, revision_id
                        )
                    entry = yaml.load(e_resp.text)
                    val_resp.get('results').append(
                        DeckhandClient._build_validation_entry(entry)
                    )
        return val_resp

    def _get_base_validation_resp(self, revision_id):
        # wraps getting the base validation response
        url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_VALIDATION_LIST
        ).format(revision_id)

        return self._get_request(url)

    def _get_subset_validation_response(self, revision_id, subset_name):
        # wraps getting the subset level of detail of validations
        subset_url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_VALIDATION
        ).format(revision_id, subset_name)

        return self._get_request(subset_url)

    def _get_entry_validation_response(self,
                                       revision_id,
                                       subset_name,
                                       entry_id):
        # wraps getting the entry level detail of validation
        e_url = DeckhandClient.get_path(
            DeckhandPaths.REVISION_VALIDATION_ENTRY
        ).format(revision_id, subset_name, entry_id)

        e_resp = self._get_request(e_url)

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
            headers = {
                'X-Context-Marker': self.context_marker,
                'X-Auth-Token': get_token()
            }
            if document_data is not None:
                headers['content-type'] = 'application/x-yaml'

            DeckhandClient._log_request('PUT', url, params)
            response = requests.put(url,
                                    params=params,
                                    headers=headers,
                                    data=document_data,
                                    timeout=(5, 30))
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
            headers = {
                'content-type': 'application/x-yaml',
                'X-Context-Marker': self.context_marker,
                'X-Auth-Token': get_token()
            }

            DeckhandClient._log_request('GET', url, params)
            response = requests.get(url,
                                    params=params,
                                    headers=headers,
                                    timeout=(5, 30))
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
            headers = {
                'X-Context-Marker': self.context_marker,
                'X-Auth-Token': get_token()
            }
            if document_data is not None:
                headers['content-type'] = 'application/x-yaml'

            DeckhandClient._log_request('POST', url, params)
            response = requests.post(url,
                                     params=params,
                                     headers=headers,
                                     data=document_data,
                                     timeout=(5, 30))
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
            headers = {
                'X-Context-Marker': self.context_marker,
                'X-Auth-Token': get_token()
            }

            DeckhandClient._log_request('DELETE', url, params)
            response = requests.delete(url,
                                       params=params,
                                       headers=headers,
                                       timeout=(5, 30))
            return response
        except RequestException as rex:
            LOG.error(rex)
            raise DeckhandAccessError(
                response_message=(
                    'Unable to Invoke deckhand: {}'.format(str(rex)),
                )
            )

#
# Deckhand stateful messages wrapped as exceptions
#


class DeckhandStatefulError(Exception):
    """
    Base exception for errors that indicate some stateful-based
    condition in deckhand. Not intended for use directly
    """
    def __init__(self, response_message=None):
        super().__init__()
        self.response_message = response_message


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


class DeckhandResponseError(Exception):
    """
    Indicates that a response was returned from
    Deckhand that was not expected
    """
    def __init__(self, status_code, response_message=None):
        super().__init__()
        self.status_code = status_code
        self.response_message = response_message


class DeckhandRejectedInputError(DeckhandResponseError):
    """
    Indicates that Deckhand has rejected input for some reason
    This is usually accompanied by a 400 status code from Deckhand
    """
    pass

#
# Errors accessing Deckhand
#


class DeckhandAccessError(Exception):
    """
    Used to indicate that accessing Deckhand has failed.
    This is not the same as a bad response from Deckhand:
    See DeckhandResponseError
    """
    def __init__(self, response_message=None):
        super().__init__()
        self.response_message = response_message
