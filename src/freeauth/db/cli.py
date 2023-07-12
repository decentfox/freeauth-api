from __future__ import annotations

import string
import subprocess
from pathlib import Path

import edgedb
import typer
from dotenv import set_key
from rich import print
from rich.table import Table

from freeauth.conf.settings import get_settings
from freeauth.security.utils import gen_random_string, get_password_hash

from .admin import admin_qry_edgeql

app = typer.Typer(help="FreeAuth CLI")

migration_app = typer.Typer(
    name="migration", help="FreeAuth db migration manager."
)
app.add_typer(migration_app)

admin_app = typer.Typer(name="admin", help="FreeAuth admin CLI manager.")
app.add_typer(admin_app)

settings = get_settings()
client = edgedb.create_client(
    dsn=settings.edgedb_dsn or settings.edgedb_instance,
    database=settings.edgedb_database,
)


@app.command()
def install():
    """
    Initialize FreeAuth EdgeDB project (override EDGEDB_INSTANCE in .env
    file or environment variable).
    """
    subprocess.call(
        (
            "edgedb",
            "project",
            "init",
            "--project-dir",
            Path(__file__).resolve().parent,
            "--server-instance",
            settings.edgedb_instance,
        )
    )


def handle_migration_command(command):
    schema_dir = Path(__file__).resolve().parent / "dbschema"
    subprocess.call(
        (
            "edgedb",
            "migration",
            command,
            "--schema-dir",
            schema_dir,
            "--dsn" if settings.edgedb_dsn else "--instance",
            settings.edgedb_dsn or settings.edgedb_instance,
            "--database",
            settings.edgedb_database,
        )
    )


@migration_app.command(name="create")
def create_migration():
    """
    Create a migration script.
    """
    handle_migration_command("create")


@migration_app.command(name="apply")
def apply_migration():
    """
    Bring current database to the latest or a specified revision.
    """
    handle_migration_command("apply")


@admin_app.command()
def setup():
    """
    Setting up administrator account.
    """
    db = client.with_default_module("freeauth")
    print("1. 正在配置应用...\n")
    current_app = None
    if settings.freeauth_app_id:
        current_app = db.query_single(
            """\
            select Application { id, name }
            filter .id = <uuid>$id;\
            """,
            id=settings.freeauth_app_id,
        )
    if not current_app:
        current_app = db.query_single("""\
            select assert_single((
                select Application { id, name }
                filter .is_protected
            ));\
            """)
        if not current_app:
            secret = gen_random_string(32, secret=True)
            current_app = admin_qry_edgeql.create_application(
                db,
                name="FreeAuth",
                description="FreeAuth 后台管理应用",
                hashed_secret=get_password_hash(secret),
            )
            db.query(
                """\
                update Application
                filter .id = <uuid>$id set {
                    is_protected := true
                };\
            """,
                id=current_app.id,
            )
    set_key(settings.Config.env_file, "freeauth_app_id", str(current_app.id))
    scoped_db = db.with_globals(current_app_id=current_app.id)
    print("[green][OK][/green] [cyan]应用[/cyan]配置成功!\n")
    print("应用信息：")
    table = Table("应用ID", "应用名称")
    table.add_row(str(current_app.id), current_app.name)
    print(table)

    print("\n2. 正在配置系统管理员角色...\n")
    current_role = scoped_db.query_single("""\
        select Role {
            id,
            name,
            code,
            users: { id, username }
        } filter (
            select Permission
            filter .application = global current_app
            and .code = '*'
        ) in .permissions
        limit 1;\
        """)
    if not current_role:
        role_code = "ADMINISTRATOR"
        while True:
            try:
                current_role = admin_qry_edgeql.create_role(
                    scoped_db,
                    name="系统管理员",
                    code=role_code.upper(),
                    description="该角色拥有应用程序中的最高权限，可以执行任何操作、访问所有功能",
                )
            except edgedb.errors.ConstraintViolationError:
                random_str = gen_random_string(5, letters=string.digits)
                role_code = f"ADMINISTRATOR_{random_str}"
            else:
                break
        current_role = scoped_db.query_single(
            """\
            select (
                update Role filter .id = <uuid>$id set {
                    permissions += (
                        select Permission
                        filter .application = global current_app
                        and .code = '*'
                    )
                }
            ) {
                id,
                name,
                code,
                users: { id, username }
            };\
            """,
            id=current_role.id,
        )
    print("[green][OK][/green] [cyan]角色[/cyan]配置成功!\n")
    print("角色信息：")
    table = Table("角色名称", "角色代码")
    table.add_row(current_role.name, current_role.code)
    print(table)

    print("\n3. 正在创建系统管理员账号...\n")
    username = gen_random_string(6, letters=string.ascii_lowercase)
    password = gen_random_string(12, secret=True)
    while True:
        try:
            user = admin_qry_edgeql.create_user(
                scoped_db,
                name=f"{current_app.name}管理员",
                username=username,
                hashed_password=get_password_hash(password),
                reset_pwd_on_first_login=True,
            )
        except edgedb.errors.ConstraintViolationError:
            username = gen_random_string(6, letters=string.ascii_lowercase)
        else:
            break
    admin_qry_edgeql.role_bind_users(
        scoped_db, user_ids=[user.id], role_ids=[current_role.id]
    )
    print("[green][OK][/green] [cyan]管理员账号[/cyan]创建成功!\n")
    print("登录信息：")
    table = Table("用户名", "密码")
    table.add_row(user.username, password)
    print(table)


if __name__ == "__main__":
    app()
