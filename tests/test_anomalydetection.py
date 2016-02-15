#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation 
# All rights reserved. 
# 
# Distributed under the terms of the MIT License
#-------------------------------------------------------------------------
import unittest
from cortanaanalytics.anomalydetection import AnomalyDetection, Uris
import httpretty
import os
from datetime import datetime
from time import sleep

class AnomalyDetectionTests(unittest.TestCase):
    
    def setUp(self):
        # These values are fake.  This is fine since we don't send requests
        # to the live service for tests.  If you want to run against a live setup
        # modify these variables and comment out the httpretty decorator on the test.
        self.key = '1abCdEFGh/ijKlmN/opq234r56st/UvWXYZabCD7EF8='
        return super().setUp()

    @httpretty.activate
    def test_score_raw(self):
        test_data = "9/21/2014 11:05:00 AM=3;9/21/2014 11:10:00 AM=9.09;9/21/2014 11:15:00 AM=0;"
        test_params = "SpikeDetector.TukeyThresh=3; SpikeDetector.ZscoreThresh=3"
        uri = '{}?data=%27{}%27&params=%27{}%27'.format(Uris.score, test_data, test_params)
        httpretty.register_uri(httpretty.GET, uri, body=TestData.score_returns)
        
        ad = AnomalyDetection(self.key)

        result = ad.score_raw(test_data, test_params)
        expected = '"Time,Data,TSpike,ZSpike,Martingale values,Alert indicator,Martingale values(2),Alert indicator(2),;9/21/2014 11:05:00 AM,3,0,0,-0.687952590518378,0,-0.687952590518378,0,;9/21/2014 11:10:00 AM,9.09,0,0,-1.07030497733224,0,-0.884548154298423,0,;9/21/2014 11:15:00 AM,0,0,0,-1.05186237440962,0,-1.173800281031,0,;"'
        self.assertEqual(result['table'], expected)
    
    @httpretty.activate
    def test_score(self):
        httpretty.register_uri(httpretty.GET, Uris.score, body=TestData.score_returns)

        ad = AnomalyDetection(self.key)


        test_data = [
                        (datetime(2014, 9, 21, 11, 5, 0), 3),
                        (datetime(2014, 9, 21, 11, 10, 0), 9.09),
                        (datetime(2014, 9, 21, 11, 15, 0), 0)
                    ]
        result = ad.score(test_data)
        #Anomaly(
        # Time=datetime.datetime(2014, 9, 21, 11, 5), Data=3.0, TSpike=0.0, ZSpike=0.0, 
        # Martingale_values=-0.687952590518378, Alert_indicator=0.0, 
        # Martingale_values_2=-0.687952590518378, Alert_indicator_2=0.0)
        self.assertEqual(result[0].Time, datetime(2014,9,21,11,5))
        self.assertEqual(result[0].Data, 3)
        self.assertEqual(result[0].TSpike, 0)
        self.assertEqual(result[0].ZSpike, 0)
        self.assertEqual(result[0].Martingale_values, -0.687952590518378)
        self.assertEqual(result[0].Alert_indicator, 0)
        self.assertEqual(result[0].Martingale_values_2, -0.687952590518378)
        self.assertEqual(result[0].Alert_indicator_2, 0)

class TestData():
    score_returns = '''{
"odata.metadata":"https://api.datamarket.azure.com/data.ashx/aml_labs/anomalydetection/v1/$metadata#Microsoft.CloudML.ScoreResult","table":"\\"Time,Data,TSpike,ZSpike,Martingale values,Alert indicator,Martingale values(2),Alert indicator(2),;9/21/2014 11:05:00 AM,3,0,0,-0.687952590518378,0,-0.687952590518378,0,;9/21/2014 11:10:00 AM,9.09,0,0,-1.07030497733224,0,-0.884548154298423,0,;9/21/2014 11:15:00 AM,0,0,0,-1.05186237440962,0,-1.173800281031,0,;\\""
}'''