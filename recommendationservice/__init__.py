import requests
import base64
from xml.etree import ElementTree
import os
from time import sleep
from datetime import datetime

class RecommendationService:
    API_VERSION = '1.0'
    ns = { 'a' : 'http://www.w3.org/2005/Atom', 'm' : "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata", 'd' : "http://schemas.microsoft.com/ado/2007/08/dataservices" }

    def __init__(self, email, account_key):
        """
        Sample app to show usage of part of the cloudML recommendation API 
        The application will create a model container, add catalog and usage data, 
        trigger a recommendation model build, monitor the build execution and get recommendations 
        The application also show the usage of updating model information. 
        
        The scenario above is a full loop when you don't have anything, usually you will create a container once and invoke 
        other API according to your need.
        """
        self.auth = ('ptvsazure@outlook.com', '5dxIeDWCg/dwSclY/mvt929z26mf/RnHKNXeqDN2he8=')

    def create_model(self, model_name):
        """
        create the model with the given name.

        Returns:
            str: The model id.
        """
        create_model_url = Uris.root_uri + Uris.create_model_url.format(model_name, self.API_VERSION)

        response = requests.post(create_model_url, auth=self.auth)

        if response.status_code != 200:
            raise Exception('Failed to create model: Code:{} Reason:{}'.format(response.status_code, response.reason))

        # get model id
        tree = ElementTree.fromstring(response.content)
        model_id = tree.find('a:entry/a:content/m:properties/d:Id', self.ns).text
        return model_id

    def extract_error_info(self, response):
        """
        Extract error message from the httpResponse, (reason phrase + body)
        """
        detailed_reason = None
        if response.content is not None:
            detailed_reason = response.content

        error_msg = '{}->{}'.format(response.reason, detailed_reason) if detailed_reason else response.reason 
        return error_msg

    def _build_recommendation(self, model_id, build_description, build_type, body):
        """
        Helper to trigger a build for the given model and body
        To see the different types of builds visit
        http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters

        Args:
            model_id (str): the model id
            build_description (str): a description for the build
            body (str): the body describing this build.

        Returns:
            str: The id of the triggered build.
        """
        if not build_description:
            build_description = "build of " + datetime.now().strftime('%Y%m%d%H%M%S')

        response = requests.post(Uris.root_uri + Uris.build_model.format(model_id, build_description, build_type), body, headers={'content-type': 'Application/xml'}, auth=self.auth)

        if response.status_code != 200:
            raise Exception("Error {0}: Failed to start build for model {1}, \n reason {2}".format(
                response.status_code, model_id, self.extract_error_info(response)))

        build_id = None
        #process response if success
        node = ElementTree.fromstring(response.content).find('a:entry/a:content/m:properties/d:Id', self.ns)
        if node is not None:
            build_id = node.text
            return build_id
        else:
            raise Exception('Response did not contain expected elements.  Unable to find build id.')
    
    def build_rank_model(self, model_id, build_description = None):
        """
        Trigger a rank build for the given model
        To see the different types of builds visit
        http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters

        Args:
            model_id (str): the model id
            build_description (str): a description for the build

        Returns:
            str: The id of the triggered build.
        """

        # Explanation in the API document:
        # http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters
        body = '''<BuildParametersList>
    <NumberOfModelIterations>10</NumberOfModelIterations>
    <NumberOfModelDimensions>20</NumberOfModelDimensions>
    <ItemCutOffLowerBound>1</ItemCutOffLowerBound>
    <ItemCutOffUpperBound>0</ItemCutOffUpperBound>
    <UserCutOffLowerBound>0</UserCutOffLowerBound>
    <UserCutOffUpperBound>0</UserCutOffUpperBound>
</BuildParametersList>'''
        
        return self._build_recommendation(model_id, build_description, 'Ranking',  body)

    def build_recommendation_model(self, model_id, build_description = None):
        """
        Trigger a recommendation build for the given model
        To see the different types of builds visit
        http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters

        Args:
            model_id (str): the model id
            build_description (str): a description for the build

        Returns:
            str: The id of the triggered build.
        """

        # Explanation in the API document:
        # http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters
        body = '''<BuildParametersList>
    <NumberOfModelIterations>10</NumberOfModelIterations>
    <NumberOfModelDimensions>20</NumberOfModelDimensions>
    <ItemCutOffLowerBound>1</ItemCutOffLowerBound>
    <ItemCutOffUpperBound>0</ItemCutOffUpperBound>
    <UserCutOffLowerBound>0</UserCutOffLowerBound>
    <UserCutOffUpperBound>0</UserCutOffUpperBound>
    <Description>0</Description>
    <EnableModelingInsights>false</EnableModelingInsights>
    <UseFeaturesInModel>false</UseFeaturesInModel>
    <ModelingFeatureList></ModelingFeatureList>
    <AllowColdItemPlacement>true</AllowColdItemPlacement>
    <EnableFeatureCorrelation>false</EnableFeatureCorrelation>
    <ReasoningFeatureList></ReasoningFeatureList>
</BuildParametersList>'''
        
        return self._build_recommendation(model_id, build_description, 'Recommendation', body)
    
    def build_fbt_model(self, model_id, build_description = None):
        """
        Trigger an fbt build for the given model
        To see the different types of builds visit
        http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters

        Args:
            model_id (str): the model id
            build_description (str): a description for the build

        Returns:
            str: The id of the triggered build.
        """

        # Explanation in the API document:
        # http://azure.microsoft.com/en-us/documentation/articles/machine-learning-recommendation-api-documentation/#1113-recommendation-build-parameters
        body = '''<BuildParametersList>
    <FbtSupportThreshold>6</FbtSupportThreshold>
    <FbtMaxItemSetSize>2</FbtMaxItemSetSize>
    <FbtMinimalScore>0</FbtMinimalScore>
</BuildParametersList>'''
        
        return self._build_recommendation(model_id, build_description, 'Fbt', body)

    def get_build_status(self, model_id, build_id):
        """
        Retrieve the build status for the given build
        """
        response = requests.get(Uris.root_uri + Uris.build_statuses.format(model_id, False), auth=self.auth)
        
        if response.status_code != 200:
            raise Exception("Error {0}: Failed to retrieve build for status for model {1} and build id {2}, \n reason {3}".format(
                response.status_code, model_id, build_id, self.extract_error_info(response)))
        
        build_status_str = None
        node = ElementTree.fromstring(response.content).find("a:entry/a:content/m:properties[d:BuildId='{0}']/d:Status".format(build_id), self.ns)
        if node is  None:
            # Queued objects don't have a 'BuildId' but instead an 'Id' Element
            node = ElementTree.fromstring(response.content).find("a:entry/a:content/m:properties[d:Id='{0}']/d:Status".format(build_id), self.ns)
        
        if node is not None:
            return node.text
        else:
            raise Exception("Failed to find entry/content/properties[Id='{}']/Status Element".format(build_id))
                
    def update_model(self, model_id, description, active_build_id):
        """
        Update model information.  If description is set we update the model name.  
        If active_build_id is specified we update the active build.

        Args:
            model_id (str): The id of the model
            description (str): The model description (optional)
            active_build_id (str): The id of the build to be active (optional)
        """
        
        body = '<ModelUpdateParams xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'                  

        if description is not None and description != '':
            body += "<Description>{0}</Description>".format(description)
        
        if active_build_id is not None and active_build_id != '':
            body += "<ActiveBuildId>{0}</ActiveBuildId>".format(active_build_id)
        
        body += "</ModelUpdateParams>"
           
        response = requests.put(Uris.root_uri + Uris.update_model.format(model_id), body, headers={'content-type':'Application/xml'}, auth=self.auth)

        if response.status_code != 200:
            raise Exception("Error {0}: Failed to update model for model {1}, \n reason {2}".format(
                response.status_code, model_id, self.extract_error_info(response)))

    def get_recommendation(self, model_id, item_id_list, number_of_results=10, include_metadata = False):
        """
        Retrieve recommendation for the given item(s)

        Args:
            model_id (str):
            item_id_list (list of str):
            number_of_results (int):

        Returns:
            list of RecommendedItem): A collection of recommended items.
        """
        
        response = requests.get(Uris.root_uri + Uris.get_recommendation.format(model_id,','.join(item_id_list), number_of_results, include_metadata), auth=self.auth)

        if response.status_code != 200:
            raise Exception(
                "Error {0}: Failed to retrieve recommendation for item list {1} and model {2}, \n reason {3}".format(
                    response.status_code, ",".join(item_id_list), model_id, self.extract_error_info(response)))
        
        reco_list = []
        node_list = ElementTree.fromstring(response.content).findall("a:entry/a:content/m:properties", self.ns)

        for node in node_list:
            item = RecommendedItem()
            # cycle through the recommended items
            for child in node.getchildren():
                childName = str(child)
            
                if "Id" in childName:
                    item.id = child.text
                elif "Name" in childName:
                    item.name = child.text
                elif "Rating" in childName:
                    item.rating = child.text
                elif "Reasoning" in childName:
                    item.reasoning = child.text
                else:
                    print('WARNING: Found an unexpected value "{}"'.format(childName)) # TODO: Should this be an error/exception

            reco_list.append(item)

        return reco_list

    def import_file(self, model_id, file_path, import_uri):
        """
        Import the given file (catalog/usage) to the given model. 
        """
        file = open(file_path)
        file_name = os.path.basename(file_path)
        
        response = requests.post(Uris.root_uri + import_uri.format(model_id, file_name), files={file_name: file}, auth=self.auth) 

        if response.status_code != 200:
            raise Exception(
                "Error {0}: Failed to import file {1}, for model {2} \n reason {3}".format(
                    response.status_code, file_path, model_id, self.extract_error_info(response)))

        # process response if success
        node_list = ElementTree.fromstring(response.content).findall("a:entry/a:content/m:properties/*", self.ns)

        report = ImportReport()
        report.info = file_name
        for node in node_list:
            if "LineCount" in str(node):
                report.line_count = node.text
            elif "ErrorCount" in str(node):
                report.error_count = node.text
        
        return report

    def wait_for_build(self, model_id, build_id):
        '''
        Waits for build to either complete, cancel, or error out

        Args:
            model_id (str)
            build_id (str)

        Returns:
            str : Status of the build.
        '''
        status = BuildStatus.create
        monitor = True
        while monitor:
            status = self.get_build_status(model_id, build_id)
            print("\tbuild '{0}' (model '{1}'): status {2}".format(build_id, model_id,status))
            if status != BuildStatus.error and status != BuildStatus.cancelled and status != BuildStatus.success:
                print(" --> will check in 5 sec...")
                sleep(5)
            else:
                monitor = False
        return status

