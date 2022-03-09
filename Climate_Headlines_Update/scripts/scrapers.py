import re
import requests
import logging
import time
import feedparser
from datetime import datetime, timedelta
import html2text
import sys,os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import config
from utils.helpers import NewsTextExtractor as extractor
from webpreview import web_preview, URLUnreachable, InvalidURL, URLNotFound
import time

# create logger
scrapers_logger = logging.getLogger('daily_news_updater.scrapers')

class BingNewsScraper():

    def __init__(self, date_yesterday):
        self.date_yesterday = date_yesterday
        self.since = datetime.timestamp(datetime.strptime(self.date_yesterday, config.date_format))
        self.date_today = datetime.today().strftime(config.date_format)
        self.url = "https://api.bing.microsoft.com/v7.0/news/search"
        self.headers = config.bing_headers
        self.count = 100

    def get_news_one_keyword(self, keyword):
        scrapers_logger.info('Querying Bing News to get news about "{}" from {} to {}'.format(keyword, self.date_yesterday, self.date_today))
        gather_climate_news = {}
        offset = 0

        page_number = 0
        while True:
            page_number += 1
            # https://docs.microsoft.com/https://docs.microsoft.com/en-us/rest/api/cognitiveservices-bingsearch/bing-news-api-v7-referenceen-us/rest/api/cognitiveservices-bingsearch/bing-news-api-v7-reference
            params  = {"q": keyword, 'category':'Business', 'freshness':'Day',
                        'count':self.count, 'offset':offset, 'since':self.since, 'sortBy':'date'}
            while True:
                try:
                    response = requests.get(self.url, headers=config.bing_headers, params=params)
                    response.raise_for_status()
                    break
                except requests.exceptions.ConnectionError as e:
                    scrapers_logger.info('Requests error: {}. Retrying...'.format(e))

            search_results = response.json()
            
            if search_results['value']:
                scrapers_logger.debug('{} estimated results for Daily freshness'.format(
                    search_results['totalEstimatedMatches']))
                scrapers_logger.info('Processing {} news'.format(len(search_results['value'])))
                for i,new in enumerate(search_results['value']):
                    keywords = [keyword for keyword in config.save_if_this_word_in_title if keyword.lower() in new['name']]
                    if not keywords:
                        # This is not climate news
                        continue
                    # Get source
                    if type(new['provider'][0]['name']) == list:
                        source = new['provider'][0]['name'][0]
                    else:
                        source = new['provider'][0]['name']
                    # Set strategy and check if source trusted
                    strategy = 'other_major_outlets' if source in config.trusted_bing_sources else 'remaining_outlets'
                    url = new['url']
                    scrapers_logger.debug(f'{i} {url}')
                    # get metadata
                    # summary, thumbnail = BSExtracter(url).main()
                    try:
                        _, summary, thumbnail = web_preview(new['url'], parser="html.parser", timeout=10)
                        # If webpreview failed, extracting text will fail (but not throw error for some reason)
                        text = extractor().extract_text(url)
                    except (URLUnreachable, InvalidURL, URLNotFound, KeyError, requests.exceptions.ChunkedEncodingError) as e:
                        scrapers_logger.info('Error {}. WebPreview failed'.format(e))
                        summary, thumbnail, text = None, None, None
                    if not summary:
                        summary = new['description']
                    if not thumbnail:
                        try:
                            thumbnail = new['image']['thumbnail']['contentUrl']
                        except KeyError:
                            thumbnail = None
                    try:
                        prov_thumbnail = new['provider'][0]['image']['thumbnail']['contentUrl']
                    except KeyError:
                        prov_thumbnail = None
                    date_time = datetime.fromisoformat(new['datePublished'][:-2]).strftime(config.date_time_format)
                    date = datetime.fromisoformat(new['datePublished'][:-2]).strftime(config.date_format)
                    scrapers_logger.info('Getting text for "{}"'.format(url))
                    # Key is the url
                    new_dict = {url:{
                                    'title':new['name'],
                                    'news_source':source,
                                    'api':'Bing News',
                                    'date':date,
                                    'date_time':date_time,
                                    'tweeted':'no',
                                    'query':keyword,
                                    'keywords':', '.join(keywords),
                                    'summary':html2text.html2text(summary),
                                    'source_thumbnail':prov_thumbnail,
                                    'thumbnail':thumbnail,
                                    'strategy':strategy,
                                    'text':text
                                    }}
                    assert len(new_dict[url]) == config.document_length
                    gather_climate_news.update(new_dict)
                    scrapers_logger.debug('New piece of news: \n {}'.format(new['name']))
                scrapers_logger.debug('End of batch------')
                offset = page_number * self.count
                scrapers_logger.info('{} queries performed'.format(offset))
                time.sleep(5)
                return gather_climate_news
                # Only make 500 queries, prob not important news after that
                if search_results['totalEstimatedMatches'] < offset or offset > 500:
                    scrapers_logger.info('====Total Bing climate news: {}===='.format(len(gather_climate_news)))
                    return gather_climate_news
            else:
                scrapers_logger.info('No news returned for "{}"'.format(keyword))
                gather_climate_news = []
                return {}

