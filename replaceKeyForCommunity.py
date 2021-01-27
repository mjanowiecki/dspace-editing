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
parser.add_argument('-1', '--oldKey', help='the key to be replaced.')
parser.add_argument('-2', '--newKey', help='the new key.')
parser.add_argument('-i', '--handle', help='community handle to retreive.')
args = parser.parse_args()

if args.oldKey:
    oldKey = args.oldKey
else:
    oldKey = input('Enter the key to be replaced: ')
if args.newKey:
    newKey = args.newKey
else:
    newKey = input('Enter the replacement key: ')
if args.handle:
    handle = args.handle
else:
    handle = input('Enter community handle: ')

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

endpoint = baseURL+'/rest/handle/'+handle
community = requests.get(endpoint, headers=header, cookies=cookies,
                         verify=verify).json()
communityID = community['uuid']
commID = str(communityID)
collections = requests.get(baseURL+'/rest/communities/'+commID+'/collections',
                           headers=header, cookies=cookies,
                           verify=verify).json()
collSels = ''
for j in range(0, len(collections)):
    collectionID = collections[j]['uuid']
    collSel = '&collSel[]=' + collectionID
    collSels = collSels + collSel

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

f = csv.writer(open(filePath+'replaceKey'+dt+'.csv', 'w'))
f.writerow(['itemID']+['newKey']+['replacedValue']+['delete']+['post'])
offset = 0
recordsEdited = 0
items = ''
itemLinks = []
while items != []:
    endpoint = baseURL+'/rest/filtered-items?query_field[]='+newKey+'&query_op[]=exists&query_val[]='+collSels+'&limit=200&offset='+str(offset)
    print(endpoint)
    response = requests.get(endpoint, headers=header, cookies=cookies, verify=verify).json()
    items = response['items']
    for item in items:
        itemMetadataProcessed = []
        itemLink = item['link']
        itemLinks.append(itemLink)
    offset = offset+200
    print(offset)
for itemLink in itemLinks:
    itemMetadataProcessed = []
    print(itemLink)
    link = baseURL+itemLink+'/metadata'
    metadata = requests.get(link, headers=header, cookies=cookies,
                            verify=verify).json()
    for element in range(0, len(metadata)):
        metadata[element].pop('schema', None)
        metadata[element].pop('element', None)
        metadata[element].pop('qualifier', None)
        if metadata[element]['key'] == oldKey:
            replacedElement = metadata[element]
            updatedMetadataElement = {}
            updatedMetadataElement['key'] = newKey
            updatedMetadataElement['value'] = replacedElement['value']
            updatedMetadataElement['language'] = replacedElement['language']
            print(updatedMetadataElement)
            itemMetadataProcessed.append(updatedMetadataElement)
            provNote = '\''+newKey+'\' replaced \''+oldKey+'\' by batch process\
                        on '+dt+'.'
            provNoteElement = {}
            provNoteElement['key'] = 'dc.description.provenance'
            provNoteElement['value'] = provNote
            provNoteElement['language'] = 'en_US'
            itemMetadataProcessed.append(provNoteElement)
        else:
            if metadata[element] not in itemMetadataProcessed:
                itemMetadataProcessed.append(metadata[element])
    itemMetadataProcessed = json.dumps(itemMetadataProcessed)
    delete = requests.delete(link, headers=header, cookies=cookies,
                             verify=verify)
    print(delete)
    post = requests.put(link, headers=header, cookies=cookies, verify=verify,
                        data=itemMetadataProcessed)
    print(post)
    f.writerow([itemLink]+[replacedElement['key']]+[replacedElement['value']]+[delete]+[post])

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
