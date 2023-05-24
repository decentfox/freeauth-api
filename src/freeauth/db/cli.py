from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from freeauth.conf.settings import get_settings

settings = get_settings()

parser = argparse.ArgumentParser(prog="FreeAuth")
subparsers = parser.add_subparsers(title="subcommands", dest="command")
subparsers.add_parser(
    "install",
    help=(
        "Initialize FreeAuth EdgeDB project (override EDGEDB_INSTANCE in .env"
        " file or environment variable)"
    ),
)
migration_parser = subparsers.add_parser(
    "migration",
    help="Migration management subcommands",
)
migration_subparsers = migration_parser.add_subparsers(
    title="subcommands", dest="subcommands"
)
migration_subparsers.add_parser(
    "apply",
    help="Bring current database to the latest or a specified revision",
)
migration_subparsers.add_parser("create", help="Create a migration script")
subparsers.add_parser("dump", help="Create a database backup")
subparsers.add_parser("restore", help="Restore a database backup from file")


def main():
    args = parser.parse_args()
    if not args.command:
        parser.print_help()

    instance = settings.edgedb_instance
    database = settings.edgedb_database

    if args.command == "install":
        subprocess.call(
            (
                "edgedb",
                "project",
                "init",
                "--project-dir",
                Path(__file__).resolve().parent,
                "--server-instance",
                instance,
            )
        )
    if args.command == "migration":
        schema_dir = Path(__file__).resolve().parent / "dbschema"
        subprocess.call(
            (
                "edgedb",
                "migration",
                args.subcommands,
                "--schema-dir",
                schema_dir,
                "--instance",
                instance,
                "--database",
                database,
            )
        )
    if args.command in ("dump", "restore"):
        subprocess.call(
            (
                "edgedb",
                args.command,
                "--instance",
                instance,
                "--database",
                database,
            )
        )


if __name__ == "__main__":
    main()
