# -*- coding: utf-8 -*-

import json
import falcon

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

ERR_UNKNOWN = {'status': falcon.HTTP_500, 'title': 'Internal Server Error'}

ERR_AIRFLOW_RESPONSE = {
    'status': falcon.HTTP_400,
    'title': 'Error response from Airflow'
}


class AppError(Exception):
    def __init__(self, error=ERR_UNKNOWN, description=None):
        self.error = error
        self.error['description'] = description

    @property
    def title(self):
        return self.error['title']

    @property
    def status(self):
        return self.error['status']

    @property
    def description(self):
        return self.error['description']

    @staticmethod
    def handle(exception, req, res, error=None):
        res.status = exception.status
        meta = OrderedDict()
        meta['message'] = exception.title
        if exception.description:
            meta['description'] = exception.description
        res.body = json.dumps(meta)


class AirflowError(AppError):
    def __init__(self, description=None):
        super().__init__(ERR_AIRFLOW_RESPONSE)
        self.error['description'] = description
