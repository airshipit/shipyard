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
    steps = format_utils.table_factory(
        field_names=['Steps', 'Index', 'State', 'Footnotes']
    )
    # rendered notes , a list of lists of notes
    r_notes = []

    if step_list:
        for step in step_list:
            notes = step.get('notes')
            if notes:
                r_notes.append(format_notes(notes))
            steps.add_row([
                'step/{}/{}'.format(action_id, step.get('id')),
                step.get('index'),
                step.get('state'),
                "({})".format(len(r_notes)) if notes else ""
            ])
    else:
        steps.add_row(['None', '', '', ''])

    return "{}\n\n{}".format(
        format_utils.table_get_string(steps),
        notes_table("Step", r_notes))


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
                     'Step Succ/Fail/Oth', 'Footnotes'])
    # list of lists of rendered notes
    r_notes = []
    if action_list:
        # sort by id, which is ULID - chronological.
        for action in sorted(action_list, key=lambda k: k['id']):
            notes = action.get('notes')
            if notes:
                r_notes.append(format_notes(notes))
            actions.add_row([
                action.get('name'),
                'action/{}'.format(action.get('id')),
                action.get('action_lifecycle'),
                action.get('dag_execution_date'),
                _step_summary(action.get('steps', [])),
                "({})".format(len(r_notes)) if notes else ""
            ])
    else:
        actions.add_row(['None', '', '', '', '', ''])

    return "{}\n\n{}".format(
        format_utils.table_get_string(actions),
        notes_table("Action", r_notes))


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


def gen_site_statuses(status_dict):
    """Generates site statuses table.

    Assumes status_types as list of filters and status_dict a dictionary
    with statuses lists
    """
    formatted_output = ''

    status_types = status_dict.keys()

    for st in status_types:
        call_func = _site_statuses_switcher(st)
        op = call_func(status_dict)
        formatted_output = "{}\n{}\n".format(formatted_output, op)

    return formatted_output


def _gen_machines_powerstate_table(status_dict):
    # Generates machines power states status table

    machine_powerstate_table = format_utils.table_factory(
        field_names=['Hostname', 'Power State'])

    pwrstate_list = status_dict.get('machines_powerstate')

    if pwrstate_list:
        for pwrstate in pwrstate_list:
            machine_powerstate_table.add_row(
                [pwrstate.get('hostname'),
                 pwrstate.get('power_state')])
    else:
        machine_powerstate_table.add_row(['', ''])

    return format_utils.table_get_string(table=machine_powerstate_table,
                                         title="Machines Power State:",
                                         vertical_char=' ')


def _gen_nodes_provision_status_table(status_dict):
    # Generates nodes provision status table

    nodes_status_table = format_utils.table_factory(
        field_names=['Hostname', 'Status'])
    prov_status_list = status_dict.get('nodes_provision_status')

    if prov_status_list:
        for status in prov_status_list:
            nodes_status_table.add_row(
                [status.get('hostname'),
                 status.get('status')])
    else:
        nodes_status_table.add_row(['', ''])

    return format_utils.table_get_string(table=nodes_status_table,
                                         title="Nodes Provision Status:",
                                         vertical_char=' ')


def _site_statuses_switcher(status_type):
    """Maps status types with a callabe function to the format
     output.

    The dictionary will be updated with new functions
    to map future supported status-types for "site-statuses"
    """
    status_func_switcher = {
        'nodes_provision_status': _gen_nodes_provision_status_table,
        'machines_powerstate': _gen_machines_powerstate_table,
    }

    call_func = status_func_switcher.get(status_type, lambda: None)

    return call_func


def gen_detail_notes(title, dict_with_notes):
    """Generates a standard formatted section of notes

    :param title: the title for the notes section. E.g.: "Step"
    :param dict_with_notes: a dictionary with a possible notes field.
    :returns: string of notes or empty string if there were no notes
    """
    n_strings = format_notes(dict_with_notes.get('notes', []))
    if n_strings:
        return "{} Notes:\n{}".format(title, "\n".join(n_strings))
    return ""


def notes_table(title, notes_list):
    """Format a table of notes

    :param title: the header for the table. e.g.: "Step"
    :param list notes_list: a list of lists of formatted notes:
        e.g.:[[note1,note2],[note3]]
        The notes ideally have been pre-formatted by "format_notes"

    :returns: string of a table e.g.:

    Step Notes  Note
    (1)         > note1
                  - Info avail...
                > note2
    (2)         > note3

    If notes_list is empty, returns an empty string.
    """
    if not notes_list:
        return ""
    headers = ["{} Footnotes".format(title), "Note"]
    rows = []
    index = 1
    for notes in notes_list:
        rows.append(["({})".format(index), "\n".join(notes)])
        index += 1
    return format_utils.table_get_string(
        format_utils.table_factory(headers, rows))


def format_notes(notes):
    """Formats a list of notes.

    :param list notes: The list of note dictionaries to display
    :returns: a list of note strings

    Assumed note dictionary example:
    {
        'assoc_id': "action/12345678901234567890123456,
        'subject': "12345678901234567890123456",
        'sub_type': "action",
        'note_val': "message",
        'verbosity': 1,
        'note_id': "09876543210987654321098765",
        'note_timestamp': "2018-10-08 14:23:53.346534",
        'resolved_url_value': \
            "Details at notedetails/09876543210987654321098765"
    }

    Resulting in:

    > action:12345678901234567890123456(2018-10-08 14:23:53.346534): message
      - Info available with 'describe notedetails/09876543210987654321098765'
    """
    nl = []
    for n in notes:
        try:
            s = "> {}:{}({}): {}".format(
                n['sub_type'],
                n['subject'],
                n['note_timestamp'],
                n['note_val']
            )
            if n['resolved_url_value']:
                s += ("\n  - Info available with "
                      "'describe notedetails/{}'".format(n['note_id']))
        except KeyError:
            s = "!!! Unparseable Note: {}".format(n)

        nl.append(s)
    return nl
