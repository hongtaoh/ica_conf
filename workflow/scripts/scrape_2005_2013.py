"""
scrape years between 2009 and 2013
"""

import pandas as pd
import numpy as np
import time 
import math
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
import sys

PAPER_2005_2013 = sys.argv[1]
AUTHOR_2005_2013 = sys.argv[2]

def click_on_view_program():
	all_btn = driver.find_elements(
		By.CSS_SELECTOR, 
		"div.menu_item__icon_text_window__text > a.mainmenu_text"
	)
	for btn in all_btn:
		if 'Program' in btn.text:
			view_program_btn = btn 
			break
	view_program_btn.click()

def click_on_individual_presentations():
	'''
	To click on 'individual presentations'
	'''
	presentations = wait.until(EC.element_to_be_clickable((
		By.XPATH,
		'//td[@class="tab_topped_window__tab_cell"][2]'
	)))
	presentations.click()

def get_papers():
	"""
	get all paper elements in the current page
	"""
	papers = driver.find_elements(
		By.CSS_SELECTOR, 'tr.worksheet_window__row__light, tr.worksheet_window__row__dark'
	)
	return papers

def removeprefix(text, prefix):
	# https://stackoverflow.com/a/16891418
	if text.startswith(prefix):
		return text[len(prefix):]
	return text 

def get_paper_meta(paper, year, paper_meta_dict_list):
	"""
	get paper index, paper title, and paper_type
		the author names can be found here but I'll collect later in the view page
	"""
	idx = paper.find_element(
		By.CSS_SELECTOR, 'td[title="##"]').text
	## in the format of '0001'
	paper_id = year + '-' + idx.zfill(4)
	# summary elements:
	summary = paper.find_element(
		By.CSS_SELECTOR, 'td[title="Summary"]'
	)
	title = summary.find_element(
		By.CSS_SELECTOR, 'a.search_headingtext'
	).text
	summary_info = summary.find_elements(
		By.CSS_SELECTOR, 'td[style="padding: 5px;"] tr'
	)
	session = np.nan
	division = np.nan
	submission_type = np.nan
	research_areas = np.nan
	for i in summary_info:
		if 'In Session Submission' in i.text:
			session = removeprefix(i.text, '  In Session Submission: ')
		elif 'Session Submission Division' in i.text:
			division = removeprefix(i.text, '  Session Submission Division: ')
		elif 'Session Submission Unit' in i.text:
			division = removeprefix(i.text, '  Session Submission Unit: ')
		elif 'Submission type' in i.text:
			submission_type = removeprefix(i.text, '  Individual Submission type: ')
		elif 'Research Areas:' in i.text:
			research_areas = removeprefix(i.text, '  Research Areas: ')
	paper_meta_dict = {
		'Paper ID': paper_id,
		'Title': title,
		'Session': session,
		'Division/Unit': division,
		'Sumission Type': submission_type,
		'Research Areas': research_areas,
	}
	# update the dict list
	paper_meta_dict_list.append(paper_meta_dict)
	return paper_meta_dict

def open_view(paper):
	"""
	Input:
		paper element
	Aim:
		open a new window and click 'view'
	"""
	action = paper.find_element(
		By.CSS_SELECTOR, 'td[title="Action"]'
	)
	view_link_e = action.find_element(
				By.CSS_SELECTOR, "li.action_list > a.fieldtext"
			)
	view_link = view_link_e.get_attribute('href')
	driver.execute_script("window.open('');")
	driver.switch_to.window(driver.window_handles[1])
	driver.get(view_link)

def get_title_to_check(paper_meta_dict_list):
	# there are two 'tr.header font.headingtext'
	# title is the second one
	headingtexts = driver.find_elements(
		By.CSS_SELECTOR, 'tr.header font.headingtext'
	)
	title_to_check = headingtexts[1].text
	# update the most recent paper_meta_dict_list
	paper_meta_dict_list[-1]['Title to Check'] = title_to_check
	return title_to_check

def get_session_to_check(paper_meta_dict_list):
	session_to_check = driver.find_element(
		By.CSS_SELECTOR, 'blockquote.tight > a.search_headingtext'
	)
	session_to_check = session_to_check.text
	# update the most recent paper_meta_dict_list
	paper_meta_dict_list[-1]['Session to Check'] = session_to_check
	return session_to_check

