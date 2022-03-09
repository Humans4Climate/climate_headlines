import tweepy
import gspread
import gspread_formatting as gf
import pymongo
import logging
from tqdm import tqdm
from datetime import datetime

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import config


# create logger
db_and_out_logger = logging.getLogger('daily_news_updater.db_and_out')

class UpdateDB():
    '''Updates MongoDB with data passed as argument in dict form.'''

    def __init__(self, date_today, date_yesterday):
        self.client = pymongo.MongoClient(config.uri)
        self.daily_climate_news = self.client.climate_news.daily_climate_news
        self.date_today, self.date_yesterday = date_today, date_yesterday

    def update_some_data(self, news_dict):
        db_and_out_logger.info('Updating Database')
        # Old Logic
        count_writes = 0
        dupes = 0
        for k, val in tqdm(news_dict.items()):
            formatted = val
            formatted.update({'_id':k})
            try:
                # if there no document with same name and date today, update it
                if self.daily_climate_news.count_documents({'title':formatted['title'],'date':{'$in':[self.date_today,self.date_yesterday]}}) == 0:
                    self.daily_climate_news.insert_one(formatted)
                    count_writes += 1
                else:
                    dupes +=1
            except pymongo.errors.DuplicateKeyError: 
                dupes +=1
        assert len(news_dict) == count_writes + dupes,'{} writes + {} dupes != {} total'.format(
                                                        count_writes, dupes, len(news_dict)
        )
        db_and_out_logger.info('{} news written to daily_climate_news'.format(count_writes))
        db_and_out_logger.info('{} dupes not written'.format(dupes))
        db_and_out_logger.info('Finished updating climate news database on {}'.format(self.date_today))
        # db_and_out_logger.info('Example: \n{}'.format(self.daily_climate_news.find_one({})))

class TweetFromDB():

    def __init__(self, date_today):  
        self.client = pymongo.MongoClient(config.uri)
        self.daily_climate_news = self.client.climate_news.daily_climate_news
        auth = tweepy.OAuthHandler(*config.t_api_keys)
        auth.set_access_token(*config.t_api_tokens)
        self.tweepy_api = tweepy.API(auth)
        self.date_today = date_today

    def choose_best_tweet(self):
        '''Gets all tweets from DB and tweets the most recent piece of news not tweeted yet'''
        recent_cursor = self.daily_climate_news.find({'tweeted':'no', 'date':self.date_today, 'strategy':'major_climate_outlets'})
        most_recent_untweeted_news = next(recent_cursor)
        return most_recent_untweeted_news
        
    def tweet_top_new(self):
        most_recent_untweeted_news = self.choose_best_tweet()
        title = most_recent_untweeted_news['title']
        url = most_recent_untweeted_news['_id']
        _ = self.tweepy_api.update_status(
            '{}\n{}'.format(
                title,
                url
            ))
        self.daily_climate_news.update({'_id':url}, {'$set': {'tweeted':'yes'}})
        db_and_out_logger.info('This piece of news was tweeted!\n>>>> {}\n>>>> {}'.format(title, url))

