# AUTOGENERATED FROM 'app/queries/create_director.edgeql' WITH:
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
class CreateDirectorResult(NoPydanticValidation):
    id: uuid.UUID
    name: str


async def create_director(
    executor: edgedb.AsyncIOExecutor,
    *,
    name: str,
) -> CreateDirectorResult:
    return await executor.query_single(
        """\
        select (
            insert Person {
                name := <str>$name
            }
        ) {name};\
        """,
        name=name,
    )
