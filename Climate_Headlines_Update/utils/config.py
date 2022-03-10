import os


# Build secrets
# MongoDB
uri = "mongodb+srv://{}:{}@freeclimatecluster.8eg0f.mongodb.net/myFirstDatabase?w=majority&ssl=true&ssl_cert_reqs=CERT_NONE&retrywrites=false".format(os.getenv("mongoazureusr"), os.getenv("mongoazurepwd"))
# Bing
bing_headers = {"Ocp-Apim-Subscription-Key":os.getenv("bingstudent")}
# Google sheets
gsheet = {
  "type": "service_account",
  "project_id": "climatemoneybot",
  "private_key_id": "5eccb212c944da35bfd77f3778b99706327acc99",
  "private_key": os.getenv('gsheetpk'),
  "client_email": "climatemoneybot@climatemoneybot.iam.gserviceaccount.com",
  "client_id": "115112158692493017800",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/climatemoneybot%40climatemoneybot.iam.gserviceaccount.com"
}

t_api_keys = (os.getenv("tapikey"), os.getenv("tapikeysecret"))
t_api_tokens = (os.getenv("taccesstoken"), os.getenv("taccesstokensecret"))

# Null document on spreadsheet/airtable
null_doc = {
    'null':{
        'title':'null',
        'summary':'null',
        'date':'null',
        'date_time':'null',
        'api':'null',
        'tweeted':'null',
        'news_source':'null',
        'keywords':'null',
        'query':'null',
        'thumbnail':'null',
        'source_thumbnail':'null',
        'strategy':'null'
        }
    }

# Default images if none found
default_thumbnail = 'https://images.unsplash.com/photo-1570358934836-6802981e481e?ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80'
default_source_thumbnail = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/google/298/rolled-up-newspaper_1f5de-fe0f.png'



limit_news_sent = 50
strategies = ['major_climate_outlets','other_major_outlets','remaining_outlets']

# Spreadsheet config
document_length = 13
row_length = 10
row_letters = 'A:J'
letters = ['A','B','C','D','E','F','G','H','I','J']
cols = ['URL', 'Title', 'Summary', 'Source', 'Date-Time', 'Keywords', 'Thumbnail', 'Source Thumbnail', 'Strategy', 'Rank']
col_widths = [
    250, # URL
    400, # Title
    500,  # Summary
    150, # Source
    120, # date-time
    100,  # keywords
    100, # thumbnail
    100, # provider thumbnail,
    100,  # strategy (for bookkeeping, not sent to the.com)
    20 # ranking (for bookkeeping, not sent to the.com)
    ]

    
# Date_times
time_format = '%Y-%m-%d %H:%M'
date_format = '%Y-%m-%d'
date_time_format = '%I:%M%p (%b %d %Y)'

### Aggregating Strategies

# Strategy 1: Major Climate Publications
# Show all news from major climate-specific sources (no keyword search)
rss_climate_specific = [
    ('Carbon Brief','https://feeds.feedburner.com/carbonbrief'),
    ('NASA Climate','https://climate.nasa.gov/news/rss.xml'),
    ('Reuters Environment','https://www.reutersagency.com/feed/?best-topics=environment&post_type=best'),
    ('New York Times Climate','https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml'),
    ('New York Times Energy','https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml'),
    ('Politico Energy & Environment','https://rss.politico.com/energy.xml'),
    ('The Guardian Climate Change','https://www.theguardian.com/environment/climate-change/rss'),
    ('The Guardian Energy','https://www.theguardian.com/environment/energy/rss'),
    ('The Guardian Environment','https://www.theguardian.com/environment/rss'),
    ('Nature Climate','http://feeds.nature.com/nclimate/rss/current'),
    ('TechCrunch Green','http://feeds.feedburner.com/TechCrunch/greentech'),
    ('BBC Climate and Environment','http://feeds.bbci.co.uk/news/science_and_environment/rss.xml'),
    ('UN Climate','https://news.un.org/feed/subscribe/en/news/topic/climate-change/feed/rss.xml'),
    ('US Energy Information Administration','https://www.eia.gov/rss/todayinenergy.xml'),
    ('EPA Climate Change','https://www.epa.gov/newsreleases/search/rss/subject/climate'),
    ('EPA Energy','https://www.epa.gov/newsreleases/search/rss/subject/energy'),
    ('EPA International','https://www.epa.gov/newsreleases/search/rss/subject/international'),
    ('The Global Warming Policy Foundation','https://www.thegwpf.org/feed/'),
    ('Canary Media','https://www.canarymedia.com/rss'),
    ('Job One for Humanity','https://www.joboneforhumanity.org/blog.rss'),
    ('Shell Climate Change','https://blogs.shell.com/feed/'),
    # ('Climate Change Dispatch','https://follow.it/climate-change-dispatch'), # Anti-climate
    ('Columbia Law Climate','http://blogs.law.columbia.edu/climatechange/feed/'),
    ('Union of Concerned Scientists','https://blog.ucsusa.org/category/global-warming/feed'),
    ('Environmental Defense Fund','http://blogs.edf.org/edfish/feed/')
]