class UpdateSpreadsheet():

    def __init__(self, date_today):
        self.client = pymongo.MongoClient(config.uri)
        self.daily_climate_news = self.client.climate_news.daily_climate_news
        client = gspread.service_account_from_dict(config.gsheet)
        self.sheet = client.open("Climate Headlines")
        self.date_today = date_today

    def get_worksheet_with_dates(self):
        '''Not used anymore'''
        try:
            worksheet = self.sheet.add_worksheet(title=self.date_today, rows=100, cols=20)
        except gspread.exceptions.APIError:
            worksheet = self.sheet.worksheet(self.date_today)
            self.sheet.del_worksheet(worksheet)
            worksheet = self.sheet.add_worksheet(title=self.date_today, rows=100, cols=20)
        return worksheet
    
    def get_unique_worksheet(self, worksheet_name):
        '''To be used for the.com as a single worksheet that gets overwritten. Gets
        worksheet object and clears all data, then returns worksheet'''
        worksheet = self.sheet.worksheet(worksheet_name)
        worksheet.clear()
        # worksheet = self.sheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
        return worksheet

    def read_news_from_db(self):
        # Get news from mongo
        news_to_spreadsheet = []
        # This goes in order of priority so news should be ordered by strategy,
        # then ordered by date within strategy
        for strategy in config.strategies:
            todays_news = list(self.daily_climate_news.find({
                'date':self.date_today,
                'strategy':strategy}))
            # Sort by recency of publication, within each strategy
            try:
                todays_news = sorted(todays_news, key= lambda d: datetime.strptime(
                    d['date_time'], config.date_time_format),reverse=True)
            except ValueError:
                todays_news = sorted(todays_news, key= lambda d: datetime.strptime(
                    d['date_time'], '%b %d, %I:%M%p'),reverse=True)
            if todays_news:
                news_to_spreadsheet.extend(todays_news)
        # Workaround if 'strategy' doesn't exist
        if not news_to_spreadsheet:
            todays_news = list(self.daily_climate_news.find({
                'date':self.date_today}))
            try:
                todays_news = sorted(todays_news, key= lambda d: datetime.strptime(
                    d['date_time'], config.date_time_format),reverse=True)
            except ValueError:
                todays_news = sorted(todays_news, key= lambda d: datetime.strptime(
                    d['date_time'], '%b %d, %I:%M%p'),reverse=True)
            news_to_spreadsheet = todays_news

        # Add value with ranking according to order
        _ = [item.update({'rank':rank+1}) for rank, item in enumerate(news_to_spreadsheet)]
        # Push limited number of news to spreadsheet
        reduced_news_to_spreadsheet = news_to_spreadsheet[:config.limit_news_sent]
        
        return news_to_spreadsheet, reduced_news_to_spreadsheet

    def update_sheet_todays_news(self, worksheet_name, data_to_spreadsheet, clear_sheet=False):
        
        # Only clear out spreadsheet not sent to the.com
        if clear_sheet:
            worksheet = self.get_unique_worksheet(worksheet_name)
        else:
            worksheet = self.sheet.worksheet(worksheet_name)

        # Put values in required format
        all_data = []
        dedupe_check = set()
        for news in data_to_spreadsheet:
            # double deduping temporarily
            if news['title'] in dedupe_check:
                continue
            dedupe_check.add(news['title'])
            if type(news['news_source']) == list:
                source = news['news_source'][0]
            else:
                source = news['news_source']

            # Get thumbnails, if None get default ones
            thumbnail = news['thumbnail'] if news[
                'thumbnail'] else config.default_thumbnail
            source_thumbnail = news['source_thumbnail'] if news[
                'source_thumbnail'] else config.default_source_thumbnail

            # Data saved to spreadsheet from DB
            news_list = [news['_id'], news['title'], news['summary'], source, 
                        news['date_time'], news['keywords'], thumbnail, source_thumbnail, news['strategy'], news['rank']]
            assert len(news_list) == config.row_length
            all_data.append(news_list) 

        # Col names
        cols = config.cols
        assert len(cols) == config.row_length
        all_data.insert(0, cols)

        worksheet.update(config.row_letters, all_data)
        worksheet.format(config.row_letters, {"wrapStrategy": "WRAP"})
        worksheet.freeze(rows=1)

        # Set custom column widths
        set_col_widths = zip(config.letters, config.col_widths)
        gf.set_column_widths(worksheet, list(set_col_widths)) 

        # Set custom foramtting
        headers = gf.cellFormat(
            backgroundColor=gf.color(0.85, 0.85,0.85),
            textFormat=gf.textFormat(bold=True, fontSize=12)
        )
            
        all_cells = gf.cellFormat(
            horizontalAlignment='CENTER',
            verticalAlignment='MIDDLE',
            textFormat=gf.textFormat(fontSize=11)
            )

        title = gf.cellFormat(
            backgroundColor=gf.color(0.95,0.95,0.95,0.15),
            textFormat=gf.textFormat(bold=True),
            horizontalAlignment='LEFT',
            )

        summary = gf.cellFormat(
            horizontalAlignment='LEFT'
            )

        source = gf.cellFormat(
            backgroundColor=gf.color(0.95,0.95,0.95,0.15),
            )

        gf.format_cell_ranges(worksheet, [
            (config.row_letters, all_cells), 
            ('B', title), 
            ('D', source),
            ('C', summary),
            ('1', headers)])
        
    def main(self):
        news_to_spreadsheet, reduced_news_to_spreadsheet = self.read_news_from_db()

        self.update_sheet_todays_news('climate_headlines', reduced_news_to_spreadsheet)
        db_and_out_logger.info('Data saved to Climate Headlines - sheet "{}". Total news today: {}'.format(
            'climate_headlines', len(reduced_news_to_spreadsheet)))
        
        self.update_sheet_todays_news('all_news_climate_headlines', news_to_spreadsheet, clear_sheet=True)
        db_and_out_logger.info('Data saved to Climate Headlines - sheet "{}". Total news today: {}'.format(
            'all_news_climate_headlines', len(news_to_spreadsheet)))
        