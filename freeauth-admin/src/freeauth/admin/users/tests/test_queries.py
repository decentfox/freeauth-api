from __future__ import annotations

from typing import Optional

import edgedb
import pytest

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreateUserResult,
    create_user,
    delete_user,
    get_user_by_id,
    update_user,
)


@pytest.fixture
async def user(edgedb_client: edgedb.AsyncIOClient) -> CreateUserResult:
    user: CreateUserResult = await create_user(
        edgedb_client,
        name="张三",
        username="user",
        email="user@example.com",
        mobile="13800000000",
        hashed_password="password",
        organization_ids=None,
        org_type_id=None,
        reset_pwd_on_first_login=False,
    )
    return user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,username,email,mobile,hashed_password",
    [
        ("张三", "user", None, None, "password"),
        ("张三", "user", "user@example.com", None, "password"),
        ("张三", "user", "user@example.com", "13800000000", "password"),
    ],
)
async def test_create_user(
    edgedb_client: edgedb.AsyncIOClient,
    name: str,
    username: str,
    email: str | None,
    mobile: str | None,
    hashed_password: str,
):
    user: CreateUserResult = await create_user(
        edgedb_client,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
        hashed_password=hashed_password,
        organization_ids=None,
        org_type_id=None,
        reset_pwd_on_first_login=False,
    )
    assert user.id is not None
    assert user.name == name, user.username == username
    assert user.email == email, user.mobile == mobile
    assert user.created_at is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "new_username,new_email,new_mobile,field",
    [
        ("user", "user1@example.com", "13800000001", "username"),
        ("user1", "user@example.com", "13800000001", "email"),
        ("user1", "user1@example.com", "13800000000", "mobile"),
    ],
)
async def test_create_user_existing(
    edgedb_client: edgedb.AsyncIOClient,
    user: CreateUserResult,
    new_username: str,
    new_email: str,
    new_mobile: str,
    field,
):
    with pytest.raises(edgedb.errors.ConstraintViolationError) as e:
        await create_user(
            edgedb_client,
            name="张三",
            username=new_username,
            email=new_email,
            mobile=new_mobile,
            hashed_password="password",
            organization_ids=None,
            org_type_id=None,
            reset_pwd_on_first_login=False,
        )

    assert f"{field} violates exclusivity constraint" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,username,email,mobile",
    [
        ("张三", "user1", None, None),
        ("张三", "user1", "user1@example.com", None),
        (
            "张三",
            "user1",
            "user1@example.com",
            "13800000001",
        ),
        (
            "张三",
            "user1",
            "user1@example.com",
            "13800000001",
        ),
    ],
)
async def test_update_user(
    edgedb_client: edgedb.AsyncIOClient,
    user: CreateUserResult,
    name: str,
    username: str,
    email: str | None,
    mobile: str | None,
):
    updated_user: Optional[CreateUserResult] = await update_user(
        edgedb_client,
        name=name,
        username=username,
        email=email,
        mobile=mobile,
        id=user.id,
    )
    assert updated_user is not None
    assert updated_user.id == user.id
    assert updated_user.username == username != user.username
    assert updated_user.email == email != user.email


@pytest.mark.asyncio
async def test_delete_user(
    edgedb_client: edgedb.AsyncIOClient,
    user: CreateUserResult,
):
    await delete_user(edgedb_client, user_ids=[user.id])
    deleted_user = await get_user_by_id(edgedb_client, id=user.id)
    assert deleted_user is None
