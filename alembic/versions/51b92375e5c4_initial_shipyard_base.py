"""initial shipyard  base

Revision ID: 51b92375e5c4
Revises:
Create Date: 2017-09-12 11:12:23.768269

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import (types, func)
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = '51b92375e5c4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create the initial tables needed by shipyard
    26 character IDs are ULIDs. See: https://github.com/mdipierro/ulid
    """
    op.create_table(
        'actions',
        # ULID key for the action
        sa.Column('id', types.String(26), primary_key=True),
        # The name of the action invoked
        sa.Column('name', types.String(50), nullable=False),
        # The parameters passed by the user to the action
        sa.Column('parameters', pg.JSONB, nullable=True),
        # The DAG/workflow name used in airflow, if applicable
        sa.Column('dag_id', sa.Text, nullable=True),
        # The DAG/workflow execution time string from airflow, if applicable
        sa.Column('dag_execution_date', sa.Text, nullable=True),
        # The invoking user
        sa.Column('user', sa.Text, nullable=False),
        # Timestamp of when an action was invoked
        sa.Column('datetime',
                  types.TIMESTAMP(timezone=True),
                  server_default=func.now()),
        # The user provided or shipayrd generated context marker
        sa.Column('context_marker', types.String(36), nullable=False)
    )

    op.create_table(
        'preflight_validation_failures',
        # ID (ULID) of the preflight validation failure
        sa.Column('id', types.String(26), primary_key=True),
        # The ID of action this failure is associated with
        sa.Column('action_id', types.String(26), nullable=False),
        # The common language name of the validation that failed
        sa.Column('validation_name', sa.Text, nullable=True),
        # The text indicating details of the failure
        sa.Column('details', sa.Text, nullable=True),
    )

    op.create_table(
        'action_command_audit',
        # ID (ULID) of the audit
        sa.Column('id', types.String(26), primary_key=True),
        # The ID of action this audit record
        sa.Column('action_id', types.String(26), nullable=False),
        # The text indicating command invoked
        sa.Column('command', sa.Text, nullable=False),
        # The user that invoked the command
        sa.Column('user', sa.Text, nullable=False),
        # Timestamp of when the command was invoked
        sa.Column('datetime',
                  types.TIMESTAMP(timezone=True),
                  server_default=func.now()),
    )

def downgrade():
    """
    Remove the database objects created by this revision
    """
    op.drop_table('actions')
    op.drop_table('preflight_validation_failures')
    op.drop_table('action_command_audit')
