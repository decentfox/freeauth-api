from __future__ import annotations

from typing import Optional

import edgedb
import pytest

from freeauth.queries.query_api import (
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
        username="user",
        email="user@example.com",
        hashed_password="password",
    )
    return user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username,email,hashed_password",
    [
        ("user", None, None),
        ("user", "user@example.com", None),
        ("user", "user@example.com", "password"),
    ],
)
async def test_create_user(
    edgedb_client: edgedb.AsyncIOClient,
    username: str,
    email: str | None,
    hashed_password: str | None,
):
    user: CreateUserResult = await create_user(
        edgedb_client,
        username=username,
        email=email,
        hashed_password=hashed_password,
    )
    assert user.id is not None
    assert user.username == username
    assert user.email == email
    assert user.created_at is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "new_username,new_email,field",
    [
        ("user", "user1@example.com", "username"),
        ("user1", "user@example.com", "email"),
    ],
)
async def test_create_user_existing(
    edgedb_client: edgedb.AsyncIOClient,
    user: CreateUserResult,
    new_username: str,
    new_email: str,
    field,
):
    with pytest.raises(edgedb.errors.ConstraintViolationError) as e:
        await create_user(
            edgedb_client,
            username=new_username,
            email=new_email,
            hashed_password=None,
        )

    assert f"{field} violates exclusivity constraint" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username,email,hashed_password",
    [
        ("user1", None, None),
        ("user1", "user1@example.com", "password1"),
    ],
)
async def test_update_user(
    edgedb_client: edgedb.AsyncIOClient,
    user: CreateUserResult,
    username: str,
    email: str | None,
    hashed_password: str | None,
):
    updated_user: Optional[CreateUserResult] = await update_user(
        edgedb_client,
        username=username,
        email=email,
        hashed_password=hashed_password,
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
    await delete_user(edgedb_client, id=user.id)
    deleted_user = await get_user_by_id(edgedb_client, id=user.id)
    assert deleted_user is None
