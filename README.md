# Valorant Champions Tour Web Scraper

![banner_picture](banner.jpg)


## Table of Contents

- [About](#about)
- [Using the Data](#using_the_data)
- [Getting Started](#getting_started)
- [Rate Limit](#rate_limit)
- [Usage](#usage)
- [Built With](#built_with)
- [To Do List](#to_do_list)

## About <a name = "about"></a>

**This repository is a little messy right now as I originally had plans to automate this and move it to cloud but I've been busy. If you want to run this, please checkout to the commit history from August 6th, 2024 from the first commit. I will eventually move the main branch back to that version.**

An asynchronous web scraper scraping the 2021 - 2026 Valorant Champions Tour data. It scrapes tournaments, players and agents data from vlr.gg. This is part of the Valorant Champions Tour ETL pipeline. 

## Using the Data <a name ="using_the_data"></a>
The data is publicly available on [Kaggle](https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data).

## Getting Started <a name = "getting_started"></a>


### Prerequisites

- Python 3.10 or higher



### Installing


```
$ git clone https://github.com/RyanLuong1/vct-web-scraping.git
$ cd vct-web-scraping
$ pip3 install -r requirements.txt
```


## Rate Limit <a name = "rate_limit"></a>
Please do not increase the scraping rate on the code to prevent overloading the scraper. Although there is [no robots.txt on vlr.gg](https://www.vlr.gg/30777/is-data-scraping-allowed), please do not overload vlr.gg.

## Usage <a name = "usage"></a>
You must run the commands in this order
```
$ python3 matches_scraper.py
$ python3 agent_pick_rates_scraper.py
$ python3 player_stats_scraper.py
```

If you want to clean the data and you ran the three commands above
```
$ python3 clean_data.py
$ python3 missing_data_scraper.py #This only need to be run if you are cleaning 2021 data
```

If you want to retrieve all the ids (it is best you perform the data clean steps)
```
$ python3 combine_all_columns_value.py
```

## Built With <a name="built_with"></a>
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Pandas](https://pandas.pydata.org/)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [AIOHTTP](https://docs.aiohttp.org/en/stable/)
- [Requests](https://requests.readthedocs.io/en/latest/)

## To Do List <a name ="to_do_list"></a>

1. Clean the data as errors arise
