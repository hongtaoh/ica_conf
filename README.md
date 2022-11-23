# ICA Conference Data Explorer 

## Why this project?

It surprised me that we had over 20 years of data of ICA annual conferences and yet no one has organized it in a way that every researcher has easy access to it. It is a painful effort to scrape all the data manually and I do not expect every scholar to do that. 

But why ICA conference data? Why do we need it? What is it good for? I have the following ideas:

  1. To inspire new research ideas. Right now, most communication literature came from journal papers (searched mostly in Google Scholar). Findings from conferences may provide a new perspective and inspire new directions. 

  2. Publications might have biases (For example, https://doi.org/10.1093/hcr/hqz015). Not all research projects end up being published. To circumbent publication bias, it is important to see the topics that are researched but not published (This idea is inspired by Yiwei Xu from Cornell). ICA annual conferences are a good starting poing for communication science. Note that ICA annual conferences are peer reviewed and selective. Therefore, even though they are not publisehd, their quality is still quaranteed. This is different from non peer-review preprints. 

  3. For larger scientometric analysis. The ICA annual conference data that we collected is larger. It contains over 40K papers and 120K scholars (a rough guess). This dataset is useful for large scale scientometric analysis. For example, to study the topic evolution of communication studies in the past 20 years or to study academic collaboration or mobility within the filed of communication 

## Plans

I am thinking of (1) design an interactive paper explorationn system, (2) clean and make public the the dataset, and (3) write a paper based on preliminary results. I do not plan to do comprehensive analyses based on the data; that is the job for other scholars if they want to use our dataset. 

## Introduction to this Repository

This repository now has three folders: 

  - Data: where all data is stored. 
  - Notebooks: this is for exploratory coding. It is mainly useful for me, but maynot be useful for others. 
  - Workflow: this is where all the codes are stored, mostly scrapers and data processing scripts. 

## Data

You do not need to pay any attention to folders of `deprecated`. Right now, all preliminary data is stored in the folder of `interim`. I still need to process them. Processed data will be pushed to the folder of `processed`.

## Workflow

I used [`snakemake`](https://github.com/hongtaoh/snakemake-tutorial) to manage the workflow. Details are in `Snakefile`.

### Scripts

- `scrape_2003_2004.py` scraped all data from 2003 to 2004

- `scrape_2005_2013.py` scraped all data from 2005 to 2013

- `scrape_2014_onward_paper_session.py` scraped data from 2014 to 2018, for the paper sessions. 

- `scrape_2014_onward_interactive_paper.py` scraped data for posters (extended abstracts) from 2014 to 2018. 
