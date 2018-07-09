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
"""Reusable parts for outputting Shipyard results in CLI format"""

from shipyard_client.cli import format_utils


def gen_action_steps(step_list, action_id):
    """Generate a table from the list of steps.

    Assumes that the input list contains dictionaries with 'id', 'index', and
    'state' fields.
    Returns a string representation of the table.
    """
    # Generate the steps table.
    steps = format_utils.table_factory(field_names=['Steps', 'Index', 'State'])
    if step_list:
        for step in step_list:
            steps.add_row([
                'step/{}/{}'.format(action_id, step.get('id')),
                step.get('index'),
                step.get('state')
            ])
    else:
        steps.add_row(['None', '', ''])

    return format_utils.table_get_string(steps)


def gen_action_commands(command_list):
    """Generate a table from the list of commands

    Assumes command_list is a list of dictionaries with 'command', 'user', and
    'datetime'.
    """
    cmds = format_utils.table_factory(
        field_names=['Commands', 'User', 'Datetime'])
    if command_list:
        for cmd in command_list:
            cmds.add_row(
                [cmd.get('command'),
                 cmd.get('user'),
                 cmd.get('datetime')])
    else:
        cmds.add_row(['None', '', ''])

    return format_utils.table_get_string(cmds)


def gen_action_validations(validation_list):
    """Generates a CLI formatted listing of validations

    Assumes validation_list is a list of dictionaries with 'validation_name',
    'action_id', 'id', and 'details'.
    """
    if validation_list:
        validations = []
        for val in validation_list:
            validations.append('{} : validation/{}/{}\n'.format(
                val.get('validation_name'), val.get('action_id'), val.get(
                    'id')))
            validations.append(val.get('details'))
            validations.append('\n\n')
        return 'Validations: {}'.format('\n'.join(validations))
    else:
        return 'Validations: {}'.format('None')


def gen_action_details(action_dict):
    """Generates the detailed information for an action

    Assumes action_dict is a dictionary with 'name', 'id', 'action_lifecycle',
    'parameters', 'datetime', 'dag_status', 'context_marker', and 'user'
    """
    details = format_utils.table_factory()
    details.add_row(['Name:', action_dict.get('name')])
    details.add_row(['Action:', 'action/{}'.format(action_dict.get('id'))])
    details.add_row(['Lifecycle:', action_dict.get('action_lifecycle')])
    details.add_row(['Parameters:', str(action_dict.get('parameters'))])
    details.add_row(['Datetime:', action_dict.get('datetime')])
    details.add_row(['Dag Status:', action_dict.get('dag_status')])
    details.add_row(['Context Marker:', action_dict.get('context_marker')])
    details.add_row(['User:', action_dict.get('user')])
    return format_utils.table_get_string(details)


def gen_action_step_details(step_dict, action_id):
    """Generates the detailed information for an action step

    Assumes action_dict is a dictionary with 'index', 'state', 'start_date',
    'end_date', 'duration', 'try_number', and 'operator'
    """
    details = format_utils.table_factory()
    details.add_row(['Name:', step_dict.get('task_id')])
    details.add_row(
        ['Task ID:', 'step/{}/{}'.format(action_id, step_dict.get('task_id'))])
    details.add_row(['Index:', step_dict.get('index')])
    details.add_row(['State:', step_dict.get('state')])
    details.add_row(['Start Date:', step_dict.get('start_date')])
    details.add_row(['End Date:', step_dict.get('end_date')])
    details.add_row(['Duration:', step_dict.get('duration')])
    details.add_row(['Try Number:', step_dict.get('try_number')])
    details.add_row(['Operator:', step_dict.get('operator')])
    return format_utils.table_get_string(details)


