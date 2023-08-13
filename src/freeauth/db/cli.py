# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan
# PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from __future__ import annotations

import os
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

settings = get_settings()
client = edgedb.create_client(
    dsn=settings.edgedb_dsn or settings.edgedb_instance,
    database=settings.edgedb_database,
)


def find_edgedb_project_dir():
    dir_ = os.getcwd()
    dev = os.stat(dir_).st_dev

    while True:
        toml = os.path.join(dir_, "edgedb.toml")
        if not os.path.isfile(toml):
            parent = os.path.dirname(dir_)
            if parent == dir_:
                break
            parent_dev = os.stat(parent).st_dev
            if parent_dev != dev:
                break
            dir_ = parent
            dev = parent_dev
            continue
        return dir_
    print("no `edgedb.toml` found")


@app.command()
def sync():
    """
    Synchronizing FreeAuth dbschema
    """
    dir_ = find_edgedb_project_dir()
    if not dir_:
        return

    target_dir = None
    for file_or_dir in Path(dir_).iterdir():
        if not file_or_dir.exists():
            continue
        if file_or_dir.is_dir() and file_or_dir.name == "dbschema":
            target_dir = file_or_dir
            break
    if not target_dir:
        print("no `dbschema` folder found")
        return

    source_dir = Path(__file__).resolve().parent / "dbschema"
    for file_or_dir in source_dir.iterdir():
        if not file_or_dir.suffix.lower() == ".esdl":
            continue
        target_file = Path(target_dir) / f"freeauth_{file_or_dir.name}"
        if target_file.exists():
            continue
        subprocess.call(("ln", file_or_dir, target_file))


@app.command()
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
            users: { id, name, username, is_deleted }
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
                users: { id, name, username, is_deleted }
            };\
            """,
            id=current_role.id,
        )
    print("[green][OK][/green] [cyan]角色[/cyan]配置成功!\n")
    print("角色信息：")
    table = Table("角色名称", "角色代码")
    table.add_row(current_role.name, current_role.code)
    print(table)

    print("\n3. 正在查询系统管理员账号...\n")
    if current_role.users:
        print("已为您找到以下系统管理员账号：\n")
        table = Table("用户名", "姓名", "状态")
        for user in current_role.users:
            table.add_row(
                user.username,
                user.name,
                "已停用" if user.is_deleted else "正常",
            )
        print(table)
    else:
        print("首次配置，尚未创建系统管理员账号\n")

    confirm = not bool(current_role.users)
    if not confirm:
        confirm = typer.confirm("需要继续创建管理员账号吗？")
    if confirm:
        print("\n4. 正在创建系统管理员账号...\n")
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
