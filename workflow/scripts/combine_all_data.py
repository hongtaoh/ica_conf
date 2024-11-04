"""
Combine all data together
"""

import pandas as pd
import numpy as np
import sys
import hashlib
import uuid 

PAPER_2003_2004 = sys.argv[1]
PAPER_2005_2013 = sys.argv[2]
PAPER_2014_2018 = sys.argv[3]
INTERACTIVE_PAPER_2014_2018 = sys.argv[4]
AUTHOR_2003_2004 = sys.argv[5]
AUTHOR_2005_2013 = sys.argv[6]
AUTHOR_2014_2018 = sys.argv[7]
INTERACTIVE_AUTHOR_2014_2018 = sys.argv[8]
SESSION_2014_2018 = sys.argv[9]
INTERACTIVE_SESSION_2014_2018 = sys.argv[10]
PAPERS_DF = sys.argv[11]
AUTHORS_DF = sys.argv[12]
SESSIONS_DF = sys.argv[13]

# generate new paper id based on title_paper_id
def generate_unique_id(title_paper_id):
	return hashlib.md5(str(title_paper_id).encode()).hexdigest()[:16]

def update_paper_df_and_get_id_dic(paper_df):
	"""
	The purpose of this function is to update Paper ID because
	The old paper_ids are not unique.

	We update the id and get a dict where key is old_paper_id-title and value is the
	new paper_id (str)
	"""
	# change col name
	paper_df.rename(columns={'Paper ID': 'Old Paper ID'}, inplace=True)

	# check whether title_paper_ids are truly unique
	paper_df['Title_Old_Paper_ID'] = paper_df.apply(
		lambda row: row['Title'] + "_" + str(row['Old Paper ID']), axis = 1)
	if len(paper_df['Title_Old_Paper_ID'].unique()) == paper_df.shape[0]:
		print("Title_Old_Paper_ID is truly unique")
	else:
		print("Even Title_Old_Paper_ID is not truly unique")

	paper_df['Paper ID'] = ''

	for year, group in paper_df.groupby('Year'):
		for idx, row in group.iterrows():
			title_paper_id = row['Title'] + "_" + str(row['Old Paper ID'])
			paper_df.at[idx, 'Paper ID'] = f"{year}-{generate_unique_id(title_paper_id)}"

	# check whether the new paper ids are unique or not
	if len(paper_df['Paper ID'].unique()) == paper_df.shape[0]:
		print("The new Paper IDs are truly unique")
	else:
		print("The new Paper IDs are not truly unique")
		print(len(paper_df['Paper ID'].unique()))
		print(paper_df.shape[0])

	# generate the dic 
	id_dic = dict(zip(paper_df['Title_Old_Paper_ID'], paper_df['Paper ID']))

	paper_df.drop(columns=['Title_Old_Paper_ID', 'Old Paper ID'], inplace=True)

	paper_df = paper_df[['Paper ID'] + [
		col for col in paper_df.columns if col != 'Paper ID']]
	
	return paper_df, id_dic

def update_author_df(author_df, id_dic):
	"""Update paper_id in author_df
	"""
	author_df.rename(columns={'Paper ID': 'Old Paper ID'}, inplace=True)

	# Create 'Title_Old_Paper_ID' only if both columns exist
	author_df['Title_Old_Paper_ID'] = author_df.apply(
		lambda row: row['Title'] + "_" + str(row['Old Paper ID']), axis=1
	)

	# use map instead of apply to avoid keyerror
	author_df['Paper ID'] = author_df['Title_Old_Paper_ID'].map(id_dic)

	author_df.drop(columns=['Title_Old_Paper_ID', 'Old Paper ID'], inplace=True)

	author_df = author_df[['Paper ID'] + [
		col for col in author_df.columns if col != 'Paper ID']]
	
	return author_df

