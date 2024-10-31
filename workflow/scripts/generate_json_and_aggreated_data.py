# generate paeprs.json and aggreated author and session data
import pandas as pd
import numpy as np
import sys
import json 

PAPERS_DF = sys.argv[1]
AUTHORS_DF = sys.argv[2]
SESSIONS_DF = sys.argv[3]
PAPERS_JSON = sys.argv[4]
AUTHORS_JSON = sys.argv[5]
SESSIONS_JSON = sys.argv[6]

def process_papers_df(PAPERS_DF):
    papers = pd.read_csv(PAPERS_DF)
    papers.columns = ['paper_id', 'title', 'paper_type', 'abstract', 
                    'number_of_authors', 'year', 'session', 'division', 'authors']
    papers.drop(['authors'], inplace=True, axis = 1)
    return papers 

def get_authorships_dic_and_paperid_authors_dic(AUTHORS_DF):
    authors = pd.read_csv(AUTHORS_DF)
    # look like this:
    """
    [{'position': 0, 'author_name': 'Åsa Kroon', 'author_affiliation': 'Örebro U'},
    {'position': 1,
    'author_name': 'Mats Erik Ekstrom',
    'author_affiliation': 'Orebro U'}]
    """
    authorships_dic = {}
    # this is easy to understand. key is paper_id, value is list of authors
    paperid_authors_dic = {}
    # for every paper
    for paper_id, group in authors.groupby('Paper ID'):
        paperid_authors_dic[paper_id] = list(group['Author Name'])
        authorships = []
        author_names = group['Author Name'].tolist()
        affs = group['Author Affiliation'].tolist()
        for i, author_name in enumerate(author_names):
            dic = {}
            dic['position'] = i
            dic['author_name'] = author_name 
            dic['author_affiliation'] = affs[i]
            authorships.append(dic)
        authorships_dic[paper_id] = authorships
    return authorships_dic, paperid_authors_dic

def get_session_dic(SESSIONS_DF):
    """
    looks like this:

    {'session': 'Sports Communication Interactive Poster Session',
    'session_type': 'Interactive Paper Session',
    'chair_name': nan,
    'chair_affiliation': nan,
    'division': 'In Event: ICA Plenary Interactive Paper/Poster Session II'}
    """
    sessions = pd.read_csv(SESSIONS_DF)
    session_dic = {}
    for session, group in sessions.groupby('Session Title'):
        dic = {}
        dic['session'] = session
        dic['session_type'] = group['Session Type'].tolist()[0]
        dic['chair_name'] = group['Chair Name'].tolist()[0]
        dic['chair_affiliation'] = group['Chair Affiliation'].tolist()[0]
        dic['division'] = group['Division/Unit'].tolist()[0]
        session_dic[session] = dic 
    return session_dic

def update_papers_json(
        papers_json_raw, authorships_dic, paperid_authors_dic, session_dic):
    for paper_dic in papers_json_raw:
        try:
            paper_dic['authorships'] = authorships_dic[paper_dic['paper_id']]
        except:
            paper_dic['authorships'] = None
        try:
            paper_dic['author_names'] = paperid_authors_dic[paper_dic['paper_id']]
        except:
            paper_dic['author_names'] = None 
        try:
            paper_dic['session_info'] = session_dic[paper_dic['session']]
        except:
            paper_dic['session_info'] = None

def get_sessions_json(papers, session_dic):
    for session, group in papers.groupby('session'):
    # groupby excludes rows with nan values
        if session in session_dic:
            session_dic[session]['years'] = [int(year) for year in group['year'].unique()]
            session_dic[session]['paper_count'] = len(group)
        else:
            dic = {}
            dic['session'] = session
            dic['years'] = [int(year) for year in group['year'].unique()]
            dic['paper_count'] = len(group)
            dic['session_type'] = None 
            dic['chair_name'] = None 
            dic['chair_affiliation'] = None
            try:
                dic['division'] = group.division.unique()[0]
            except:
                dic['division'] = None
            session_dic[session] = dic
    sessions_json = list(session_dic.values())
    return sessions_json

def get_authors_json(AUTHORS_DF):
    authors = pd.read_csv(AUTHORS_DF)
    authors_json = []
    for author_name, group in authors.groupby('Author Name'):
        # sort by year to make sure affs are in temporal order 
        group = group.sort_values('Year', ascending=True)
        paper_ids = list(group['Paper ID'].unique())
        affs = group['Author Affiliation'].dropna().unique()
        years = [int(year) for year in group['Year'].unique()]
        dic = {
            'author_name': author_name,
            'attend_count': int(len(years)),
            'paper_count': int(len(paper_ids)),
            'paper_ids': paper_ids,
            'affiliation': " -> ".join(map(str, affs)),
            'years_attended': years,
        }
        authors_json.append(dic)
    # sort by attend_count, descending
    return sorted(authors_json, key=lambda x: x['attend_count'], reverse=True)

if __name__ == '__main__':
    papers = process_papers_df(PAPERS_DF)
    paper_ids = papers.paper_id.unique()
    papers_json_raw = json.loads(papers.to_json(orient='records'))
    authorships_dic, paperid_authors_dic = get_authorships_dic_and_paperid_authors_dic(
        AUTHORS_DF
    )
    session_dic = get_session_dic(SESSIONS_DF)
    update_papers_json(
        papers_json_raw, 
        authorships_dic, 
        paperid_authors_dic, 
        session_dic
    )
    sessions_json_raw = get_sessions_json(papers, session_dic)
    authors_json_raw = get_authors_json(AUTHORS_DF)

    with open(PAPERS_JSON, 'w') as f:
        json.dump(papers_json_raw, f, indent=2)
    with open(AUTHORS_JSON, 'w') as f:
        json.dump(authors_json_raw, f, indent=2)
    with open(SESSIONS_JSON, 'w') as f:
        json.dump(sessions_json_raw, f, indent=2)
    
    print('Files written. All should be in place now.')




