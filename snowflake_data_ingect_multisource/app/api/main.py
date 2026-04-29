from fastapi import FastAPI
from app.api.routes import sources,pipelines
app=FastAPI(title='OI Atlas Snowflake Generator')
app.include_router(sources.router,prefix='/sources')
app.include_router(pipelines.router,prefix='/pipelines')
