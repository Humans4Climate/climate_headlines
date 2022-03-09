from bs4 import BeautifulSoup as bs
import requests

class NewsTextExtractor():

    def __init__(self):
        pass

    def extract_text(self, url):
                
        resp = requests.get(url, verify=False)
        soup = bs(resp.text, features="html.parser")
        text = soup.get_text()
        text = text.replace('\n\n','').replace('\n',' ')
        return text
    