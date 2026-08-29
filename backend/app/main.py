from fastapi import FastAPI
from routes.migrations import router as migrations_router

app = FastAPI()


app.include_router(migrations_router)
