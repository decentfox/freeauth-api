# AUTOGENERATED FROM 'app/queries/create_movie.edgeql' WITH:
#     $ edgedb-py --dir app


from __future__ import annotations
import dataclasses
import edgedb
import uuid


class NoPydanticValidation:
    @classmethod
    def __get_validators__(cls):
        from pydantic.dataclasses import dataclass as pydantic_dataclass
        pydantic_dataclass(cls)
        cls.__pydantic_model__.__get_validators__ = lambda: []
        return []


@dataclasses.dataclass
class CreateMovieResult(NoPydanticValidation):
    id: uuid.UUID
    title: str
    director: CreateMovieResultDirector


@dataclasses.dataclass
class CreateMovieResultDirector(NoPydanticValidation):
    id: uuid.UUID
    name: str


async def create_movie(
    executor: edgedb.AsyncIOExecutor,
    *,
    title: str,
    director_name: str,
) -> CreateMovieResult:
    return await executor.query_single(
        """\
        select (
            insert Movie {
                title := <str>$title,
                director := assert_single((
                    select Person
                    filter .name = <str>$director_name
                ))
            }
        ) {title, director: {name}};\
        """,
        title=title,
        director_name=director_name,
    )