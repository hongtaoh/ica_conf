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

PAPERS_JSON = '../data/processed/papers.json'
AUTHORS_JSON = '../data/processed/authors.json'
SESSIONS_JSON = '../data/processed/sessions.json'

if __name__ == "__main__":

    papers_collection.drop()
    print('papers collection deleted')

    authors_collection.drop()
    print('authors collection deleted')

    sessions_collection.drop()
    print('sessions collection deleted')

    # Load JSON files into DataFrames, convert to records 
    # (list of dictionaries), and insert
    papers_data = pd.read_json(PAPERS_JSON).to_dict(orient='records')
    authors_data = pd.read_json(AUTHORS_JSON).to_dict(orient='records')
    sessions_data = pd.read_json(SESSIONS_JSON).to_dict(orient='records')

    papers_collection.insert_many(papers_data)
    print('papers collection created')

    authors_collection.insert_many(authors_data)
    print('authors collection created')

    sessions_collection.insert_many(sessions_data)
    print('sessions collection created')