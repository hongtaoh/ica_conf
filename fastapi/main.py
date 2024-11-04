from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Path, HTTPException
import logging
from typing import List, Optional
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json 

from sklearn.preprocessing import normalize
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

load_dotenv()
uri = os.getenv("MONGODB_URI")
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.ica_conf
    papers_collection = db['papers']
    authors_collection = db['authors']
    sessions_collection = db['sessions']
    embeddings_collection = db['embeddings']
except Exception as e:
    print("Error connecting to MongoDB:", e)
    raise 


# Load the embeddings directly from MongoDB
print("Loading embeddings from MongoDB...")
embedding_docs = list(embeddings_collection.find({}, {"_id": 0, "paper_id": 1, "embedding": 1}))
paper_embeddings = {doc["paper_id"]: doc["embedding"] for doc in embedding_docs}
print("Loading embeddings finished!")

# Convert embeddings to NumPy array for FAISS
embeddings = np.array(list(paper_embeddings.values()), dtype=np.float32)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Load the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load the pre-trained PCA model
with open("pca_model.pkl", "rb") as f:
    pca = pickle.load(f)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",          
        "https://ica-conf.onrender.com",  
        "https://icaconf.vercel.app",
        "https://ica-conference-app-hongtaohs-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a response model for type-checking and documentation
class Authorship(BaseModel):
    position: Optional[int] = None
    author_name: Optional[str] = None
    author_affiliation: Optional[str] = None

class SessionInfo(BaseModel):
    session: str
    session_type: Optional[str] = None
    chair_name: Optional[str] = None
    chair_affiliation: Optional[str] = None
    division: Optional[str] = None
    years: List[int] = []
    paper_count: Optional[int] = None
    session_id: Optional[str] = None

class Paper(BaseModel):
    paper_id: str
    title: str
    paper_type: str
    abstract: Optional[str] = None
    number_of_authors: int
    year: int
    session: Optional[str] = None
    division: Optional[str] = None
    authorships: Optional[List[Authorship]] = None
    author_names: Optional[List[str]] = None
    session_info: Optional[SessionInfo] = None 

class Author(BaseModel):
    author_name: str
    attend_count: int
    paper_count: int
    paper_ids: Optional[List[str]] = None
    affiliations: Optional[List[str]] = None
    affiliation_history: Optional[str] = None
    years_attended: Optional[List[int]] = None

class Session(BaseModel):
    session: str
    session_type: Optional[str] = None
    chair_name: Optional[str] = None
    chair_affiliation: Optional[str] = None
    division: Optional[str] = None
    years: Optional[List[int]] = []
    paper_count: Optional[int] = None
    session_id: str

@app.get("/")
async def root():
    return {"message": "Welcome to ICA Conf Data"}

def get_query_embedding(query):
    query_embedding = model.encode(query).reshape(1, -1)
    query_embedding = pca.transform(query_embedding) 
    query_embedding = normalize(query_embedding, norm='l2')
    return query_embedding

