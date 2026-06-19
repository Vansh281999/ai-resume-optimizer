from __future__ import annotations
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from alembic import context
from sqlalchemy import engine_from_config, pool

_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=str(_env_path) if _env_path.exists() else ".env", override=True)

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

config = context.config

if os.getenv("DATABASE_URL"):
    url = os.getenv("DATABASE_URL")
    cfg_path = Path(__file__).resolve().parent / "alembic.ini"
    text = cfg_path.read_text()
    text = text.replace("sqlalchemy.url = sqlite:///./career_platform.db", f"sqlalchemy.url = {url}")
    cfg_path.write_text(text)

target_metadata = None


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.StaticPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()