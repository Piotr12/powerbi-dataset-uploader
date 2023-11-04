# need some setup in PowerBI to get this operational
# https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal
# plus this: https://docs.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-groups-create-azure-portal
# plus a lot of trial and error at portal.azure.com ;) 

import msal
import requests
import json
import sys
import atexit
import os
import pprint

class PowerBIPushDataSet:
    def __init__(self,name,guid = "NotAssignedYet",api_editable=True):
        self.name = name
        self.guid = guid
        self.api_editable = api_editable
        self.tables = []

    def __str__(self):
        if (self.api_editable):
            return f"API Editable DataSet {self.name}, {self.guid}."
        else:
            return f"!NOT EDITABLE! DataSet {self.name}, {self.guid}."

    def parse_as_api_create_new_entity_string(self):
        # should be using json package vs this silly thing.
        my_json = '{\n'
        my_json += f'\t"name":"{self.name}",\n'
        my_json += f'\t"defaultMode": "Push",\n'
        my_json += f'\t"tables":[\n'
        for table in self.tables:
            my_json += table.parse_as_api_create_new_entity_string() + ",\n"
        my_json = my_json[:-2] + "\n" #last comma ... should not be doing this 
        my_json += f'\t]\n'
        my_json += '}'
        return my_json


class PowerBIPushDataSetTable:
    def __init__(self,name):
        self.name = name
        self.columns = []

    def add_column(self,name,datatype):
        if datatype not in ("Int64","bool","DateTime","string"):
            raise NotImplementedError(f"{datatype} datatype not implemneted (yet?)")
        self.columns.append({"name":name, "datatype":datatype})
    
    def add_columns(self,name_datatype_pairs):
        for pair in name_datatype_pairs:
            self.add_column(pair["name"],pair["datatype"])
    
    def parse_as_api_create_new_entity_string(self):
        my_json = '\t\t{\n'
        my_json += f'\t\t\t"name":"{self.name}",\n'
        my_json += f'\t\t\t"columns":[\n'
        for column in self.columns:
            my_json += f'\t\t\t\t{{"name":"{column["name"]}", '
            my_json += f'"dataType": "{column["datatype"]}" }},\n'
        my_json = my_json[:-2] + "\n" #last comma ... should not be doing this 
        my_json += f'\t\t\t]\n'
        my_json += '\t\t}'
        return my_json

    
        
