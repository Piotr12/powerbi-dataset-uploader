# powerbi-dataset-uploader
quick and dirty facade for PowerBI API to easily access it in Python for PushDatasets 

```bash
sudo pip3 install git+https://github.com/Piotr12/powerbi-dataset-uploader.git #or something similar to get it installed
```

see [demo.py](demo.py) for sample usage

you will need three env variables set to get it running:
+ PBI_UPLOADER_CLIENT_ID
+ PBI_UPLOADER_SECRET
+ PBI_UPLOADER_TENANT_ID

Relevant docs to review:
+ [https://docs.microsoft.com/en-us/power-bi/developer/automation/walkthrough-push-data](https://docs.microsoft.com/en-us/power-bi/developer/automation/walkthrough-push-data)
+ [https://github.com/AzureAD/microsoft-authentication-library-for-python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
+ [https://docs.microsoft.com/en-us/rest/api/power-bi/push-datasets/datasets-post-dataset-in-group](https://docs.microsoft.com/en-us/rest/api/power-bi/push-datasets/datasets-post-dataset-in-group)

## it is not alpha-ready yet

please do note currently only device-code authentication method *works* and in general only one use case was mildly tested. 
