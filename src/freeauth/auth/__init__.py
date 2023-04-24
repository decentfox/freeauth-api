from fastapi import APIRouter

router = APIRouter(tags=["认证相关"])


def get_router():
    from . import sign_in  # noqa
    from . import sign_up  # noqa

    return router
