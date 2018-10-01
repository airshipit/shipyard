"""create notes table

Revision ID: 7486ddec1979
Revises: 51b92375e5c4
Create Date: 2018-10-02 16:10:08.139378

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import (types, func)


# revision identifiers, used by Alembic.
revision = '7486ddec1979'
down_revision = '51b92375e5c4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notes',
        # ULID key for the note
        sa.Column('note_id', types.String(26), primary_key=True),
        # The supplied association id used for lookup
        sa.Column('assoc_id', types.String(128), nullable=False),
        # The supplied subject of the note (what is this note about?)
        sa.Column('subject', types.String(128), nullable=False),
        # The supplied type of the subject (what kind of thing is the subject?)
        sa.Column('sub_type', types.String(128), nullable=False),
        # The text value of the note
        sa.Column('note_val', sa.Text, nullable=False),
        # The numeric verbosity level of the note (1-5)
        sa.Column('verbosity', types.Integer, nullable=False),
        # An optional URL containing more info for the note
        sa.Column('link_url', sa.Text, nullable=True),
        # Boolean if the link requires a X-Auth-Token header
        sa.Column('is_auth_link', types.Boolean, nullable=False),
        # The creation timestamp for the note
        sa.Column('note_timestamp',
                  types.TIMESTAMP(timezone=True),
                  server_default=func.now()),
    )


def downgrade():
    op.drop_table('notes')
