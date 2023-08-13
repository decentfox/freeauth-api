# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from __future__ import annotations

from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException
from pydantic import BaseModel

from .asgi import auth_app, get_edgedb_client, router
from .queries.create_director_async_edgeql import (
    CreateDirectorResult,
    create_director,
)
from .queries.create_movie_async_edgeql import CreateMovieResult, create_movie


class MovieRequestData(BaseModel):
    title: str
    director: str


@router.post(
    "/movies",
    dependencies=[Depends(auth_app.perm_accepted("create:movies"))],
)
async def post_movie(
    body: MovieRequestData,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateMovieResult:
    try:
        movie = await create_movie(
            client,
            title=body.title,
            director_name=body.director,
        )
    except edgedb.errors.MissingRequiredError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Director not found"
        )
    return movie


class DirectorRequestData(BaseModel):
    name: str


@router.post(
    "/directors",
    dependencies=[Depends(auth_app.perm_accepted("create:directors"))],
)
async def post_director(
    body: DirectorRequestData,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateDirectorResult:
    return await create_director(
        client,
        name=body.name,
    )
