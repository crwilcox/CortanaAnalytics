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
        text_blocks ([{"Text":'string' Id:0},...])
        '''
        data = { "Inputs" : text_blocks }
        API_URL = Uris.get_sentiment_batch
        response = requests.post(API_URL, json=data, auth=self.auth)
        return response.json()['SentimentBatch']

    def get_key_phrases(self, text):
        '''
        text (str)
        '''
        API_URL = Uris.get_key_phrases
        response = requests.get(API_URL, params = { 'text':text }, auth=self.auth)
        return response.json()['KeyPhrases']

    def get_key_phrases_batch(self, text_blocks):
        '''
        text_blocks ([{"Text":'string' Id:0},...])
        '''
        data = { "Inputs" : text_blocks }
        API_URL = Uris.get_key_phrases_batch
        response = requests.post(API_URL, json=data, auth=self.auth)
        return response.json()['KeyPhrasesBatch']

    def get_language(self, text, number_of_languages_to_detect=1):
        '''
        text (str)
        '''
        API_URL = Uris.get_language
        params = { 'text':text, 'NumberOfLanguagesToDetect':number_of_languages_to_detect }
        response = requests.get(API_URL, params = params, auth=self.auth)
        return response.json()['DetectedLanguages']

    def get_language_batch(self, text_blocks):
        '''
        text_blocks ([{"Text":'string' Id:0},...])
        '''
        data = { "Inputs" : text_blocks }
        API_URL = Uris.get_language_batch
        response = requests.post(API_URL, json=data, auth=self.auth)
        print(response.json())
        return response.json()['LanguageBatch']

class Uris:
    root = 'https://api.datamarket.azure.com/data.ashx/amla/text-analytics/v1/'
    get_sentiment = root + 'GetSentiment'
    get_sentiment_batch = root + 'GetSentimentBatch'
    get_key_phrases = root + 'GetKeyPhrases'
    get_key_phrases_batch = root + 'GetKeyPhrasesBatch'
    get_language = root + 'GetLanguage'
    get_language_batch = root + 'GetLanguageBatch'