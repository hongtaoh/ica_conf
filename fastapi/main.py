from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Path, HTTPException
from typing import List, Optional
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
uri = os.getenv("MONGODB_URI")
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.ica_conf
    papers_collection = db['papers']
    authors_collection = db['authors']
    sessions_collection = db['sessions']
except Exception as e:
    print("Error connecting to MongoDB:", e)
    raise 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to ICA Conf Data"}

@app.get("/papers", response_model=List[dict])
async def get_papers(
    year: Optional[int] = Query(None),
    paper_type: Optional[str] = Query(None, description="Type of presentation, either Paper or Poster"),
    session: Optional[str] = Query(None, description="Session title"),
    paper_title: Optional[str] = Query(None, description="Paper Title"),
    num_authors: Optional[int] = Query(None, alias='number_of_authors', description="Number of authors"),
    division: Optional[str] = Query(None, description="Division or Unit that organizes the paper"),
    paper_id: Optional[str] = Query(None, description="Unique ID assigned to the paper"),
    title_contains: Optional[str] = Query(None, description="Keyword to search in the paper title"),
    abstract_contains: Optional[str] = Query(None, description="Keyword to search in the paper abstract"),
    session_contains: Optional[str] = Query(None, description="Keyword to search in the session")
):
    query = {
        "Year": year,
        "Paper Type": paper_type,
        "Session": session,
        "Title": paper_title,
        "Number of Authors": num_authors,
        "Division/Unit": division,
        "Paper ID": paper_id,
    }
    query = {k: v for k, v in query.items() if v is not None}
    if title_contains:
        query['Title'] = {"$regex": title_contains, "$options":"i"}
    if abstract_contains:
        query['Abstract'] = {"$regex": abstract_contains, "$options": "i"}
    if session_contains:
        query['Session'] = {"$regex": session_contains, "$options": "i"}
    papers = list(papers_collection.find(query, {"_id":0}))
    return papers

@app.get("/papers/{paper_id}")
async def get_paper_by_id(paper_id: str):
    paper = papers_collection.find_one({'Paper ID': paper_id}, {'_id':0})
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.get("/sample_papers", response_model=List[dict])
async def get_sample_papers(
    limit: int = Query(100, description="Number of random sample papers")
):
    sample_papers = list(papers_collection.aggregate([
        {'$sample': {"size":limit}}
    ]))
    for paper in sample_papers:
        paper.pop("_id", None)
    return sample_papers

@app.get("/papers/{paper_id}/authors", response_model=List[dict])
async def get_authors_by_paper_id(
    paper_id: str = Path(..., description="Unique ID assigned to the paper"),
):
    query = {'Paper ID': paper_id}
    authors = list(authors_collection.find(query, {"_id":0}))
    return authors

@app.get("/authors", response_model=List[dict])
async def get_authors(
    paper_id: Optional[str] = Query(None, description="Unique ID assigned to the paper"),
    paper_title: Optional[str] = Query(None, description="Paper Title"),
    year: Optional[int] = Query(None),
    num_authors: Optional[int] = Query(None, alias='number_of_authors', description="Number of authors"),
    author_position: Optional[int] = Query(None, description="Position of the author"),
    author_name: Optional[str] = Query(None),
    author_affiliation: Optional[str] = Query(None),
    title_contains: Optional[str] = Query(None, description="Keyword to search in the paper title"),
):
    query = {
        "Year": year,
        "Number of Authors": num_authors,
        "Author Position": author_position,
        "Paper ID": paper_id,
        "Title": paper_title,
        "Author Name": author_name,
        "Author Affiliation": author_affiliation
    }
    query = {k: v for k, v in query.items() if v is not None}
    if title_contains:
        query['Title'] = {"$regex": title_contains, "$options":"i"}
    authors = list(authors_collection.find(query, {"_id":0}))
    return authors

@app.get("/sessions", response_model=List[dict])
async def get_sessions(
    year: Optional[int] = Query(None),
    session_type: Optional[str] = Query(None),
    session_title: Optional[str] = Query(None),
    division: Optional[str] = Query(None),
    chair_name: Optional[str] = Query(None),
    chair_affiliation: Optional[str] = Query(None),
):
    query = {
        "Year": year,
        "Session Type": session_type,
        "Session Title": session_title,
        "Division/Unit": division,
        "Chair Name": chair_name,
        "Chair Affiliation": chair_affiliation
    }
    query = {k: v for k, v in query.items() if v is not None}
    
    sessions = list(sessions_collection.find(query, {"_id":0}))
    return sessions
    
