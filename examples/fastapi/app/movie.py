from __future__ import annotations

from pydantic import BaseModel

from fastapi import Depends

from .asgi import auth_app, router
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
) -> CreateMovieResult:
    return await create_movie(
        auth_app.db,
        title=body.title,
        director_name=body.director,
    )


class DirectorRequestData(BaseModel):
    name: str


@router.post(
    "/directors",
    dependencies=[Depends(auth_app.perm_accepted("create:directors"))],
)
async def post_director(
    body: DirectorRequestData,
) -> CreateDirectorResult:
    return await create_director(
        auth_app.db,
        name=body.name,
    )