@app.get("/search")
async def search_papers(query: str, k: int = 5):
    try:
        # Encode the query and search for similar embeddings
        query_embedding = get_query_embedding(query)
        distances, indices = index.search(query_embedding.reshape(1, -1), k)
        
        # Retrieve the top k paper IDs from MongoDB
        top_k_paper_ids = [list(paper_embeddings.keys())[i] for i in indices[0]]
        
        # Fetch paper details from MongoDB
        papers = list(papers_collection.find({"paper_id": {"$in": top_k_paper_ids}}, {"_id": 0}))
        return papers

    except Exception as e:
        print(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/papers", response_model=List[Paper])
async def get_papers(
    page: int = Query(1, description="Page number"),
    limit: int = Query(100, description="Number of items per page"),
    paper_id: Optional[str] = Query(None, description="Unique ID assigned to the paper"),
    title_contains: Optional[str] = Query(None, description="Keyword to search in the paper title"),
    paper_type: Optional[str] = Query(None, description="Type of presentation, either Paper or Poster"),
    abstract_contains: Optional[str] = Query(None, description="Keyword to search in the paper abstract"),
    number_of_authors: Optional[int] = Query(None, alias='number_of_authors', description="Number of authors"),
    session_contains: Optional[str] = Query(None, description="Keyword to search in the session"),
    year: Optional[int] = Query(None),
    session: Optional[str] = Query(None, description="Session title"),
    division: Optional[str] = Query(None, description="Division or Unit that organizes the paper"),
    has_author: Optional[str] = Query(None, description="Author Name appears in this paper"),
    first_author: Optional[str] = Query(None, description="First author of the paper"),
    last_author: Optional[str] = Query(None, description="Last author of the paper"),
    session_id: Optional[str] = Query(None, description='Session id exact match')
):
    query = {
        "year": year,
        "paper_type": paper_type,
        "session": session,
        "number_of_authors": number_of_authors,
        "division": division,
        "paper_id": paper_id,
    }
    query = {k: v for k, v in query.items() if v is not None}

    if title_contains:
        query['title'] = {"$regex": title_contains, "$options":"i"}
    if abstract_contains:
        query['abstract'] = {"$regex": abstract_contains, "$options": "i"}
    if session_contains:
        query['session'] = {"$regex": session_contains, "$options": "i"}
    if session_id:
        query['session_info.session_id'] = session_id
    if has_author:
        query["authorships.author_name"] = {"$regex": has_author, "$options": "i"}
    if first_author:
        query["authorships.0.author_name"] = {"$regex": first_author, "$options": "i"}  # First author
    elif last_author:
        query["authorships.-1.author_name"] = {"$regex": last_author, "$options": "i"}  # Last author
    # Pagination
    skip = (page - 1) * limit
    papers = list(
        papers_collection.find(query, {"_id": 0})
        .sort("year", -1)  # Sort by year in descending order
        .skip(skip)
        .limit(limit)
    )
    return papers

@app.get("/papers/{paper_id}")
async def get_paper_by_id(paper_id: str):
    paper = papers_collection.find_one({'paper_id': paper_id}, {'_id':0})
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.get("/sample_papers", response_model=List[Paper])
async def get_sample_papers(
    limit: int = Query(100, description="Number of random sample papers"),
    sort_by: Optional[str] = "year", 
    order: Optional[int] = -1
):
    sample_papers = list(papers_collection.aggregate([
        {'$sample': {"size":limit}},
        {'$sort': {sort_by: order}},  
        {'$project': {"_id": 0}}
    ]))
    # for paper in sample_papers:
    #     paper.pop("_id", None)
    return sample_papers

@app.get("/authors", response_model=List[Author])
async def get_authors(
    page: int = Query(1, description="Page number"),
    limit: int = Query(50, description="Number of items per page"),
    author_name: Optional[str] = Query(None, description="Exact name of the author"),
    min_attend_count: Optional[int] = Query(None, description="Minimum number of times the author attended"),
    min_paper_count: Optional[int] = Query(None, description="Minimum number of papers the author has"),
    affiliation_contains: Optional[str] = Query(None, description="Keyword to search in affiliations"),
    year_attended: Optional[int] = Query(None, description="Specific year the author attended")
):
    # Build the query dictionary
    query = {}
    
    if author_name:
        query["author_name"] = author_name  # Exact match on author name
    if min_attend_count is not None:
        query["attend_count"] = {"$gte": min_attend_count}
    if min_paper_count is not None:
        query["paper_count"] = {"$gte": min_paper_count}
    if affiliation_contains:
        query["affiliations"] = {"$regex": affiliation_contains, "$options": "i"}
    if year_attended:
        query["years_attended"] = year_attended  # Checks if the year is in the list of years attended
    
    # Pagination
    skip = (page - 1) * limit
    authors = list(authors_collection.find(query, {"_id": 0}).skip(skip).limit(limit))
    if not authors:
        return []
    return authors

@app.get("/sample_authors", response_model=List[Author])
async def get_sample_authors(
    limit: int = Query(100, description="Number of random sample authors"),
    sort_by: Optional[str] = "attend_count", 
    order: Optional[int] = -1
):
    sample_authors = list(authors_collection.aggregate([
        {'$sample': {"size": limit}},
        {'$sort': {sort_by: order}},  
        {'$project': {"_id": 0}}
    ]))
    return sample_authors

@app.get("/sessions", response_model=List[Session])
async def get_sessions(
    page: int = Query(1, description="Page number"),
    limit: int = Query(50, description="Number of items per page"),
    session: Optional[str] = Query(None, description="Exact session name"),
    session_type: Optional[str] = Query(None, description="Type of the session (e.g., Paper Session)"),
    chair_name: Optional[str] = Query(None, description="Name of the session chair"),
    chair_affiliation: Optional[str] = Query(None, description="Affiliation of the session chair"),
    division: Optional[str] = Query(None, description="Division or unit organizing the session"),
    year: Optional[int] = Query(None, description="Specific year the session was held"),
    paper_count: Optional[int] = Query(None, description="Number of papers in the session")
):
    # Build the MongoDB query
    query = {}
    
    if session:
        query["session"] = session  # Exact match on session name
    if session_type:
        query["session_type"] = session_type  # Exact match on session type
    if chair_name:
        query["chair_name"] = chair_name  # Exact match on chair name
    if chair_affiliation:
        query["chair_affiliation"] = chair_affiliation  # Exact match on chair affiliation
    if division:
        query["division"] = division  # Exact match on division
    if year:
        query["years"] = year  # Matches a specific year in the years array
    if paper_count is not None:
        query["paper_count"] = paper_count  # Exact match on paper count

    # Retrieve and filter sessions from MongoDB
    skip = (page - 1) * limit
    sessions = list(sessions_collection.find(query, {"_id": 0}).skip(skip).limit(limit))
    if not sessions:
        return []
    return sessions

@app.get("/sample_sessions", response_model=List[Session])
async def get_sample_sessions(
    limit: int = Query(10, description="Number of random sample sessions"),
    sort_by: Optional[str] = "paper_count", 
    order: Optional[int] = -1
):
    try:
        sample_sessions = list(sessions_collection.aggregate([
            {'$sample': {"size":limit}},
            {'$sort': {sort_by: order}},  
            {'$project': {"_id": 0}}
        ]))
        return sample_sessions
    except Exception as e:
        # Log the exception for further analysis
        logging.error(f"Error fetching sample sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
