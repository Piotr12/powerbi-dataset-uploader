import powerbi_dataset_uploader as pbi
import os

auth_dict = {
    "client_id" : os.environ.get("PBI_UPLOADER_CLIENT_ID","variable is not set in os env variables?"),
    "secret" : os.environ.get("PBI_UPLOADER_SECRET","variable is not set in os env variables?"),
    "tenant_id" : os.environ.get("PBI_UPLOADER_TENANT_ID","variable is not set in os env variables?"),
    "scope" : ["https://analysis.windows.net/powerbi/api/Dashboard.ReadWrite.All"]
}

uploader = pbi.PowerBiPushDataSetUploader(auth_dict)
uploader.login()
# LIST DataSets demo
datasets = uploader.get_all_datasets()
for dataset in datasets:
    if dataset.api_editable:
        print (dataset)
        tables = uploader.get_dataset_tables(dataset)
        for table in tables:
            print ("\t",table)
# CREATE Dataset (with two tables) demo
new_dataset = pbi.PowerBIPushDataSet("uploader_test_dataset")
new_table = pbi.PowerBIPushDataSetTable("uploader_test_table")
new_table.add_column("id","Int64")
new_table.add_column("name","string")
new_table.add_column("age","Int64")
new_dataset.tables.append(new_table)
new_table = pbi.PowerBIPushDataSetTable("uploader_test_table_number2")
new_table.add_columns([
    {"name":"id", "datatype":"Int64"},
    {"name":"name", "datatype":"string"},
    {"name":"age", "datatype":"Int64"}
    ])
new_dataset.tables.append(new_table)
create_result = uploader.create_dataset_with_tables(new_dataset)
print ("Create Result",create_result)
# DELETE ALL ROWS in a table
delete_all_rows_result = uploader.delete_table_content("uploader_test_dataset","uploader_test_table")
print ("Delete All Rows Result",delete_all_rows_result)
# UPLOAD NEW ROWS (add to existing ones)
rows = [
    {"id":1,"name":"Piotr","age":42},
    {"id":2,"name":"Basia","age":7} 
]
add_rows_result = uploader.upload_table_content("uploader_test_dataset","uploader_test_table",rows)
print ("add rows result",add_rows_result)