class Uris:
    root_uri = "https://api.datamarket.azure.com/amla/recommendations/v2/"
    create_model_url = "CreateModel?modelName=%27{}%27&apiVersion=%27{}%27"
    import_catalog = "ImportCatalogFile?modelId=%27{0}%27&filename=%27{1}%27&apiVersion=%271.0%27"
    import_usage = "ImportUsageFile?modelId=%27{0}%27&filename=%27{1}%27&apiVersion=%271.0%27"
    build_model = "BuildModel?modelId=%27{0}%27&userDescription=%27{1}%27&buildType=%27{2}%27&apiVersion=%271.0%27"
    build_statuses = "GetModelBuildsStatus?modelId=%27{0}%27&onlyLastBuild={1}&apiVersion=%271.0%27"
    get_recommendation = "ItemRecommend?modelId=%27{0}%27&itemIds=%27{1}%27&numberOfResults={2}&includeMetadata={3}&apiVersion=%271.0%27"
    update_model = "UpdateModel?id=%27{0}%27&apiVersion=%271.0%27"

class BuildStatus:
    create = 'Create'
    queued = 'Queued'
    building = 'Building'
    success = 'Success'
    error = 'Error'
    cancelling = 'Cancelling'
    cancelled = 'Cancelled'

class CatalogItem:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __str__(self):
        return 'Id: {}, Name: {}'.format(self.id, self.name)

class ImportReport:
    info = ""
    error_count = 0
    line_count = 0

class RecommendedItem:
    name = ''
    rating = ''
    reasoning = ''
    id = ''

    def __str__(self):
        return "Name: {0}, Id: {1}, Rating: {2}, Reasoning: {3}".format(
            self.name, self.id, self.rating, self.reasoning)