class PowerBiPushDataSetUploader:
    def __init__(self,auth_dict):
        self.client_id = auth_dict["client_id"]
        self.secret = auth_dict["secret"]
        self.tenant_id = "https://login.microsoftonline.com/" + auth_dict["tenant_id"]
        self.scope = auth_dict["scope"]
        self.connected = False
    
    def login(self):
        PATH_FOR_OUTPUT = os.getenv('PATH_FOR_OUTPUT','./')
        cache = msal.SerializableTokenCache()
        if os.path.exists(PATH_FOR_OUTPUT + "my_cache.bin"):
            cache.deserialize(open(PATH_FOR_OUTPUT + "my_cache.bin", "r").read())
        atexit.register(lambda:
                open(PATH_FOR_OUTPUT + "my_cache.bin", "w").write(cache.serialize())
                # Hint: The following optional line persists only when state changed
                if cache.has_state_changed else None
                )
        app = msal.PublicClientApplication(self.client_id, authority=self.tenant_id,token_cache=cache)
        accounts = app.get_accounts()
        #print ("Accounts:",accounts)
        if accounts:
            result = app.acquire_token_silent(self.scope, account=accounts[0])
        else:
            result = None
        if not result:
            flow = app.initiate_device_flow(scopes=self.scope)
            print(flow["message"])
            sys.stdout.flush()
            result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self.connected = True
            self.token = result["access_token"]
            self.authenticated_header = {'Content-Type':'application/json; charset=utf-8','Authorization': f'Bearer {self.token}'}
            return True
        else:
            print(result.get("error"))
            print(result.get("error_description"))
            print(result.get("correlation_id"))  # You might need this when reporting a bug.
            return False
                
    def get_all_datasets(self):
        results_list = []
        if self.connected:
            url = "https://api.powerbi.com/v1.0/myorg/datasets"
            response = requests.get(url=url,headers = self.authenticated_header)
            if (response.status_code==200):
                y = json.loads(response.content.decode())["value"]

                for dataset_dict in y:
                    results_list.append(PowerBIPushDataSet(dataset_dict["name"],
                                                            dataset_dict["id"],
                                                            dataset_dict["addRowsAPIEnabled"]))
                return results_list
            else:   
                print (f"PowerBIPushDataSet class says: Issue while querying {url}, response code: {response.status_code}, expected 200")
        else:
            print ("PowerBIPushDataSet class says: Not logged in!")
            return []
    
    def get_dataset_tables(self,dataset):
        if self.connected:
            if dataset.api_editable:
                url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset.guid}/tables"
                response = requests.get(url=url,headers = self.authenticated_header)
                if (response.status_code==200):
                    y = json.loads(response.content.decode())["value"]
                    return y
                    
                else:
                    print (f"PowerBIPushDataSet class says: Issue while querying {url}, response code: {response.status_code}, expected 200")
            else:
                print (f"PowerBIPushDataSet class says: your dataset is not API Editable {dataset}")
        else:
            print ("PowerBIPushDataSet class says: Not logged in!")
        return [] 

    def create_dataset_with_tables(self,dataset):
        datasets = self.get_all_datasets()
        for existing_dataset in datasets:
            if existing_dataset.name == dataset.name:
                print (f"I will not create a second dataset with this name. Dataset called {existing_dataset.name} is already there in your Power BI workspace")
                return False
        data = dataset.parse_as_api_create_new_entity_string()
        url = f"https://api.powerbi.com/v1.0/myorg/datasets?defaultRetentionPolicy=None"
        response = requests.post(url=url,headers = self.authenticated_header, data = data)
        if (response.status_code==201) or (response.status_code==202):
            return True
        else:
            print (response.text)   
            return False

    def delete_table_content(self,dataset_name,table_name):
        datasets_modified = 0
        datasets = self.get_all_datasets()
        result = True
        for dataset in datasets:
            if dataset.name == dataset_name:
                datasets_modified +=1
                url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset.guid}/tables/{table_name}/rows"
                response = requests.delete(url=url,headers = self.authenticated_header)
                if (response.status_code!=200):
                    result = False
                    print (response.content)
        if datasets_modified!=1:
            print (f"delete_table_content touched {datasets_modified} datasets, thats a number other than 1?")
        return result

    def upload_table_content(self,dataset_name,table_name,rows_list):
        datasets_modified = 0
        datasets = self.get_all_datasets()
        result = True
        for dataset in datasets:
            if dataset.name == dataset_name:
                datasets_modified += 1
                url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset.guid}/tables/{table_name}/rows"
                data = self.parse_as_api_rows_input(rows_list)
                response = requests.post(url=url, headers = self.authenticated_header, data = data)
                if response.status_code!=200:
                    result = False
                    print (response.content)
        if datasets_modified!=1:
            print (f"upload_table_content touched {datasets_modified} datasets, thats a number other than 1?")
        return result

    def parse_as_api_rows_input(self,rows_list):
        data = '{"rows":[\n'
        for row in rows_list:
            if type(row) is not dict:
                raise NotImplementedError("ooops, parse_as_api_rows_input() is unable to handle non dict rows as of now")
            data += "\t{\n"
            for key in row.keys():
                value = row[key]
                data += f'\t\t"{key}":"{value}",\n'
                pass
            data = data[:-2] + "\n" # TODO fix it with Json lib not own code 
            data += "\t},\n"
        data = data[:-2] + "\n" # TODO fix it with Json lib not own code 
        data += "]}\n"
        #print (data)
        return data