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
Contains the json schemas for the REST interface, and provides the functions
to validate against the schemas.
see: http://json-schema.org
see: https://pypi.org/project/jsonschema/
"""
import json
import logging

from jsonschema import validate
from jsonschema.exceptions import FormatError, SchemaError, ValidationError

from shipyard_airflow.errors import AppError, InvalidFormatError

LOG = logging.getLogger(__name__)


def validate_json(json_string, schema):
    """
    invokes the validate function of jsonschema
    """
    schema_dict = json.loads(schema)
    schema_title = schema_dict['title']
    try:
        validate(json_string, schema_dict)
    except ValidationError as err:
        title = 'JSON validation failed: {}'.format(err.message)
        description = 'Failed validator: {} : {}'.format(
            err.validator, err.validator_value)
        LOG.error(title)
        LOG.error(description)
        raise InvalidFormatError(
            title=title,
            description=description,
        )
    except SchemaError as err:
        title = 'SchemaError: Unable to validate JSON: {}'.format(err)
        description = 'Invalid Schema: {}'.format(schema_title)
        LOG.error(title)
        LOG.error(description)
        raise AppError(title=title, description=description)
    except FormatError as err:
        title = 'FormatError: Unable to validate JSON: {}'.format(err)
        description = 'Invalid Format: {}'.format(schema_title)
        LOG.error(title)
        LOG.error(description)
        raise AppError(title=title, description=description)


# The action resource structure
ACTION = '''
    {
        "title": "Action schema",
        "type" : "object",
        "properties" : {
             "id" : {"type" : "string"},
            "name" : {"type" : "string"},
            "parameters" : {"type" : "object"},
            "user" : {"type" : "string"},
            "time" : {"type" : "string"},
            "actionStatus" : {
                "enum" : [
                    "Pending",
                    "Validation Failed",
                    "Processing",
                    "Complete",
                    "Failed"
                ]
            },
            "dagStatus" : {"type" : "string"},
            "validations" : {
                "type" : "array",
                "items" : {
                    "type" : "object",
                    "properties" : {
                        "id" : {"type" : "string"},
                        "status" : {
                            "enum" : [
                                "Passed",
                                "Failed",
                                "Pending"
                            ]
                        }
                    }
                }
            },
            "steps" : {
                "type" : "array",
                "items" : {
                    "type" : "object",
                    "properties" : {
                        "id" : {"type" : "string"},
                        "status" : {
                            "enum" : [
                                "Pending",
                                "Processing",
                                "Complete",
                                "Failed"
                            ]
                        }
                    }
                }
            }
        },
        "required" : ["name"]
    }
'''
