from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

print(client.list_database_names())

db = client.ica_conf

print(db.list_collection_names())

papers_collection = db['papers']
authors_collection = db['authors']
sessions_collection = db['sessions']

from fastapi import FastAPI, Query
from typing import List, Optional

app = FastAPI()

@app.get("/papers", response_model=List[dict])
async def get_papers(
    year: Optional[int] = Query(None),
    paper_type: Optional[str] = Query(None, description="Type of presentation, either Paper or Poster"),
    session: Optional[str] = Query(None, description="Session title"),
    num_authors: Optional[int] = Query(None, alias='number_of_authors', description="Number of authors"),
    division: Optional[str] = Query(None, description="Division or Unit that organizes the paper"),
    paper_id: Optional[str] = Query(None, description="Unique ID assigned to the paper"),
    title_contains: Optional[str] = Query(None, description="Keyword to search in the paper title"),
    abstract_contains: Optional[str] = Query(None, description="Keyword to search in the paper abstract")
):
    query = {}
    if year is not None:
        query['Year'] = year
    if paper_type:
        query['Paper Type'] = paper_type
    if session:
        query['Session'] = session
    if num_authors is not None:
        query['Number of Authors'] = num_authors
    if division:
        query['Division/Unit'] = division 
    if paper_id:
        query['Paper ID'] = paper_id 
    if title_contains:
        query['Title'] = {"$regex": title_contains, "$options":"i"}
    if abstract_contains:
        query['Abstract'] = {"$regex": abstract_contains, "$options": "i"}
    papers = list(papers_collection.find(query, {"_id":0}))
    return papers

@app.get("/papers/{paper_id}")
async def get_paper_by_id(paper_id:str):
    return papers_collection.find_one({'Paper ID': paper_id}, {'_id':0})