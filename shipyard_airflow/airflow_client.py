import requests

from shipyard_airflow.errors import AirflowError


class AirflowClient(object):
    def __init__(self, url):
        self.url = url

    def get(self):
        response = requests.get(self.url).json()

        # This gives us more freedom to handle the responses from airflow
        if response["output"]["stderr"]:
            raise AirflowError(response["output"]["stderr"])
        else:
            return response["output"]["stdout"]
