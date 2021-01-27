import json
import requests
import secrets
import time
import csv
from datetime import datetime
import urllib3
import argparse

secretsVersion = input('To edit production server, enter secrets file: ')
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

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fileName', help='the CSV file of changes.')
args = parser.parse_args()

if args.fileName:
    fileName = args.fileName
else:
    fileName = input('Enter filename of CSV (including \'.csv\'): ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

dt = datetime.now().strftime('%Y-%m-%d%H.%M.%S')

f = csv.writer(open(filePath+'searchAndReplace'+dt+'.csv', 'w'))
f.writerow(['itemID']+['oldKey']+['oldValue']+['delete']+['post'])
with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        oldKey = row['oldKey']
        newKey = row['newKey']
        oldValue = row['oldValue']
        newValue = row['newValue']
        if (oldValue != newValue) or (oldKey != newKey):
            offset = 0
            recordsEdited = 0
            items = ''
            itemLinks = []
            while items != []:
                endpoint = baseURL+'/rest/filtered-items?query_field[]='+oldKey+'&query_op[]=equals&query_val[]='+oldValue+'&limit=200&offset='+str(offset)
                print(endpoint)
                response = requests.get(endpoint, headers=header,
                                        cookies=cookies, verify=verify).json()
                items = response['items']
                for item in items:
                    itemMetadataProcessed = []
                    itemLink = item['link']
                    itemLinks.append(itemLink)
                offset = offset + 200
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
                    languageValue = metadata[element]['language']
                    if metadata[element]['key'] == oldKey and metadata[element]['value'] == oldValue:
                        replacedElement = metadata[element]
                        updatedMetadataElement = {}
                        updatedMetadataElement['key'] = newKey
                        updatedMetadataElement['value'] = newValue
                        updatedMetadataElement['language'] = languageValue
                        itemMetadataProcessed.append(updatedMetadataElement)
                        provNote = ('\''+newKey+': '+newValue+'\' replaced \''
                                    + oldKey+': '+oldValue+'\' by batch process\
                                     on '+dt+'.')
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
                post = requests.put(link, headers=header, cookies=cookies,
                                    verify=verify, data=itemMetadataProcessed)
                print(post)
                f.writerow([itemLink]+[replacedElement['key']]+[replacedElement['value']]+[delete]+[post])

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
