import json
import requests
import secrets
import time
import csv
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

secretsVersion = input('To edit production server, enter secrets filename: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print('Editing Production')
    except ImportError:
        print('Editing Stage')
else:
    print('Editing Stage')

baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify
skippedCollections = secrets.skippedCollections

startTime = time.time()
data = {'email': email, 'password': password}
header = {'content-type': 'application/json', 'accept': 'application/json'}
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify,
                        params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}
cookiesFileUpload = cookies
status = requests.get(baseURL+'/rest/status', headers=header, cookies=cookies,
                      verify=verify).json()
print('authenticated')

fileName = filePath+input('Enter fileName (including \'.csv\'): ')
addedKey = input('Enter key: ')
startTime = time.time()
dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

f = csv.writer(open(filePath+'addKeyValuePair'+dt+'.csv', 'w'))
f.writerow(['itemID']+['addedKey']+['addedValue']+['delete']+['post'])

with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        addedValue = row['value']
        handle = row['handle'].strip()
        addedMetadataElement = {}
        addedMetadataElement['key'] = addedKey
        addedMetadataElement['value'] = addedValue
        addedMetadataElement['language'] = 'en_us'
        endpoint = baseURL+'/rest/handle/'+handle
        item = requests.get(endpoint, headers=header, cookies=cookies,
                            verify=verify).json()
        itemID = item['uuid']
        link = baseURL+'/rest/items/'+str(itemID)+'/metadata'
        itemMetadata = requests.get(link, headers=header, cookies=cookies,
                                    verify=verify).json()
        itemMetadata.append(addedMetadataElement)
        itemMetadataProcessed = itemMetadata
        provNote = '\''+addedKey+': '+addedValue+'\' was added through a batch\
                    process on '+dt+'.'
        provNoteElement = {}
        provNoteElement['key'] = 'dc.description.provenance'
        provNoteElement['value'] = provNote
        provNoteElement['language'] = 'en_US'
        itemMetadataProcessed.append(provNoteElement)

        itemMetadataProcessed = json.dumps(itemMetadataProcessed)
        delete = requests.delete(link, headers=header, cookies=cookies,
                                 verify=verify)
        print(delete)
        post = requests.put(link, headers=header, cookies=cookies,
                            verify=verify, data=itemMetadataProcessed)
        print(post)
        f.writerow([itemID]+[addedMetadataElement['key']]+[addedMetadataElement['value']]+[delete]+[post])
