import json
import requests
import secrets
import time
import csv
from datetime import datetime
import urllib3
import argparse

secretsVersion = input('To edit production server, enter secrets filename: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print('Editing Production')
    except ImportError:
        print('Editing Stage')
else:
    print('Editing Stage')

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key', help='the key to be added.')
parser.add_argument('-v', '--value', help='the value to be added.')
parser.add_argument('-l', '--language', help='the language tag to be added.')
parser.add_argument('-i', '--handle', help='handle of the collection.')
args = parser.parse_args()

if args.key:
    addedKey = args.key
else:
    addedKey = input('Enter the key: ')
if args.value:
    addedValue = args.value
else:
    addedValue = input('Enter the value: ')
if args.language:
    addedLanguage = args.language
else:
    addedLanguage = input('Enter the language tag: ')
if args.handle:
    handle = args.handle
else:
    handle = input('Enter collection handle: ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

itemList = []
endpoint = baseURL+'/rest/handle/'+handle
collection = requests.get(endpoint, headers=header, cookies=cookies,
                          verify=verify).json()
collectionID = collection['uuid']
collectID = str(collectionID)
offset = 0
items = ''
while items != []:
    link = baseURL+'/rest/collections/'+collectID+'/items?limit=200&offset='\
           + str(offset)
    items = requests.get(link, headers=header, cookies=cookies, verify=verify)
    while items.status_code != 200:
        time.sleep(5)
        items = requests.get(link, headers=header, cookies=cookies,
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

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S'
recordsEdited = 0
f = csv.writer(open(filePath+'addKeyValuePair'+dt+'.csv', 'w'))
f.writerow(['itemID']+['addedKey']+['addedValue']+['delete']+['post'])
for number, itemID in enumerate(itemList):
    itemsRemaining = len(itemList) - number
    print('Items remaining: ', itemsRemaining, 'ItemID: ', itemID)
    link = baseURL+'/rest/items/'+str(itemID)+'/metadata'
    metadata = requests.get(link, headers=header, cookies=cookies,
                            verify=verify).json()
    itemMetadataProcessed = []
    for l in range(0, len(metadata)):
        metadata[l].pop('schema', None)
        metadata[l].pop('element', None)
        metadata[l].pop('qualifier', None)
        itemMetadataProcessed.append(metadata[l])
    addedMetadataElement = {}
    addedMetadataElement['key'] = addedKey
    addedMetadataElement['value'] = addedValue
    addedMetadataElement['language'] = addedLanguage
    itemMetadataProcessed.append(addedMetadataElement)
    provNote = '\''+addedKey+': '+addedValue+'\' was added through\
               batch process on '+dt+'.'
    provNoteElement = {}
    provNoteElement['key'] = 'dc.description.provenance'
    provNoteElement['value'] = provNote
    provNoteElement['language'] = 'en_US'
    itemMetadataProcessed.append(provNoteElement)
    recordsEdited = recordsEdited + 1
    itemMetadataProcessed = json.dumps(itemMetadataProcessed)
    print('updated', itemID, recordsEdited)
    delete = requests.delete(link, headers=header, cookies=cookies,
                             verify=verify)
    print(delete)
    post = requests.put(link, headers=header, cookies=cookies, verify=verify,
                        data=itemMetadataProcessed).json()
    print(post)
    f.writerow([itemID]+[addedKey]+[addedValue]+[delete]+[post])

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
