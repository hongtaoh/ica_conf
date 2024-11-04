from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os 
import pandas as pd 

load_dotenv()
uri = os.getenv("MONGODB_URI")

client = MongoClient(uri, server_api=ServerApi('1'))

print(client.list_database_names())

db = client.ica_conf

print(db.list_collection_names())

papers_collection = db['papers']
authors_collection = db['authors']
sessions_collection = db['sessions']
embeddings_collection = db['embeddings']

PAPERS_JSON = '../data/api/papers.json'
AUTHORS_JSON = '../data/api/authors.json'
SESSIONS_JSON = '../data/api/sessions.json'
EMBEDDINGS_JSON = '../data/api/paper_embeddings.json'

if __name__ == "__main__":

    papers_collection.drop()
    print('papers collection deleted')

    authors_collection.drop()
    print('authors collection deleted')

    sessions_collection.drop()
    print('sessions collection deleted')

    embeddings_collection.drop()
    print('embeddings collection deleted')

    # Load JSON files into DataFrames, convert to records 
    # (list of dictionaries), and insert
    papers_data = pd.read_json(PAPERS_JSON).to_dict(orient='records')
    authors_data = pd.read_json(AUTHORS_JSON).to_dict(orient='records')
    sessions_data = pd.read_json(SESSIONS_JSON).to_dict(orient='records')
    embeddings_data = pd.read_json(EMBEDDINGS_JSON).to_dict(orient='records')

    papers_collection.insert_many(papers_data)
    print('papers collection created')

    authors_collection.insert_many(authors_data)
    print('authors collection created')

    sessions_collection.insert_many(sessions_data)
    print('sessions collection created')

    embeddings_collection.insert_many(embeddings_data)
    print('embeddings collection created')
