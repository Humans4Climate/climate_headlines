from Climate_Headlines_Update.scripts import database_and_output
import logging
import sys
import os
from datetime import datetime, timedelta
from collections import Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import config
from scripts import scrapers
from scripts import database_and_output as db_and_out

import azure.functions as func

class ClimateNewsRunner():

    def __init__(self):
        # Logging
        self.logger = logging.getLogger('daily_news_updater')
        # self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('(%(asctime)s)%(module)s.%(funcName)s >> %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        self.date_today = datetime.today().strftime(config.date_format)
        self.date_yesterday = (datetime.today() - timedelta(days=1)).strftime(config.date_format)

        # Initiate the feedparser class
        self.parse_rss = scrapers.FeedReader()
        # Initiate the bing querier class
        self.bing_news = scrapers.BingNewsScraper(self.date_yesterday)
        # Initiate the MongoDB update class
        self.update_mongo = database_and_output.UpdateDB(self.date_today, self.date_yesterday)
        # Initate gspread class
        self.write_spreadsheet = database_and_output.UpdateSpreadsheet(self.date_today)

    def run_strategies(self):
        '''Strategy 1: Get all new news by climate-specific sources previously
        identified, through RSS queries. No keyword-title filter applied
            Strategy 2 and 3: Get all news from Bing, set different variables, and 
        news from RSS with lower priority.
        Returns None
        '''
        strategy_results = {}
        # Strategy 1
        # (this and feeds in strategy two follow the same process now)
        for feed_data in config.rss_climate_specific:
            parsed_feed_news = self.parse_rss.get_news_one_feed(feed_data, config.strategies[0], keyword_title=True)
            strategy_results.update(parsed_feed_news)
        # Strategy 2
        for feed_data in config.rss_general:
            parsed_feed_news = self.parse_rss.get_news_one_feed(feed_data, config.strategies[1], keyword_title=True)
            strategy_results.update(parsed_feed_news)
        # Strategy 3
        for keyword in config.use_this_word_for_search:
            returned_news_search = self.bing_news.get_news_one_keyword(keyword)
            strategy_results.update(returned_news_search)
        # Save retrieved news to MongoDB and return counts 
        documents_updated = self.update_mongo.update_some_data(strategy_results)
        self.logger.info('All Strategies Mongo Results: || {}'.format(documents_updated))
        return

    def main(self):
        self.logger.info('Started Working on Climate News...')
        # Get news and update MongoDB
        self.run_strategies()
        # write to spreadsheet, today and yesterday's news
        # 2 sheets: only 50 top news, and all found news
        self.write_spreadsheet.main()
        # Tweet latest piece of news
        db_and_out.TweetFromDB(self.date_today).tweet_top_new()
    
####
def main(mytimer: func.TimerRequest) -> None:

    ClimateNewsRunner().main()
