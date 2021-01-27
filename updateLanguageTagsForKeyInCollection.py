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

key = input('Enter key: ')
collectionHandle = input('Enter collection handle: ')

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

itemList = []
endpoint = baseURL+'/rest/handle/'+collectionHandle
collection = requests.get(endpoint, headers=header, cookies=cookies,
                          verify=verify).json()
collectionID = collection['uuid']
collID = str(collectionID)
offset = 0
items = ''
while items != []:
    search = (baseURL+'/rest/collections/'+collID+'/items?limit=200&offset='
              + str(offset))
    items = requests.get(search, headers=header, cookies=cookies,
                         verify=verify)
    while items.status_code != 200:
        time.sleep(5)
        items = requests.get(search, headers=header, cookies=cookies,
                             verify=verify)
    items = items.json()
    for k in range(0, len(items)):
        itemID = items[k]['uuid']
        itemList.append(itemID)
    offset = offset + 200
elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Item list creation time: ', '%d:%02d:%02d' % (h, m, s))

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

f = csv.writer(open(filePath+'languageTagUpdate'+key+'_'+dt+'.csv', 'w'))
f.writerow(['itemID']+['key'])
for number, itemID in enumerate(itemList):
    itemMetadataProcessed = []
    itemsRemaining = len(itemList) - number
    print('Items remaining: ', itemsRemaining, 'ItemID: ', itemID)
    link = baseURL+'/rest/items/'+str(itemID)+'/metadata'
    metadata = requests.get(link, headers=header, cookies=cookies,
                            verify=verify).json()
    for element in range(0, len(metadata)):
        if metadata[element]['key'] == key and metadata[element]['language'] == '':
            updatedMetadataElement = {}
            updatedMetadataElement['key'] = metadata[element]['key']
            updatedMetadataElement['value'] = metadata[element]['value']
            updatedMetadataElement['language'] = 'en_US'
            itemMetadataProcessed.append(updatedMetadataElement)
            provNote = ('The language tag for \''+metadata[element]['key']+': '
                        + metadata[element]['value']+'\' changed from \'null\' to \'en_US\' \
                        by batch process on '+dt+'.')
            provNoteElement = {}
            provNoteElement['key'] = 'dc.description.provenance'
            provNoteElement['value'] = provNote
            provNoteElement['language'] = 'en_US'
            itemMetadataProcessed.append(provNoteElement)
        else:
            itemMetadataProcessed.append(metadata[element])
    if 'The language tag for \''+key in json.dumps(itemMetadataProcessed):
        itemMetadataProcessed = json.dumps(itemMetadataProcessed)
        print('updated', itemID)
        delete = requests.delete(link, headers=header, cookies=cookies,
                                 verify=verify)
        print(delete)
        post = requests.put(link, headers=header, cookies=cookies,
                            verify=verify, data=itemMetadataProcessed)
        print(post)
        f.writerow([itemID]+[key])
    else:
        print('not updated', itemID)

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
