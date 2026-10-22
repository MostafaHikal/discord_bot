from fastapi import FastAPI
from routes import base, interactions

app = FastAPI()

app.include_router(base.base_router)
app.include_router(interactions.interactions_router)