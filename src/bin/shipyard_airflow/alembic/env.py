from __future__ import with_statement

import os
from logging.config import fileConfig

from alembic import context
from oslo_config import cfg
from sqlalchemy import create_engine, pool

# this is the shipyard config object
CONF = cfg.CONF

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.attributes.get('configure_logger', True):
    fileConfig(config.config_file_name)

target_metadata = None


def get_url():
    """
    Returns the url to use instead of using the alembic configuration
    file
    """
    return CONF.base.postgresql_db


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    # Default code: url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = create_engine(get_url())
    # Default/generated code:
    #  connectable = engine_from_config(
    #     config.get_section(config.config_ini_section),
    #     prefix='sqlalchemy.',
    #     poolclass=pool.NullPool)

    # Updated for Alembic 1.17.0 compatibility with SQLAlchemy 2.0
    # Use connectable.begin() instead of connect() + begin_transaction()
    with connectable.begin() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
