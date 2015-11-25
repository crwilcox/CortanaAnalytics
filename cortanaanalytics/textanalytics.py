import requests

class TextAnalytics:
    def __init__(self, account_key):
        '''
        account_key (str): account_key provided at https://datamarket.azure.com/account/keys
        '''
        self.auth = ('', account_key)

    def get_sentiment(self, text):
        '''
        text (str)
        '''
        API_URL = Uris.get_sentiment
        response = requests.get(API_URL, params = { 'text':text }, auth=self.auth)
        return response.json()['Score']

    def get_sentiment_batch(self, text_blocks):
        '''
        text_blocks (str[])
        '''
        data = { "Inputs" : text_blocks }
        API_URL = Uris.get_sentiment_batch
        response = requests.post(API_URL, json=data, auth=self.auth)
        return response.json()['SentimentBatch']

    # get key phrases
    # get language
    # get key phrases batch
    # get language batch

class Uris:
    root = 'https://api.datamarket.azure.com/data.ashx/amla/text-analytics/v1/'
    get_sentiment = root + 'GetSentiment'
    get_sentiment_batch = root + 'GetSentimentBatch'
