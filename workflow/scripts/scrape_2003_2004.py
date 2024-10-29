"""
scrape 2003 and 2004
"""

import pandas as pd
import numpy as np
import time 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
import sys

PAPER_03_04 = sys.argv[1]
AUTHOR_03_04 = sys.argv[2]

def click_on_search_papers():
	search_papers = wait.until(EC.element_to_be_clickable((
		By.CSS_SELECTOR, 
		"div.menu_item__icon_text_window__text > a.mainmenu_text"
	)))
	search_papers.click()

def get_papers():
	"""
	get all paper elements in the current page
	"""
	papers = driver.find_elements(
		By.CSS_SELECTOR, 'tr.worksheet_window__row__light, tr.worksheet_window__row__dark'
	)
	return papers

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
	submission_type = summary.find_element(
		By.CSS_SELECTOR, 'td[style="padding: 5px;"]'
	).text.lstrip('  Individual Submission type: ')
	paper_meta_dict = {
		'Paper ID': paper_id,
		'Title': title,
		'Type': submission_type
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
	# obtain abstract in the newly opened page
	abstract = driver.find_element(
		By.CSS_SELECTOR, 'blockquote.tight > font.fieldtext'
	).text
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
		get_authors(paper_meta_dict, author_dict_list)
		get_abstract(paper_meta_dict_list)
		driver.close()
		driver.switch_to.window(driver.window_handles[0])
		print(f'Page {page_num} Paper {paper_idx} is done')
		time.sleep(0.5)

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
	# scrape 2003~2004
	years = range(3,5)
	for year in years:
		year = str(year).zfill(2)
		url = urlBase + year
		driver.get(url)
		# year in the form of 2003/2004
		year = f'20{year}'
		print(f'{year} has started!')
		click_on_search_papers()
		# to calculate total pages
		iterators = get_iterators()
		total_pages = int(iterators[-2].text)
		for i in range(1,total_pages+1):
			page_num = i
			if i >= 10:
				if year == '2004':
					print('2004!')
					select = Select(driver.find_element(
						By.XPATH, '//div[@class="iterator"][1] // select'
					))
					select.select_by_visible_text('+ 20')
				else:
					# if '2003', click on '20'
					iterators = get_iterators()
					iterators[-2].click()
			iterators = get_iterators()
			for j in iterators:
				if (j.text == str(i)):
					j.click()
					break 
			scrape_one_page(
				year,
				page_num, 
				paper_meta_dict_list, 
				author_dict_list
			)
			print(f'page {i} is done')
			# go back to the first page
			iterators = get_iterators()
			iterators[1].click()
	print('Everything done!')
	driver.close()
	driver.quit()
	print('Writing to file now...')
	pd.DataFrame(paper_meta_dict_list).to_csv(PAPER_03_04, index = False)
	pd.DataFrame(author_dict_list).to_csv(AUTHOR_03_04, index = False)

