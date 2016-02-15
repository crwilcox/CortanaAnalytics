#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation 
# All rights reserved. 
# 
# Distributed under the terms of the MIT License
#-------------------------------------------------------------------------
import requests
from collections import namedtuple
from datetime import datetime

DATE_FORMAT = '%m/%d/%Y %H:%M:%S %p'

class AnomalyDetection:

    def __init__(self, account_key):
        '''
        account_key (str): account_key provided at https://datamarket.azure.com/account/keys
        '''
        self.auth = ('', account_key)

    def score(self, data, spike_detector_tukey_threshold=3, spike_detector_zscore_threshold=3):
        '''
        Given a list of tuples (datetime, float) this provides a list of results showing anomalies.

        data (list of tuples (datetime, float))
            In the form [(9/21/2014 11:05:00 AM, 3), (9/21/2014 11:10:00 AM,9.09), ...]"
        spike_detector_tukey_threshold (int, optional)
        spike_detector_zscore_threshold (int, optional)
        '''

        formatted_data = ""
        for i in data:
            date, value = i
            date_str = date.strftime(DATE_FORMAT)
            formatted_data += '{}={};'.format(date_str, value)
            
        params = "SpikeDetector.TuKeyThresh={}; SpikeDetector.ZscoreThresh={}".format(spike_detector_tukey_threshold, spike_detector_zscore_threshold)
        raw = self.score_raw(formatted_data, params)
        results = self._make_named_tuples(raw)
        return results

    def score_raw(self, data, params):
        '''
        Given a string of data and params, returns a string representing a table of data.

        data (str)
            In the form "9/21/2014 11:05:00 AM=3;9/21/2014 11:10:00 AM=9.09;9/21/2014 11:15:00 AM=0;"
        params (str)
            In the form "SpikeDetector.TukeyThresh=3; SpikeDetector.ZscoreThresh=3"

        Returns:
            A table in the form 
            "Time,Data,TSpike,ZSpike,Martingale values,Alert indicator,Martingale values(2),Alert indicator(2),;" +
            "9/21/2014 11:05:00 AM,3,0,0,-0.687952590518378,0,-0.687952590518378,0,;"

        '''

        API_URL = Uris.score
        response = requests.get(API_URL, params = { 'data':data, 'params' : params }, auth=self.auth)
        json_response = response.json()
        table = json_response['table']
        if len(table) > 2:
            table = table[1:-1] # trim '"' characters
        return table
    
    def _make_named_tuples(self, raw):
        '''
        Given the string from score_raw, this creates a list of named tuples.
        '''
        lines = raw.strip(';').split(';')
        results = []

        # Get Header / Data Format and Create Named Tuple
        #'Time,Data,TSpike,ZSpike,Martingale values,Alert indicator,Martingale values(2),Alert indicator(2),'
        # convert this line to be valid field names, have no spaces,etc
        cleansed_line = ""
        for i in lines[0].strip(',').split(','):
            i = i.strip()
            for j in ' ()':
                i = i.replace(j, '_')
            cleansed_line += i.strip('_') + ','
        anomaly = namedtuple('Anomaly', cleansed_line.strip(','))

        # Get Data and Create Named Tuples
        #  0                     1 2 3 4                  5 6                  7 
        # '9/21/2014 11:05:00 AM,3,0,0,-0.687952590518378,0,-0.687952590518378,0,'
        for i in lines[1:]:
            split = i.strip(',').split(',')
            a = anomaly(
                datetime.strptime(split[0], DATE_FORMAT), 
                float(split[1]),
                float(split[2]),
                float(split[3]),
                float(split[4]),
                float(split[5]),
                float(split[6]),
                float(split[7])
            )
            results.append(a)

        return results

class Uris:
    root = 'https://api.datamarket.azure.com/data.ashx/aml_labs/anomalydetection/v1/'
    score = root + 'Score'
  