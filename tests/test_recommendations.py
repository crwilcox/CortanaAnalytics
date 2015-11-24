import unittest
from cortanaanalytics.recommendations  import Recommendations, Uris, BuildStatus, CatalogItem
import httpretty
import os
from datetime import datetime
from time import sleep
import config

class RecommendationServiceTests(unittest.TestCase):
    
    def setUp(self):
        # These values are fake.  This is fine since we don't send requests
        # to the live service for tests.  If you want to run against a live setup
        # modify these variables and comment out the httpretty decorator on the test.
        self.email = 'email@outlook.com'
        self.key = '1abCdEFGh/ijKlmN/opq234r56st/UvWXYZabCD7EF8='
        return super().setUp()

    @httpretty.activate
    def test_create_model(self):
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/CreateModel?modelName=%27testtest1%27&apiVersion=%271.0%27'        
        httpretty.register_uri(httpretty.POST, uri, body=TestData.create_model_returns)

        rs = RecommendationService(self.email, self.key)
        model_id = rs.create_model('testtest1')
        self.assertEqual(model_id, 'd5c7273b-2228-4cf4-99b1-9966e28b143a')
    
    @httpretty.activate
    def test_import_file_catalog(self):
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ImportCatalogFile?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&filename=%27catalog_small.txt%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.POST, uri, body=TestData.import_file_catalog_returns)

        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'

        resources_dir = os.path.join(os.getcwd(), 'tests', 'resources')
        report = rs.import_file(model_id, os.path.join(resources_dir, 'catalog_small.txt'), Uris.import_catalog)

        self.assertEqual('8', report.line_count)
        self.assertEqual('4', report.error_count)

    @httpretty.activate
    def test_import_file_usage(self):
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ImportUsageFile?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&filename=%27usage_small.txt%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.POST, uri, body=TestData.import_file_usage_returns)

        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'

        resources_dir = os.path.join(os.getcwd(), 'tests', 'resources')
        report = rs.import_file(model_id, os.path.join(resources_dir, 'usage_small.txt'), Uris.import_usage)

        self.assertEqual('38', report.line_count)
        self.assertEqual('5', report.error_count)
    
    @httpretty.activate
    def test_build_recommendation_model(self):
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/BuildModel?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&userDescription=%27build of 20150518141414%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.POST, uri, body=TestData.build_model_returns)

        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'

        now = datetime(2015, 5, 18, 14, 14, 14)
        build_id = rs.build_recommendation_model(model_id, "build of " + now.strftime('%Y%m%d%H%M%S'))
        self.assertEqual(build_id, '1514886')

    @httpretty.activate
    def test_build_model_monitor(self):
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/GetModelBuildsStatus?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&onlyLastBuild=False&apiVersion=%271.0%27'
        building_1 = httpretty.Response(TestData.build_model_monitor_building_1_response)
        building_2 = httpretty.Response(TestData.build_model_monitor_building_2_response)
        success = httpretty.Response(TestData.build_model_monitor_success_response)
        httpretty.register_uri(httpretty.GET, uri, responses = [building_1, building_2, success])   
        
        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'
        build_id = '1514886'

        building_count = 0
        success_count = 0

        print("\nMonitoring build '{}'", build_id)
        # monitor the current triggered build
        status = rs.wait_for_build(model_id, build_id)

        self.assertEqual(status, BuildStatus.success, 'We should have succeeded')

    @httpretty.activate
    def test_update_model_description(self):
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/UpdateModel?id=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.PUT, uri, body=TestData.update_model_response)
        
        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'
        build_id = '1514886'

        rs.update_model(model_id, "book model", build_id)
    
    @httpretty.activate
    def test_get_recommendations_single(self):
        responses = [ 
            httpretty.Response(TestData.invoke_recommendations_single_1), 
            httpretty.Response(TestData.invoke_recommendations_single_2) ]

        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ItemRecommend?.*'
        httpretty.register_uri(httpretty.GET, uri, responses = responses)
      
        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'

        # get recommendations. This item data was extracted from the catalog file in the resource folder.
        seed_items = [
            CatalogItem("2406E770-769C-4189-89DE-1C9283F93A96", "Clara Callan"),
            CatalogItem("552A1940-21E4-4399-82BB-594B46D7ED54", "Restraint of Beasts")]

        results_1 = rs.get_recommendation(model_id, [seed_items[0].id], 10)
        results_2 = rs.get_recommendation(model_id, [seed_items[1].id], 10)

        self.assertEqual(len(results_1), 1)
        self.assertEqual(results_1[0].id, seed_items[1].id)
        self.assertEqual(len(results_2), 0)
    
    @httpretty.activate
    def test_get_recommendations_list(self):
        
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ItemRecommend?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&itemIds=%272406e770-769c-4189-89de-1c9283f93a96,552a1940-21e4-4399-82bb-594b46d7ed54%27&numberOfResults=10&includeMetadata=False&apiVersion=%271.0%27'

        httpretty.register_uri(httpretty.GET, uri, TestData.invoke_recommendations_list)

        rs = RecommendationService(self.email, self.key)
        model_id = 'd5c7273b-2228-4cf4-99b1-9966e28b143a'

        # get recommendations. This item data was extracted from the catalog file in the resource folder.
        seed_items = [
            CatalogItem("2406e770-769c-4189-89de-1c9283f93a96", "Clara Callan"),
            CatalogItem("552a1940-21e4-4399-82bb-594b46d7ed54", "Restraint of Beasts")]

        items = rs.get_recommendation(model_id, [i.id for i in seed_items], 10)
        self.assertEqual(len(items), 0)

    def _invoke_recommendations(self, rs, model_id, seed_items, use_list=True):
        """
        A helper that prints out recommendations. See above tests for 
        more info on how to do single recommendation requests.

        Args:
            model_id (str): The model id.
            seed_items (list str): A list of item to get recommendation.
            use_list (bool): 
                If true all the items are used to get a recommendation on the 
        """
        if use_list:
            items = rs.get_recommendation(model_id, [i.id for i in seed_items], 10)
            print("\tRecommendations for [{0}]".format('],['.join(str(element) for element in seed_items)))
            for item in items:
                print("\t {0}", item)
        else:
            for item in seed_items:
                reco_items = rs.get_recommendation(model_id, [ item.id ], 10)
                print("Recommendation for '{}'".format(item))
                for reco_item in reco_items:
                    print("\t {}".format(reco_item))
                print("\n")

    @httpretty.activate
    def test_e2e(self):
        # mock connections for the test. Below sample will work if this is commented out.
        self.mock_connections()

        model_name = 'testtest1'

        rs = RecommendationService(self.email, self.key)

        # Create a model container
        print('\nCreating model container {}...', model_name)
        model_id = rs.create_model('testtest1')
        print("\yModel '{}' created with ID: {}".format(model_name, model_id))

        # Import data to the container
        print('\nImporting catalog and usage data...')
        resources_dir = os.path.join(os.getcwd(), 'tests', 'resources')
        print('\timport catalog...')
        report = rs.import_file(model_id, os.path.join(resources_dir, 'catalog_small.txt'), Uris.import_catalog)
        print('\t{}'.format(report))

        print('\timport usage...')
        report = rs.import_file(model_id, os.path.join(resources_dir, "usage_small.txt"), Uris.import_usage);
        print('\t{}'.format(report))

        # Trigger a build to produce a recommendation model
        print("\nTrigger build for model '{0}'", model_id)
        build_id = rs.build_recommendation_model(model_id, "build of " + datetime.now().strftime('%Y%m%d%H%M%S'))
        print("\ttriggered build id '{0}'", build_id)

        print("\nMonitoring build '{}'", build_id)
        # monitor the current triggered build
        status = rs.wait_for_build(model_id, build_id)
        print("\n\tBuild {0} ended with status {1}", build_id, status)

        if status != BuildStatus.success:
            print("Build {0} did not end successfully, the sample app will stop here.", build_id)
            return
        
        #The below api is more meaningful when you want to give a cetain build id to be an active build.
        #currently this app has a single build which is already active.
        print("\nUpdating model description to 'book model' and set active build")

        rs.update_model(model_id, "book model", build_id)
        # we deliberately add delay in order to propagate the model updates from the build...
        print("\nWaiting for propagation of the built model...")
        sleep(5)

        print("\nGetting some recommendations...")
        # get recommendations. This item data was extracted from the catalog file in the resource folder.
        seed_items = [
            CatalogItem("2406e770-769c-4189-89de-1c9283f93a96", "Clara Callan"),
            CatalogItem("552a1940-21e4-4399-82bb-594b46d7ed54", "Restraint of Beasts")]
        print("\t for single seed item")
        # show usage for single item
        self._invoke_recommendations(rs, model_id, seed_items, False)

        print("\n\n\t for a set of seed item")
        # show usage for a list of items
        self._invoke_recommendations(rs, model_id, seed_items, True)

    def mock_connections(self):
        #   model_id = rs.create_model('testtest1')
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/CreateModel?modelName=%27testtest1%27&apiVersion=%271.0%27'        
        httpretty.register_uri(httpretty.POST, uri, body=TestData.create_model_returns)
        
        # report = rs.import_file(model_id, os.path.join(resources_dir, 'catalog_small.txt'), Uris.import_catalog)
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ImportCatalogFile?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&filename=%27catalog_small.txt%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.POST, uri, body=TestData.import_file_catalog_returns)

        #   report = rs.import_file(model_id, os.path.join(resources_dir, "usage_small.txt"), Uris.import_usage);
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ImportUsageFile?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&filename=%27usage_small.txt%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.POST, uri, body=TestData.import_file_usage_returns)

        #   build_id = rs.build_model(model_id, "build of " + datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/BuildModel?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&userDescription=%27build of 20150518141414%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.POST, uri, body=TestData.build_model_returns)

        #   status = rs.get_build_status(model_id, build_id)
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/GetModelBuildsStatus?modelId=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&onlyLastBuild=False&apiVersion=%271.0%27'
        building_1 = httpretty.Response(TestData.build_model_monitor_building_1_response)
        building_2 = httpretty.Response(TestData.build_model_monitor_building_2_response)
        success = httpretty.Response(TestData.build_model_monitor_success_response)
        httpretty.register_uri(httpretty.GET, uri, responses = [building_1, building_2, success])   

        #   rs.update_model(model_id, "book model", build_id)
        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/UpdateModel?id=%27d5c7273b-2228-4cf4-99b1-9966e28b143a%27&apiVersion=%271.0%27'
        httpretty.register_uri(httpretty.PUT, uri, body=TestData.update_model_response)
        
        #   rs.invoke_recommendations(model_id, seed_items, false)
        #   rs.invoke_recommendations(model_id, seed_items, true)
        responses = [ 
            httpretty.Response(TestData.invoke_recommendations_single_1), 
            httpretty.Response(TestData.invoke_recommendations_single_2),
            httpretty.Response(TestData.invoke_recommendations_list) ]

        uri = 'https://api.datamarket.azure.com/amla/recommendations/v2/ItemRecommend?.*'
        httpretty.register_uri(httpretty.GET, uri, responses = responses)

