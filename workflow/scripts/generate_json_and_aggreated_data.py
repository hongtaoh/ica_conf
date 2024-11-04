# generate paeprs.json and aggreated author and session data
import pandas as pd
import hashlib
import sys
import json 
from collections import defaultdict
from fuzzywuzzy import fuzz

PAPERS_DF = sys.argv[1]
AUTHORS_DF = sys.argv[2]
SESSIONS_DF = sys.argv[3]
PAPERS_JSON = sys.argv[4]
AUTHORS_JSON = sys.argv[5]
SESSIONS_JSON = sys.argv[6]
INDEXED_PAPERS_JSON = sys.argv[7]
SESSIONID_PAPERS_JSON = sys.argv[8]
AUTHOR_PAPER_IDS_JSON = sys.argv[9]

def process_papers_df(PAPERS_DF):
    papers = pd.read_csv(PAPERS_DF)
    papers = papers.where(pd.notnull(papers), None)
    column_mapping = {
        'Paper ID': 'paper_id',
        'Title': 'title',
        'Paper Type': 'paper_type',
        'Abstract': 'abstract',
        'Number of Authors': 'number_of_authors',
        'Year': 'year',
        'Session': 'session',
        'Division/Unit': 'division',
        'Authors': 'authors'
    }
    # Rename columns in the DataFrame using the dictionary
    papers.rename(columns=column_mapping, inplace=True)
    papers.number_of_authors = papers.number_of_authors.fillna(0).astype(int)
    papers.drop(['authors'], inplace=True, axis = 1)
    return papers 

def get_session_id_dic(papers, SESSIONS_DF):
    sessions = pd.read_csv(SESSIONS_DF)
    session_names = pd.Series(list(sessions['Session Title'].dropna()) + list(papers.session.dropna())).unique()
    session_ids = [hashlib.md5(name.encode()).hexdigest()[:12] for name in session_names]
    session_id_dic = dict(zip(session_names, session_ids))
    return session_id_dic

def get_authorships_dic_and_paperid_authors_dic(AUTHORS_DF):
    authors = pd.read_csv(AUTHORS_DF)
    authors = authors.where(pd.notnull(authors), None)
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
    sessions = sessions.where(pd.notnull(sessions), None)
    session_dic = {}
    for session, group in sessions.groupby('Session Title'):
        dic = {}
        dic['session'] = session
        dic['session_type'] = group['Session Type'].tolist()[0]
        dic['chair_name'] = group['Chair Name'].tolist()[0]
        dic['chair_affiliation'] = group['Chair Affiliation'].tolist()[0]
        dic['division'] = group['Division/Unit'].tolist()[0]

        # add what we eventually want
        dic['years'] = []
        dic['paper_count'] = 0
        session_dic[session] = dic 
    return session_dic

def update_papers_json(
        papers_json_raw, 
        authorships_dic, 
        paperid_authors_dic, 
        session_dic,
        session_id_dic
    ):
    for paper in papers_json_raw:
        paper['authorships'] = authorships_dic.get(paper['paper_id'], None)
        paper['author_names'] = paperid_authors_dic.get(paper['paper_id'], None)
        paper['session_info'] = session_dic.get(paper['session'], None)
        
        if paper.get('session') and paper['session_info']:
            paper['session_info']['session_id'] = session_id_dic.get(paper['session'], None)

def get_sessions_json(papers, session_dic, session_id_dic):
    """Note that sessions_json now contains all sessions, both in papers and also sessions
    """
    # groupby excludes rows with nan values
    for session, group in papers.groupby('session'):
        has_valid_years = not group['year'].isnull().all()
        if session in session_dic:
            # if session is already in session_dic
            # update data
            session_dic[session]['years'] = [int(year) for year in group['year'].dropna().unique()] if has_valid_years else []
            session_dic[session]['paper_count'] = int(len(group))
        else:
            # if session is not in session_dic
            # add it to session_dic
            dic = {}
            dic['session'] = session
            dic['years'] = [int(year) for year in group['year'].dropna().unique()] if has_valid_years else []
            dic['paper_count'] = int(len(group))
            dic['session_type'] = None 
            dic['chair_name'] = None 
            dic['chair_affiliation'] = None
            try:
                dic['division'] = group.division.dropna().unique()[0]
            except:
                dic['division'] = None
            session_dic[session] = dic
    sessions_json = list(session_dic.values())
    for session in sessions_json:
        session['session_id'] = session_id_dic.get(session['session'], None)
        session['paper_count'] = session.get('paper_count', 0)
        session['years'] = session.get('years', [])  # Ensure 'years' is present
        # this function is for all sessions present in the papers_df
        # but the original session_dic is all sessions in sessions_df whose Session Title is not null
        # so some sessions in session_dic but not in papers_df won't have 'year'
    return sessions_json