def get_authors(paper_meta_dict, author_dict_list):
	paper_id, title = paper_meta_dict['Paper ID'], paper_meta_dict['Title']
	# note that authors_e will return a list since there might be multiple authors
	authors = driver.find_elements(
		By.CSS_SELECTOR, 'a.search_fieldtext_name'
	)
	for author in authors:
		author_idx = authors.index(author) + 1
		authorNum = len(authors)
		author_elements = author.text.split(' (')
		author_name = author_elements[0]
		# doc: https://docs.python.org/3.4/library/stdtypes.html?highlight=strip#str.rstrip
		# some don't contain '()', i.e., affiliation info
		try:
			author_aff = author_elements[1].rstrip(')')
		except:
			author_aff = np.nan
		author_dict = {
			'Paper ID': paper_id,
			'Paper Title': title,
			'Number of Authors': authorNum,
			'Author Position': author_idx,
			'Author Name': author_name,
			'Author Affiliation': author_aff,
		}
		author_dict_list.append(author_dict)

def get_abstract(paper_meta_dict_list):
	# abstract
	abstract = driver.find_elements(
		By.CSS_SELECTOR, 'blockquote.tight'
	)[-1]
	abstract = abstract.text
	paper_meta_dict_list[-1]['Abstract'] = abstract
	return abstract

def scrape_one_page(year, page_num, paper_meta_dict_list, author_dict_list):
	papers = get_papers()
	for paper in papers:
	## to test:
	# for paper in papers[0:1]:
		paper_idx = papers.index(paper) + 1
		paper_meta_dict = get_paper_meta(paper, year, paper_meta_dict_list)
		open_view(paper)
		get_title_to_check(paper_meta_dict_list)
		get_session_to_check(paper_meta_dict_list)
		get_authors(paper_meta_dict, author_dict_list)
		get_abstract(paper_meta_dict_list)
		driver.close()
		driver.switch_to.window(driver.window_handles[0])
		print(f'Year {year}, Page {page_num} Paper {paper_idx} is done')
		time.sleep(0.05)

def get_iterators():
	iterators = driver.find_elements(
		By.XPATH, '//div[@class="iterator"][1]/form//a[@class="fieldtext"]'
	)
	return iterators

if __name__ == '__main__':
	# initiate list to contain data
	paper_meta_dict_list = []
	author_dict_list = []
	driver = webdriver.Firefox()
	wait = WebDriverWait(driver, 10)
	urlBase = 'https://convention2.allacademic.com/one/ica/ica'
	# scrape 2005~2013
	years = range(5,14)
	for year in years:
		year = str(year).zfill(2)
		url = urlBase + year
		driver.get(url)
		# year in the form of 2003/2004
		year = f'20{year}'
		print(f'{year} has started!')
		click_on_view_program()
		click_on_individual_presentations()
		# to calculate total pages
		iterators = get_iterators()
		total_pages = int(iterators[-2].text)
		for i in range(1,total_pages+1):
			print(f'page {i} has started')
			page_num = i
			if i < 10:
				pass
			elif i >= 10 and i < 17:
				select = Select(driver.find_element(
					By.XPATH, '//div[@class="iterator"][1] // select'
				))
				select.select_by_visible_text('+ 10')
			elif i >= 17 and i < 27:
				select = Select(driver.find_element(
					By.XPATH, '//div[@class="iterator"][1] // select'
				))
				select.select_by_visible_text('+ 20')
			elif i >= 27 and i < 37:
				select = Select(driver.find_element(
					By.XPATH, '//div[@class="iterator"][1] // select'
				))
				select.select_by_visible_text('+ 30')
			else:
				iterators = get_iterators()
				iterators[-2].click()
			# this achieves something I never thought about. 
			# when i == 21, after selecting '+ 20', the current iterator is 21
			# then, the get_iterators() function will skip the current iterator
			# since no j is equal to 21, the program won't even go to the for loop
			# but will directly start `scrape_one_page()`
			iterators = get_iterators()
			for j in iterators:
				if (j.text == str(i)):
					current_idx = int(j.text)
					j.click()
					break 
			scrape_one_page(
				year,
				page_num, 
				paper_meta_dict_list, 
				author_dict_list
			)
			iterators = get_iterators()
			iterators[1].click()
	print('Everything done!')
	driver.close()
	driver.quit()
	print('Writing to file now...')
	pd.DataFrame(paper_meta_dict_list).to_csv(PAPER_2005_2013, index = False)
	pd.DataFrame(author_dict_list).to_csv(AUTHOR_2005_2013, index = False)

