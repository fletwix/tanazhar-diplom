"""
Alembic environment configuration.

Reads settings from pydantic config and targets our Base metadata
so that ``alembic revision --autogenerate`` picks up all ORM models.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base

# Import all models so they are registered on Base.metadata
import app.models  # noqa: F401

# ── Alembic Config ──────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url from our pydantic-settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tables created by PostGIS extensions that we must NOT touch
EXCLUDE_TABLES = {
    "spatial_ref_sys",
    # Tiger geocoder tables
    "geocode_settings", "geocode_settings_default",
    "direction_lookup", "secondary_unit_lookup", "street_type_lookup",
    "state_lookup", "county_lookup", "countysub_lookup", "place_lookup",
    "zip_lookup", "zip_lookup_all", "zip_lookup_base",
    "zip_state", "zip_state_loc",
    "loader_lookuptables", "loader_platform", "loader_variables",
    "pagc_gaz", "pagc_lex", "pagc_rules",
    "faces", "edges", "addr", "addrfeat", "featnames",
    "county", "cousub", "state", "place", "bg",
    "tract", "tabblock", "tabblock20", "zcta5",
    "layer", "topology",
}


def include_object(obj, name, type_, reflected, compare_to):
    """Filter out PostGIS internal tables from autogenerate."""
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
