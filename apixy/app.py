"""The app's entrypoint"""

from fastapi import FastAPI

from .api.v1.api import router

app = FastAPI(title="Apixy")
app.include_router(router)
