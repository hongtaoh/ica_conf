"""
scrape 2014 onward

INTERACTIVE PAPER SESSION 
"""

import pandas as pd
import numpy as np
import time 
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
import sys
import random 

INTERACTIVVE_SESSION_2014_2018 = sys.argv[1]
INTERACTIVVE_AUTHOR_2014_2018 = sys.argv[2]
INTERACTIVVE_PAPER_2014_2018 = sys.argv[3]

def click_browse_by_session_type():
	'''click on "browse by session type"
	'''
	browse_by_session_type = driver.find_elements(
		By.CSS_SELECTOR, "li.ui-li-has-icon.ui-last-child > a"
	)[3]
	browse_by_session_type.click()

def click_interactive_paper_session():
	'''click "paper session" button
	'''
	paper_session = driver.find_element(
		By.XPATH, '//li[@class="ui-li-has-count ui-first-child"] //a[@class="ui-btn"]'
	)
	paper_session.click()

def get_sessions():
	'''These are session links
	'''
	sessions = driver.find_elements(
		By.CSS_SELECTOR, 'a.ul-li-has-alt-left.ui-btn'
	)
	return sessions

def update_session_meta(year, session_tuples):
	'''update session metadata: session title, session sub unit, 
		session chair name and affiliation
	'''
	session_title_e = driver.find_element(
		By.CSS_SELECTOR, 'h3'
	)
	session_title = session_title_e.text

	# sub unit, cosponsor, chair, the presentations
	h4s = driver.find_elements(
		By.CSS_SELECTOR, 'h4'
	)
	h4s_texts = [i.text for i in h4s]
	sub_unit_e_idx = h4s_texts.index('Sub Unit')
	'''sub unit and chair are very tricky
	Some examples: year 2015, session "Environmental Journalism: Coverage, Reader Response, and Mediators"
	  in the above example, 'chair' is below 'cosponsor'
	Another example, year 2015, session 'B.E.S.T.: Organizations, Communication, and Technology'
	  This example is a little bit strange because we have 'abstract' here. However, it does not have the gray area
	My conclusion is that it seems that the gray box for sub unit is always the first one so
	I can use the index of '4'. For chair, I need to get its index and add it by 5
	'''
	try:
		sub_unit_e = driver.find_elements(
			By.CSS_SELECTOR, 'ul.ui-listview.ui-listview-inset.ui-corner-all.ui-shadow'
		)[4]
		sub_unit = sub_unit_e.text
	except:
		sub_unit = None
	# if there is no 'Chair', for example, session 200 of 2016,
	# then there is no need to proceed further. 
	if 'Chair' not in h4s_texts:
		chair_name = None
		chair_aff = None
	else:
		try:
			if 'Cosponsor' in h4s_texts:
				chair_e_idx = 6
			else:
				chair_e_idx = 5
			# chair_e_idx = h4s_texts.index('Chair')
			chair_graybox = driver.find_elements(
				By.CSS_SELECTOR, 'ul.ui-listview.ui-listview-inset.ui-corner-all.ui-shadow'
			)[chair_e_idx]
			chair_es = chair_graybox.find_elements(
				By.CSS_SELECTOR, 'li'
			)
			if chair_es:
				if len(chair_es) == 1:
					chair_info = chair_es[0].text
					chair_name = chair_info.split(', ')[0]
					chair_aff = chair_info.split(', ')[1]
				# this is to solve the issue of when there are multiple chairs. For example,
				# year 2018, session 'Research Escalator - Part 1'
				else:
					chair_name = ''
					chair_aff = ''
					for chair_e in chair_es:
						chair_info = chair_e.text
						chair_name_i = chair_info.split(', ')[0]
						chair_aff_i = chair_info.split(', ')[1]
						chair_name += chair_name_i
						chair_aff += chair_aff_i
						if chair_e != chair_es[-1]:
							chair_name += '; '
							chair_aff += '; '
		except:
			chair_name = None
			chair_aff = None

	session_tuples.append((
		year,
		'Interactive Paper Session',
		session_title,
		sub_unit,
		chair_name,
		chair_aff,
	))
	# return session title and sub_unit so that I can use them later
	return session_title, sub_unit

def get_author_num():
	"""This is to get authors element and author number, 
		which I use later in get paper info and author info
	"""
	authors_e = driver.find_elements(
		By.CSS_SELECTOR, 'ul.ui-listview.ui-listview-inset.ui-corner-all.ui-shadow:last-child  a.ui-icon-carat-r'
	)[2:]
	author_num = len(authors_e)
	return authors_e, author_num

def get_author_info(authors_e, author_num, author_tuples, paper_title, paper_id, year):
	'''get author info and update author tuples
	'''
	paper_id = year + '-' + str(paper_id).zfill(4)
	for author in authors_e:
		author_position = authors_e.index(author) + 1
		# split on the first ', ' only to solve the issue of 'person, aff, dept'
		try:
			author_name, author_aff = author.text.split(', ', 1)
		# For example:
		# 2016, Gaining Access to Social Capital, Louis Leung has no aff
		except:
			author_name = author.text
			author_aff = None
		author_tuples.append((
			paper_id,
			paper_title,
			year,
			author_num,
			author_position,
			author_name,
			author_aff
		))