if __name__ == '__main__':
	# import all data 
	paper1 = pd.read_csv(PAPER_2003_2004)
	paper2 = pd.read_csv(PAPER_2005_2013)
	paper3 = pd.read_csv(PAPER_2014_2018)
	paper4 = pd.read_csv(INTERACTIVE_PAPER_2014_2018)
	author1 = pd.read_csv(AUTHOR_2003_2004)
	author2 = pd.read_csv(AUTHOR_2005_2013)
	author3 = pd.read_csv(AUTHOR_2014_2018)
	author4 = pd.read_csv(INTERACTIVE_AUTHOR_2014_2018)
	session1 = pd.read_csv(SESSION_2014_2018)
	session2 = pd.read_csv(INTERACTIVE_SESSION_2014_2018)

	# add 'Year' to paper 1, paper2, author1, and author2
	paper2['Year'] = [i.split('-')[0] for i in paper2['Paper ID']]
	paper1['Year'] = [i.split('-')[0] for i in paper1['Paper ID']]
	author1['Year'] = [i.split('-')[0] for i in author1['Paper ID']]
	author2['Year'] = [i.split('-')[0] for i in author2['Paper ID']]

	# change author3 and author4 colname
	author3.columns = [
		'Paper ID', 'Paper Title', 'Year', 
		'Number of Authors', 'Author Position', 
		'Author Name', 'Author Affiliation'
	]
	author4.columns = [
		'Paper ID', 'Paper Title', 'Year', 
		'Number of Authors', 'Author Position', 
		'Author Name', 'Author Affiliation'
	]

	# author_df 
	author_df = pd.concat([author1, author2, author3, author4], axis = 0)
	author_df.rename(columns={'Paper Title':'Title'}, inplace=True)

	print(f'Author DF is done. Its shape: {author_df.shape}')

	# create a paper id: author num dict 
	id_num_author_dict = dict(zip(author_df['Paper ID'], author_df['Number of Authors']))

	# there are four missing paper ids in author2
	paper2_id = paper2['Paper ID'].tolist()
	author2_id = list(set(author2['Paper ID']))
	print(f'Number of paper ids in paper2: {len(paper2_id)}')
	print(f'Number of paper ids in author2: {len(author2_id)}')
	missing_paper_id = [x for x in paper2_id if x not in author2_id]
	print(missing_paper_id)

	# update dict
	for x in missing_paper_id:
		id_num_author_dict[x] = np.nan

	# add number of authors to paper1 and paper2
	paper1['Number of Authors'] = [id_num_author_dict[pid] for pid in paper1['Paper ID']]
	paper2['Number of Authors'] = [id_num_author_dict[pid] for pid in paper2['Paper ID']]

	# select cols
	paper1 = paper1[['Paper ID', 'Title', 'Type', 'Abstract', 'Number of Authors', 'Year']]
	paper2 = paper2[[
		'Paper ID', 'Title', 'Sumission Type', 
		'Abstract', 'Number of Authors', 'Year', 'Session', 'Division/Unit'
	]]

	# update colnmaes
	paper1.columns = ['Paper ID', 'Title', 'Paper Type', 
		'Abstract', 'Number of Authors', 'Year']
	paper2.columns = ['Paper ID', 'Title', 'Paper Type', 
		'Abstract', 'Number of Authors', 'Year', 'Session', 'Division/Unit']
	paper3.columns = ['Paper ID', 'Year', 'Paper Type', 'Title', 
		'Number of Authors', 'Abstract', 'Session', 'Division/Unit']
	paper4.columns = ['Paper ID', 'Year', 'Paper Type', 'Title', 
		'Number of Authors', 'Abstract', 'Session', 'Division/Unit']

	# concatenate paper df
	paper_df = pd.concat([paper1, paper2, paper3, paper4], axis = 0)
	print("Before concatenation, unique rows in paper_df:", paper_df.shape[0])
	paper_df.drop_duplicates(
		subset=['Title', 'Paper ID', 'Year'], inplace=True)
	print("After concatenation, unique rows in paper_df:", paper_df.shape[0])
	
	# get id: authors dic
	paperid_authors_dic = {}
	for paper_id, group in author_df.groupby('Paper ID'):
		paperid_authors_dic[paper_id] = np.array(group['Author Name'])

	paper_df['Authors'] = paper_df['Paper ID'].apply(
		lambda x: ", ".join(paperid_authors_dic[x]) if x in paperid_authors_dic else np.nan)

	# concatenate session df 
	session_df = pd.concat([session1, session2], axis = 0)
	session_df.columns = [
		'Year', 'Session Type', 'Session Title', 
		'Division/Unit', 'Chair Name', 'Chair Affiliation'
	]
	
	# write to file
	paper_df.to_csv(PAPERS_DF, index=False)
	author_df.to_csv(AUTHORS_DF, index=False)
	session_df.to_csv(SESSIONS_DF, index=False)

	print('Files written. All should be in place now.')
	print("Starting with recreading paper ids")

	paper_df = pd.read_csv(PAPERS_DF)
	author_df = pd.read_csv(AUTHORS_DF)

	# I need to reassign paper_ids because {2014, 2015, 2016, 2017, 2018}
	# contains duplicated paper ids
	paper_df, id_dic = update_paper_df_and_get_id_dic(paper_df)
	author_df = update_author_df(author_df, id_dic)

	print('Re-writing to files now.')
	paper_df.to_csv(PAPERS_DF, index=False)
	author_df.to_csv(AUTHORS_DF, index=False)
	print('Files written. All should be in place now.')


	