def deduplicate_affiliations(affs, threshold=50):
    if len(affs) == 1:
        return affs
    res = []
    seen = set()
    for aff in affs:
        if aff in seen:
            continue 
        similar_affs = [other_aff for other_aff in affs 
                        if other_aff not in seen and 
                        fuzz.ratio(aff, other_aff) > threshold
                        ]
        longest_aff = max(similar_affs, key=len)
        res.append(longest_aff)
        seen.update(similar_affs)
    return res

def get_authors_json(AUTHORS_DF):
    authors = pd.read_csv(AUTHORS_DF)
    authors_json = []
    for author_name, group in authors.groupby('Author Name'):
        # sort by year to make sure affs are in temporal order 
        group = group.sort_values('Year', ascending=True)
        paper_ids = list(group['Paper ID'].unique())
        affs = list(group['Author Affiliation'].dropna().unique())
        deduped_affs = deduplicate_affiliations(affs) or []
        clean_deduped_affs = [aff for aff in deduped_affs if aff is not None]
        years = [int(year) for year in group['Year'].unique()]
        dic = {
            'author_name': author_name,
            'attend_count': int(len(years)),
            'paper_count': int(len(paper_ids)),
            'paper_ids': paper_ids,
            'affiliations': deduped_affs,
            'affiliation_history': " → ".join(clean_deduped_affs),
            'years_attended': years,
        }
        authors_json.append(dic)
    # sort by attend_count, descending
    return sorted(authors_json, key=lambda x: x['attend_count'], reverse=True)

def get_indexed_papers_json(papers_json_raw):
     return {
        paper['paper_id']: paper for paper in papers_json_raw
    }

def get_sessionId_papers_json(papers_json_raw):
    sessionId_papers_json = defaultdict(list)
    for paper in papers_json_raw:
        if paper.get('session_info') and paper['session_info'].get('session_id'):
            session_id = paper['session_info']['session_id']
            sessionId_papers_json[session_id].append(paper)
    return dict(sessionId_papers_json)

def get_author_paper_ids_json(authors_json_raw):
    author_paper_ids_dict = {}
    for author in authors_json_raw:
        if author.get('author_name'):
            author_name = author.get('author_name')
            author_paper_ids_dict[author_name] = author.get("paper_ids")
    return dict(author_paper_ids_dict)

if __name__ == '__main__':
    papers = process_papers_df(PAPERS_DF)
    paper_ids = papers.paper_id.unique()
    session_id_dic = get_session_id_dic(papers, SESSIONS_DF)
    papers_json_raw = json.loads(papers.to_json(orient='records'))
    authorships_dic, paperid_authors_dic = get_authorships_dic_and_paperid_authors_dic(
        AUTHORS_DF
    )
    session_dic = get_session_dic(SESSIONS_DF)
    update_papers_json(
        papers_json_raw, 
        authorships_dic, 
        paperid_authors_dic, 
        session_dic,
        session_id_dic
    )
    sessions_json_raw = get_sessions_json(
        papers, 
        session_dic, 
        session_id_dic
    )
    authors_json_raw = get_authors_json(AUTHORS_DF)

    # paper_id (str): paper (Dict)
    indexed_papers_json = get_indexed_papers_json(papers_json_raw)

    # session_id (str): papers (List of Dict)
    sessionId_papers_json = get_sessionId_papers_json(papers_json_raw)

    # author name (str): paper_ids (List of str)
    author_paper_ids_json = get_author_paper_ids_json(authors_json_raw)

    with open(PAPERS_JSON, 'w') as f:
        json.dump(papers_json_raw, f, indent=2)
    with open(AUTHORS_JSON, 'w') as f:
        json.dump(authors_json_raw, f, indent=2)
    with open(SESSIONS_JSON, 'w') as f:
        json.dump(sessions_json_raw, f, indent=2)

    with open(INDEXED_PAPERS_JSON, 'w') as f:
        json.dump(indexed_papers_json, f, indent=2)

    with open(SESSIONID_PAPERS_JSON, 'w') as f:
        json.dump(sessionId_papers_json, f, indent=2)

    with open(AUTHOR_PAPER_IDS_JSON, 'w') as f:
        json.dump(author_paper_ids_json, f, indent=2)

    print('Files written. All should be in place now.')