class TestData():
    create_model_returns = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/CreateModel" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Create A New Model</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/CreateModel?modelName='testtest1'&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T18:16:52Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/CreateModel?modelName='testtest1'&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/CreateModel?modelName='testtest1'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">CreateANewModelEntity2</title>
              <updated>2015-05-18T18:16:52Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/CreateModel?modelName='testtest1'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:Id m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:Id>
                    <d:Name m:type="Edm.String">testtest1</d:Name>
                    <d:Date m:type="Edm.String">5/18/2015 6:16:43 PM</d:Date>
                    <d:Status m:type="Edm.String">Created</d:Status>
                    <d:HasActiveBuild m:type="Edm.String">false</d:HasActiveBuild>
                    <d:BuildId m:type="Edm.String">-1</d:BuildId>
                    <d:Mpr m:type="Edm.String">0</d:Mpr>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:Description m:type="Edm.String">-</d:Description>
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    import_file_catalog_returns = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportCatalogFile" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Import catalog file</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportCatalogFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='catalog_small.txt'&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T20:51:48Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportCatalogFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='catalog_small.txt'&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportCatalogFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='catalog_small.txt'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">ImportCatalogFileEntity2</title>
              <updated>2015-05-18T20:51:48Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportCatalogFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='catalog_small.txt'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:LineCount m:type="Edm.String">8</d:LineCount>
                    <d:ErrorCount m:type="Edm.String">4</d:ErrorCount>
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    import_file_usage_returns = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportUsageFile" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Add bulk usage data (usage file)</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportUsageFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='usage_small.txt'&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T21:06:41Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportUsageFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='usage_small.txt'&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportUsageFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='usage_small.txt'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">AddBulkUsageDataUsageFileEntity2</title>
              <updated>2015-05-18T21:06:41Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ImportUsageFile?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;filename='usage_small.txt'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:LineCount m:type="Edm.String">38</d:LineCount>
                    <d:ErrorCount m:type="Edm.String">5</d:ErrorCount>
                    <d:FileId m:type="Edm.String">2f009450-1d18-40d7-b9f1-c1ca3b6fc7c6</d:FileId>
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    build_model_returns = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Build a Model with RequestBody</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build of 20150518142732'&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T21:27:42Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build%20of%2020150518142732'&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build of 20150518142732'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">BuildAModelEntity2</title>
              <updated>2015-05-18T21:27:42Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build%20of%2020150518142732'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:Id m:type="Edm.String">1514886</d:Id>
                    <d:UserName m:type="Edm.String" />
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:Type m:type="Edm.String">Recommendation</d:Type>
                    <d:CreationTime m:type="Edm.String">2015-05-18T21:27:36.557</d:CreationTime>
                    <d:Progress_BuildId m:type="Edm.String">1514886</d:Progress_BuildId>
                    <d:Progress_ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:Progress_ModelId>
                    <d:Progress_UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:Progress_UserName>
                    <d:Progress_IsExecutionStarted m:type="Edm.String">false</d:Progress_IsExecutionStarted>
                    <d:Progress_IsExecutionEnded m:type="Edm.String">false</d:Progress_IsExecutionEnded>
                    <d:Progress_Percent m:type="Edm.String">0</d:Progress_Percent>
                    <d:Progress_StartTime m:type="Edm.String">0001-01-01T00:00:00</d:Progress_StartTime>
                    <d:Progress_EndTime m:type="Edm.String">0001-01-01T00:00:00</d:Progress_EndTime>
                    <d:Progress_UpdateDateUTC m:type="Edm.String" />
                    <d:Status m:type="Edm.String">Queued</d:Status>
                    <d:Key1 m:type="Edm.String">UseFeaturesInModel</d:Key1>
                    <d:Value1 m:type="Edm.String">false</d:Value1>
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    build_model_monitor_building_1_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Build a Model with RequestBody</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build of 20150518141414'&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T22:25:33Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build%20of%2020150518141414'&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build of 20150518141414'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">BuildAModelEntity2</title>
              <updated>2015-05-18T22:25:33Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/BuildModel?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;userDescription='build%20of%2020150518141414'&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:Id m:type="Edm.String">1514886</d:Id>
                    <d:UserName m:type="Edm.String" />
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:Type m:type="Edm.String">Recommendation</d:Type>
                    <d:CreationTime m:type="Edm.String">2015-05-18T22:25:28.613</d:CreationTime>
                    <d:Progress_BuildId m:type="Edm.String">1514886</d:Progress_BuildId>
                    <d:Progress_ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:Progress_ModelId>
                    <d:Progress_UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:Progress_UserName>
                    <d:Progress_IsExecutionStarted m:type="Edm.String">false</d:Progress_IsExecutionStarted>
                    <d:Progress_IsExecutionEnded m:type="Edm.String">false</d:Progress_IsExecutionEnded>
                    <d:Progress_Percent m:type="Edm.String">0</d:Progress_Percent>
                    <d:Progress_StartTime m:type="Edm.String">0001-01-01T00:00:00</d:Progress_StartTime>
                    <d:Progress_EndTime m:type="Edm.String">0001-01-01T00:00:00</d:Progress_EndTime>
                    <d:Progress_UpdateDateUTC m:type="Edm.String" />
                    <d:Status m:type="Edm.String">Queued</d:Status>
                    <d:Key1 m:type="Edm.String">UseFeaturesInModel</d:Key1>
                    <d:Value1 m:type="Edm.String">false</d:Value1>
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    build_model_monitor_building_2_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Get builds status of a model</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T22:26:18Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:26:18Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">false</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514886</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Building</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">100</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 10:25:33 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String" />
                    <d:ExecutionTime m:type="Edm.String">00:00:44</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">true</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String">Modeling</d:ProgressStep>
                 </m:properties>
              </content>
           </entry>
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=1&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:26:18Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=1&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514885</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 9:55:33 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 9:56:56 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:01:22</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=2&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:26:18Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=2&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514884</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 9:52:23 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 9:53:44 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:01:21</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=3&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:26:18Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=3&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514882</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 9:27:42 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 9:28:41 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:00:58</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    build_model_monitor_success_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Get builds status of a model</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T22:29:05Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:29:05Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514886</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 10:25:33 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 10:26:56 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:01:22</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=1&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:29:05Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=1&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514885</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 9:55:33 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 9:56:56 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:01:22</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=2&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:29:05Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=2&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514884</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 9:52:23 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 9:53:44 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:01:21</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=3&amp;$top=1</id>
              <title type="text">GetBuildsStatusEntity</title>
              <updated>2015-05-18T22:29:05Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/GetModelBuildsStatus?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;onlyLastBuild=False&amp;apiVersion='1.0'&amp;$skip=3&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:UserName m:type="Edm.String">637aba67-ebef-4d24-840c-d857661b0b92@dm.com</d:UserName>
                    <d:ModelName m:type="Edm.String">testtest1</d:ModelName>
                    <d:ModelId m:type="Edm.String">d5c7273b-2228-4cf4-99b1-9966e28b143a</d:ModelId>
                    <d:IsDeployed m:type="Edm.String">true</d:IsDeployed>
                    <d:BuildId m:type="Edm.String">1514882</d:BuildId>
                    <d:BuildType m:type="Edm.String">Recommendation</d:BuildType>
                    <d:Status m:type="Edm.String">Success</d:Status>
                    <d:StatusMessage m:type="Edm.String" />
                    <d:Progress m:type="Edm.String">0</d:Progress>
                    <d:StartTime m:type="Edm.String">5/18/2015 9:27:42 PM</d:StartTime>
                    <d:EndTime m:type="Edm.String">5/18/2015 9:28:41 PM</d:EndTime>
                    <d:ExecutionTime m:type="Edm.String">00:00:58</d:ExecutionTime>
                    <d:IsExecutionStarted m:type="Edm.String">false</d:IsExecutionStarted>
                    <d:ProgressStep m:type="Edm.String" />
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    update_model_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/UpdateModel" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Update an Existing Model</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/UpdateModel?id='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T23:09:01Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/UpdateModel?id='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;apiVersion='1.0'" />
        </feed>'''

    invoke_recommendations_single_1 = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Get Recommendation</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='2406e770-769c-4189-89de-1c9283f93a96'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T23:50:53Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='2406e770-769c-4189-89de-1c9283f93a96'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'" />
           <entry>
              <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='2406e770-769c-4189-89de-1c9283f93a96'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1</id>
              <title type="text">GetRecommendationEntity</title>
              <updated>2015-05-18T23:50:53Z</updated>
              <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='2406e770-769c-4189-89de-1c9283f93a96'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'&amp;$skip=0&amp;$top=1" />
              <content type="application/xml">
                 <m:properties>
                    <d:Id m:type="Edm.String">552A1940-21E4-4399-82BB-594B46D7ED54</d:Id>
                    <d:Name m:type="Edm.String">Restraint of Beasts</d:Name>
                    <d:Rating m:type="Edm.Double">0.500787351855212</d:Rating>
                    <d:Reasoning m:type="Edm.String">Most popular item (default system recommendation)</d:Reasoning>
                 </m:properties>
              </content>
           </entry>
        </feed>'''

    invoke_recommendations_single_2 = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Get Recommendation</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='552a1940-21e4-4399-82bb-594b46d7ed54'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T23:51:17Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='552a1940-21e4-4399-82bb-594b46d7ed54'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'" />
        </feed>'''

    invoke_recommendations_list = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:base="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
           <title type="text" />
           <subtitle type="text">Get Recommendation</subtitle>
           <id>https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='2406e770-769c-4189-89de-1c9283f93a96,552a1940-21e4-4399-82bb-594b46d7ed54'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'</id>
           <rights type="text" />
           <updated>2015-05-18T23:52:27Z</updated>
           <link rel="self" href="https://api.datamarket.azure.com/Data.ashx/amla/recommendations/v2/ItemRecommend?modelId='d5c7273b-2228-4cf4-99b1-9966e28b143a'&amp;itemIds='2406e770-769c-4189-89de-1c9283f93a96,552a1940-21e4-4399-82bb-594b46d7ed54'&amp;numberOfResults=10&amp;includeMetadata=False&amp;apiVersion='1.0'" />
        </feed>'''
if __name__ == '__main__':
    unittest.main()