class FeedReader():
    '''A class that initiates a FeedReader object. It's used to 
    get all news in a specific timeframe, from the RRS sources 
    that are passed to it.
    
    Attributes:
    today: Today's date in str format, define in cofig
    yesterday: Yesterday's date in str format, define in config
    recent: News published in these 2 dates will be returned by the class

    Methods:
    get_feed_new_news: Gets any news published in recent dates and returns 
        some data about them
    
    '''
    def __init__(self):
        self.today = datetime.today().strftime(config.date_format)
        self.yesterday = (datetime.today() - timedelta(days=1)).strftime(config.date_format)
        self.recent = [self.today, self.yesterday]

    def get_news_one_feed(self, feed_tup: tuple, strategy: str, keyword_title=False) -> dict:
        '''For the given feed (RSS), return some data for news published in recent dates
        
        Arguments:
            feed_tup: a tuple with key feed_name and values feed_url, to search in
            keyword_title_search: if true, news returned will be filtered and only
                the ones with a word in the keyword_title list in config will
                actually be returned
            
        Returns:
            feed_recent_news: a dict with data for all recent news in specific feed.
            (See sample structure below)
            
        '''

        feed_name, feed_url = feed_tup
        parsed_recent_news = {} # save relevant news here
        parsed = feedparser.parse(feed_url) # parsed feed with all news
        if parsed['status'] > 200:
            scrapers_logger.warning('Error: Feed {} returned status {}'.format(feed_name, parsed['status']))
        news = parsed['entries']
        scrapers_logger.info('{} Read: {} news total (no date or keyword filter applied)'.format(feed_name, len(news)))
        for i, new in enumerate(news):
            # Get url (key for results dict)
            try:
                url = new['feedburner_origlink']
                if 'http' not in url:
                    url = new['link']
                    if 'http' not in url:
                        url = new['id']
            except KeyError: # no 'id' field
                url = new['link']
            scrapers_logger.debug(f'{i} {url}')
            # Get date (for mongo) and date_time (for website)
            try:
                date = time.strftime(config.date_format, new['published_parsed'])
                date_time = time.strftime(config.date_time_format, new['published_parsed'])
            except (KeyError, TypeError): # 'published_parsed' not in the response or
                try:
                    date = time.strftime(config.date_format, new['published_parsed'])
                    date_time = time.strftime(config.date_format, new['published_parsed'])
                except (KeyError, TypeError):
                    try:
                        dt = datetime.strptime(re.search('\d{4}/\d{2}/\d{2}', url).group(), '%Y/%m/%d')
                        date = dt.strftime(config.date_format)
                        date_time = dt.strftime(config.date_time_format)
                    except (AttributeError, TypeError): #date couldn't be parsed from url
                        scrapers_logger.info('Date unknown, not saving: {}'.format(new['title']))
                        continue # not saving as we don't have date
            
            
            # Only add news not in the dict already
            if url in parsed_recent_news:
                continue
            # Only add if date is today or yesterday
            if date not in self.recent:
                scrapers_logger.debug('Too old: "{}"'.format(new['title']))
                continue
            
            # if Stragegy 2, filter by keyword
            keywords = [keyword for keyword in config.save_if_this_word_in_title if keyword.lower() in new['title'].lower()]
            if keyword_title:
                if not keywords:
                    # don't save this news because it didn't have any of the keywords
                    scrapers_logger.debug('Not news about climate: "{}"'.format(new['title']))
                    continue

            # Extract metadata using web_preview
            # summary, thumbnail = BSExtracter(url) # custom extraction, not used
            try:
                _, summary, thumbnail = web_preview(url, parser="html.parser", timeout=10)
            except (URLUnreachable, InvalidURL, KeyError) as e:
                scrapers_logger.info('Error {}. WebPreview failed'.format(e))
                summary, thumbnail = None, None
            if not summary:
                summary = new['summary']
            if not thumbnail:
                thumbnail = None
            
            text = extractor().extract_text(url)
            new_dict = {url:
                    {
                    'title':new['title'],
                    'summary':html2text.html2text(summary.split('<div')[0]),
                    'date':date,
                    'date_time':date_time,
                    'api':'FeedParser',
                    'tweeted':'no',
                    'news_source':parsed['feed']['title'],
                    'keywords':', '.join(keywords),
                    'query':'',
                    'thumbnail':thumbnail,
                    'source_thumbnail':None,
                    'strategy':strategy,
                    'text':text
                    }
                }
            assert len(new_dict[url]) == config.document_length
            parsed_recent_news.update(new_dict)
            scrapers_logger.debug('Relevant news saved: "{}"'.format(new['title']))

        if len(parsed_recent_news) > 0:
            scrapers_logger.info('{} Saved: {} news'.format(feed_name, len(parsed_recent_news)))
        return parsed_recent_news

