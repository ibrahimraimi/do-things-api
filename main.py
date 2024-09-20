import os

import databases
import sqlalchemy

from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

load_dotenv(".env")

DATABASE_URL: str = os.getenv("DATABASE_URL")

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://do-things.vercel.app",
    "https://main--do-thing.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Project(BaseModel):
    name: str
    url: str


class Developer(BaseModel):
    id: int
    name: str
    photoUrl: str
    twitterUrl: str
    projects: list[Project]


database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

developers = sqlalchemy.Table(
    "developers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("photoUrl", sqlalchemy.String),
    sqlalchemy.Column("twitterUrl", sqlalchemy.String),
    sqlalchemy.Column("projects", sqlalchemy.JSON),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/api/v1/developers")
async def read_developers():
    query = developers.select()
    return await database.fetch_all(query)


@app.get("/api/v1/developers/{developer_id}")
async def read_developer(developer_id: int):
    query = developers.select().where(developers.c.id == developer_id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Developer not found")
    return result


@app.post("/api/v1/developers")
async def create_developer(developer: Developer):
    query = developers.insert().values(
        name=developer.name,
        photoUrl=developer.photoUrl,
        twitterUrl=developer.twitterUrl,
        projects=[project.dict() for project in developer.projects]
    )
    last_record_id = await database.execute(query)
    return {**developer.dict(), "id": last_record_id}


@app.put("/api/v1/developers/{developer_id}")
async def update_developer(developer_id: int, developer: Developer):
    query = developers.update().where(developers.c.id == developer_id).values(
        name=developer.name,
        photoUrl=developer.photoUrl,
        twitterUrl=developer.twitterUrl,
        projects=[project.dict() for project in developer.projects]
    )
    await database.execute(query)
    return {**developer.dict(), "id": developer_id}


@app.delete("/api/v1/developers/{developer_id}")
async def delete_developer(developer_id: int):
    query = developers.delete().where(developers.c.id == developer_id)
    await database.execute(query)
    return {"message": "Developer deleted successfully"}
