# -*- coding: utf-8 -*-
import json
import requests
import secrets
import csv
import time
import urllib3
import argparse
from datetime import datetime

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
parser.add_argument('-i', '--handle', help='handle of the community.')
parser.add_argument('-f', '--fileName', help='the CSV file of changes.')
args = parser.parse_args()

if args.fileName:
    fileName = args.fileName
else:
    fileName = input('Enter filename of CSV of changes (including \'.csv\'): ')
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
userFullName = status['fullname']
print('authenticated')

endpoint = baseURL+'/rest/handle/'+handle
community = requests.get(endpoint, headers=header, cookies=cookies,
                         verify=verify).json()
communityID = community['uuid']
commID = str(communityID)
collLink = baseURL+'/rest/communities/'+commID+'/collections'
collections = requests.get(collLink, headers=header, cookies=cookies,
                           verify=verify).json()
collSels = ''
for j in range(0, len(collections)):
    collectionID = collections[j]['uuid']
    collSel = '&collSel[]=' + collectionID
    collSels = collSels + collSel

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

counter = 0
f = csv.writer(open(filePath+'replacedValues_'+dt+'.csv', 'w'))
f.writerow(['handle']+['oldValue']+['newValue'])
with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    rowCount = len(list(reader))
with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rowCount -= 1
        oldValue = row['oldValue']
        newValue = row['newValue']
        print('Rows remaining: ', rowCount)
        print(oldValue, ' -- ', newValue)
        if oldValue != newValue:
            print(oldValue)
            offset = 0
            recordsEdited = 0
            items = ''
            itemLinks = []
            while items != []:
                endpoint = baseURL+'/rest/filtered-items?query_field[]=*&query_op[]=equals&query_val[]='+oldValue+collSels+'&limit=200&offset='+str(offset)
                print(endpoint)
                response = requests.get(endpoint, headers=header,
                                        cookies=cookies, verify=verify)
                print(response)
                response = response.json()
                items = response['items']
                print(len(items), ' search results')
                for item in items:
                    itemLink = item['link']
                    itemLinks.append(itemLink)
                offset = offset + 200
                print(offset)
            for itemLink in itemLinks:
                itemMetadataProcessed = []
                link = baseURL+itemLink+'/metadata'
                metadata = requests.get(link, headers=header, cookies=cookies,
                                        verify=verify).json()
                counter += 1
                print(counter)
                for element in range(0, len(metadata)):
                    metadata[element].pop('schema', None)
                    metadata[element].pop('element', None)
                    metadata[element].pop('qualifier', None)
                    languageValue = metadata[element]['language']
                    if metadata[element]['value'] == oldValue:
                        key = metadata[element]['key']
                        replacedElement = metadata[element]
                        updatedMetadataElement = {}
                        updatedMetadataElement['key'] = metadata[element]['key']
                        updatedMetadataElement['value'] = newValue
                        updatedMetadataElement['language'] = languageValue
                        print(updatedMetadataElement)
                        itemMetadataProcessed.append(updatedMetadataElement)
                        provNote = (newValue+' replaced '+oldValue+' in '+key
                                    + ' by batch process on '+dt+'.')
                        provNoteElement = {}
                        provNoteElement['key'] = 'dc.description.provenance'
                        provNoteElement['value'] = provNote
                        provNoteElement['language'] = 'en_US'
                        itemMetadataProcessed.append(provNoteElement)
                        recordsEdited = recordsEdited + 1
                    else:
                        if metadata[element] not in itemMetadataProcessed:
                            itemMetadataProcessed.append(metadata[element])
                itemMetadataProcessed = json.dumps(itemMetadataProcessed)
                print(itemMetadataProcessed)
                print('updated', itemLink, recordsEdited)
                delete = requests.delete(link, headers=header, cookies=cookies,
                                         verify=verify)
                print(delete)
                post = requests.put(link, headers=header, cookies=cookies,
                                    verify=verify, data=itemMetadataProcessed)
                print(post)
                f.writerow([itemLink]+[oldValue]+[newValue]+[delete]+[post])

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