def gen_action_table(action_list):
    """Generates a list of actions

    Assumes action_list is a list of dictionaries with 'name', 'id', and
    'action_lifecycle'
    """
    actions = format_utils.table_factory(
        field_names=['Name', 'Action', 'Lifecycle', 'Execution Time',
                     'Step Succ/Fail/Oth'])
    if action_list:
        # sort by id, which is ULID - chronological.
        for action in sorted(action_list, key=lambda k: k['id']):
            actions.add_row([
                action.get('name'),
                'action/{}'.format(action.get('id')),
                action.get('action_lifecycle'),
                action.get('dag_execution_date'),
                _step_summary(action.get('steps', []))
            ])
    else:
        actions.add_row(['None', '', '', '', ''])

    return format_utils.table_get_string(actions)


def _step_summary(step_list):
    """Creates a single string representation of the step status

    Success/Failed/Other counts in each position
    """
    successes = 0
    failures = 0
    other = 0
    for s in step_list:
        state = s.get('state')
        if state in ['success']:
            successes += 1
        elif state in ['failed']:
            failures += 1
        else:
            other += 1
    return "{}/{}/{}".format(successes, failures, other)


def gen_collection_table(collection_list):
    """Generates a list of collections and their status

    Assumes collection_list is a list of dictionares with 'collection_name',
    'base_status', 'new_status', 'base_version', 'base_revision', 'new_version'
    and 'new_revision'.
    """
    collections = format_utils.table_factory(
        field_names=['Collection',
                     'Base',
                     'New'])

    if collection_list:
        for collection in collection_list:
            collections.add_row([
                collection.get('collection_name'),
                collection.get('base_status'),
                collection.get('new_status')
            ])

        collections_title = (
            'Comparing Base: {} (Deckhand revision {}) \n\t to New: {} '
            '(Deckhand revision {})'.format(
                collection.get('base_version'),
                collection.get('base_revision'),
                collection.get('new_version'),
                collection.get('new_revision')))

    else:
        collections.add_row(['None', '', ''])
        collections_title = ''

    return format_utils.table_get_string(table=collections,
                                         title=collections_title,
                                         vertical_char=' ')


def gen_workflow_table(workflow_list):
    """Generates a list of workflows

    Assumes workflow_list is a list of dictionaries with 'workflow_id' and
    'state'
    """
    workflows = format_utils.table_factory(field_names=['Workflows', 'State'])
    if workflow_list:
        for workflow in workflow_list:
            workflows.add_row(
                [workflow.get('workflow_id'),
                 workflow.get('state')])
    else:
        workflows.add_row(['None', ''])

    return format_utils.table_get_string(workflows)


def gen_workflow_details(workflow_dict):
    """Generates a workflow detail

    Assumes workflow_dict has 'execution_date', 'end_date', 'workflow_id',
    'start_date', 'external_trigger', 'steps', 'dag_id', 'state', 'run_id',
    and 'sub_dags'
    """
    details = format_utils.table_factory()
    details.add_row(['Workflow:', workflow_dict.get('workflow_id')])

    details.add_row(['State:', workflow_dict.get('state')])
    details.add_row(['Dag ID:', workflow_dict.get('dag_id')])
    details.add_row(['Execution Date:', workflow_dict.get('execution_date')])
    details.add_row(['Start Date:', workflow_dict.get('start_date')])
    details.add_row(['End Date:', workflow_dict.get('end_date')])
    details.add_row(
        ['External Trigger:',
         workflow_dict.get('external_trigger')])
    return format_utils.table_get_string(details)


def gen_workflow_steps(step_list):
    """Generates a table of steps for a workflow

    Assumes step_list is a list of dictionaries with 'task_id' and 'state'
    """
    steps = format_utils.table_factory(field_names=['Steps', 'State'])
    if step_list:
        for step in step_list:
            steps.add_row([step.get('task_id'), step.get('state')])
    else:
        steps.add_row(['None', ''])

    return format_utils.table_get_string(steps)


def gen_sub_workflows(wf_list):
    """Generates the list of Sub Workflows

    Assumes wf_list is a list of dictionaries with the same contents as a
    standard workflow
    """
    wfs = []
    for wf in wf_list:
        wfs.append(gen_workflow_details(wf))
    return '\n\n'.join(wfs)