def get_paper_info(paper_tuples, author_num, session_title, sub_unit, year, paper_id):
	'''get paper info and update paper tuples
	'''
	paper_id = year + '-' + str(paper_id).zfill(4)
	paper_title_e = driver.find_element(
		By.CSS_SELECTOR, 'h3'
	)
	paper_title = paper_title_e.text
	abstract = driver.find_element(
		By.CSS_SELECTOR, 'blockquote > p'
	).text 
	paper_tuples.append((
		paper_id,
		year,
		'Poster',
		paper_title, 
		author_num, 
		abstract, 
		session_title, 
		sub_unit,
	))
	# return paper title so I can use it in get_author_info
	return paper_title

def get_papers():
	
	h4s = driver.find_elements(
		By.CSS_SELECTOR, 'h4'
	)
	if h4s[-1].get_attribute('innerHTML') == 'Individual Presentations':
		# I do not know why but the first two selections are not paper elements. I need to remove them. 
		papers = driver.find_elements(
			By.CSS_SELECTOR, 'ul.ui-listview.ui-listview-inset.ui-corner-all.ui-shadow:last-child  a.ui-icon-carat-r'
		)[2:]
	# this is to prevent something like the session of
	# Good Grief! Disasters, Crises, and High-Risk Organizational Environments
		return papers
	elif h4s[-1].get_attribute('innerHTML') in ['Respondent', 'Respondents']:
		papers = driver.find_elements(
			By.CSS_SELECTOR, 'ul.ui-listview.ui-listview-inset.ui-corner-all.ui-shadow:nth-last-child(3)  a.ui-icon-carat-r'
		)[2:]

		return papers
	else:
		'''Why this happen? You can go to year 2016, session 262 and you'll know that there
		   are no papers. 

		   session 103 of year 2014 also have no papers
		'''
		# print('Something went wrong!')
		print('TEHRE PROBABLY ARE NO PAPERS HERE')
		# to_scrape_later_tuples.append((year, session_index))

if __name__ == '__main__':
	driver = webdriver.Firefox()
	wait = WebDriverWait(driver, 10)
	urlBase = 'https://convention2.allacademic.com/one/ica/ica'
	# scrape 2014-2018
	# years = range(14,19)
	years = [14, 15, 16, 17, 18]
	session_tuples = []
	author_tuples = []
	paper_tuples = []
	for year in years:
		year = str(year)
		url = urlBase + year
		driver.get(url)
		# year in the form of 2014/2018
		year = f'20{year}'
		print(f'{year} has started!')
		click_browse_by_session_type()
		click_interactive_paper_session()
		sessions = get_sessions()
		print(f'There are {len(sessions)} sessions.')

		# randomly choose 10 sessions for testing
		random_sessions = random.sample(sessions, 5)
		# to assign paper id. initiate it as 0 and then add 1 each time
		paper_id = 0
		# for s in sessions:
		for s in random_sessions:
			session_index = sessions.index(s)
			s_link = s.get_attribute('href')
			# open a new window
			driver.execute_script("window.open('');")
			# switch to the new window
			driver.switch_to.window(driver.window_handles[1])
			# open the session
			driver.get(s_link)
			session_title, sub_unit = update_session_meta(year, session_tuples)
			if 'preconference:' not in session_title.lower():
				print(f'Session {session_index} has started')
				papers = get_papers()
				# Sometimes paper is none, for example, year 2016, session
				# Communication and Technology, Game Studies, and Information Systems Joint Reception
				if papers:
					print(f'There are {len(papers)} papers.')
					for p in papers:
						# 2016, SESSION 85 HAS TROUBLES
						try:
							p_link = p.get_attribute('href')
							driver.execute_script("window.open('');")
							driver.switch_to.window(driver.window_handles[2])
							driver.get(p_link)
							authors_e, author_num = get_author_num()
							paper_title = get_paper_info(
								paper_tuples, 
								author_num, 
								session_title, 
								sub_unit, 
								year, 
								paper_id
							)
							get_author_info(authors_e, author_num, author_tuples, paper_title, paper_id, year)
						except:
							print('This paper is unavailable.')
						paper_id += 1

						print(f'Paper {papers.index(p) + 1} is done.')
						time.sleep(0.5+random.uniform(0, 0.5)) 
						# close windown 2
						driver.close()
						# switch to window 1
						driver.switch_to.window(driver.window_handles[1])

				print(f'Session {session_index} is done.')
				time.sleep(0.5+random.uniform(0, 0.5)) 
			else:
				print(f'Session {session_index} is Preconference.')
			# close window 1
			driver.close()
			# switch to windown 0
			driver.switch_to.window(driver.window_handles[0])
			
	print('Everything done!')
	driver.close()
	driver.quit()
			
	pd.DataFrame(session_tuples, columns = [
		'year',
		'session type',
		'session title',
		'sub unit',
		'chair name',
		'chair aff',
		]).to_csv(INTERACTIVVE_SESSION_2014_2018, index = False)
	pd.DataFrame(author_tuples, columns = [
		'paper id',
		'paper title',
		'year',
		'author number',
		'author position',
		'author name',
		'author aff'
		]).to_csv(INTERACTIVVE_AUTHOR_2014_2018, index = False)
	pd.DataFrame(paper_tuples, columns = [
		'paper id',
		'year',
		'paper type',
		'paper title',
		'author number',
		'abstract',
		'session title',
		'sub unit'
		]).to_csv(INTERACTIVVE_PAPER_2014_2018, index = False)
		