# Strategy 2: Other Trusted Publications
# News from major sources, but source is not specifically climate - keyword search
# Both from feeds and from Bing News, but filter trusted Bing sources
rss_general = [    
    ('CNN Technology','http://rss.cnn.com/rss/cnn_tech.rss'),
    ('CNN Business','http://rss.cnn.com/rss/money_latest.rss'),
    ('CNN World','http://rss.cnn.com/rss/cnn_world.rss'),
    ('CNN Top Stories','http://rss.cnn.com/rss/cnn_topstories.rss'),
    ('Reuters Busines Finance','https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best'),
    ('New York Times World','https://rss.nytimes.com/services/xml/rss/nyt/World.xml'),
    ('New York Times Business','https://rss.nytimes.com/services/xml/rss/nyt/Business.xml'),
    # {'The Washington Times Business & Economy','https://www.washingtontimes.com/rss/headlines/news/business-economy/'),
    # {'The Washington Times Technology','https://www.washingtontimes.com/rss/headlines/culture/technology/'),
    ('Wired Business','https://www.wired.com/feed/category/business/latest/rss'),
    ('Wired Science','https://www.wired.com/feed/category/science/latest/rss'),
    ('Nature','http://feeds.nature.com/nature/rss/current'),
    ('Science Daily','http://feeds.sciencedaily.com/sciencedaily'),
    ('Utility Dive','https://www.utilitydive.com/feeds/news/'),
    ('TechCrunch Startups','http://feeds.feedburner.com/TechCrunch/startups'),
    ('TechCrunch Fundings','http://feeds.feedburner.com/TechCrunch/fundings-exits'),
    ('Australia Business Telegraph','https://www.dailytelegraph.com.au/business/breaking-news/rss'),
    ('Wall Street Journal: World','https://feeds.a.dj.com/rss/RSSWorldNews.xml'),
    ('Wall Street Journal: US Business','https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml'),
    ('Vegconomist','https://vegconomist.com/feed/'),
    ('Utility Dive','https://www.utilitydive.com/feeds/news/'),
    ('The Conversation','https://theconversation.com/us/environment/articles.atom'),
    # {'Wattsupwiththat','https://wattsupwiththat.com/feed/'),
    ('The Telegraph','https://www.telegraph.co.uk/news/rss.xml'),
    ('Skeptical Science','https://skepticalscience.com/feed.xml'),
    ('Commondreams','https://www.commondreams.org/rss.xml'),
    ('Greenpeace Australia','https://www.greenpeace.org.au/feed/')
    #{'International Energy Association','https://www.iea.org/news-and-events'}
]
trusted_bing_sources = [
    'Axios',
    'YAHOO!News',
    'The Hill',
    'The Hill on MSN.com',
    'San Francisco Chronicle',
    'Business Insider',
    'CNBC',
    'The Telegraph on MSN.com',
    'Washington Examiner',
    'Quartz',
    'Calgary Herald',
    'The Daily Telegraph',
    'Quartz on MSN.com',
    'South China Morning Post on MSN.com',
    'New York Post',
    'Electrek',
    'Business Weekly',
    'Reuters'
]

# Strategy 3: Climate All Around the web
# "everything else", i.e. Bing News results not from trusted sources

# Keywords
save_if_this_word_in_title = [
    # narrower list
    'climate', 
    'carbon', 
    'offset', 
    'hydrogen', 
    'sustainab',
    'dioxide', 
    'batteries', 
    'electrification', 
    # 'environment', 
    #'emission', 
    'greenhouse', 
    'methane', 
    'acidification', 
    'solar', 
    'electric vehicle', 
    #'energy',
    'offshore', 
    #'electric', 
    #'rise', 
    'sea level', 
    'coal', 
    'natural gas', 
    #'nuclear', 
    'glacier', 
    'activist',
    #'plastic', 
    'fracking', 
    'e.p.a.', 
    #'earth', 
    #'planet', 
    'environmental', 
    'cop26', 
    # 'endangered', 
    'renewable',
    # 'greta', 
    # 'pipeline', 
    'wildfire',
    # 'heating', 
    # 'warming',
    # 'nature'
    #'epa', 'esg', 'green', 'gsg', 'fuel'
]

use_this_word_for_search = [
    # broader list
    'climate', 
    'climate change',
    'global warming',
    'carbon', 
    'co2',
    'climate tech',
    'renewable',
    'offset', 
    'hydrogen', 
    'sustainable', 
    'dioxide', 
    'batteries', 
    'electrification', 
    'environment', 
    'emission', 
    'greenhouse', 
    'methane', 
    'acidification', 
    'solar', 
    'electric vehicle', 
    'energy',
    'offshore', 
    #'electric', 
    #'rise', 
    'sea level', 
    'coal', 
    'natural gas', 
    'nuclear', 
    'glacier', 
    'activist',
    #'plastic', 
    'fracking', 
    'e.p.a.', 
    #'earth', 
    #'planet', 
    'sutainability',
    'environmental', 
    'cop26', 
    'endangered', 
    # 'greta', 
    # 'pipeline', 
    'wildfire',
    'heating',
    # 'nature'
    #'epa', 'esg', 'green', 'gsg', 'fuel'
]