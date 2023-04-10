from fastapi import FastAPI


def get_app():
    app = FastAPI(
        title="FreeAuth", description="Async REST API in Python for FreeAuth."
    )

    return app
