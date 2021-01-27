import json
import requests
import secrets
import time
import csv
from datetime import datetime
import urllib3
import argparse

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

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fileName', help='the CSV file of changes.')
args = parser.parse_args()

if args.fileName:
    fileName = args.fileName
else:
    fileName = input('Enter the file name of the CSV of changes (including \'.csv\'): ')

startTime = time.time()
data = {'email': email, 'password': password}
header = {'content-type': 'application/json', 'accept': 'application/json'}
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify, params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}
cookiesFileUpload = cookies
status = requests.get(baseURL+'/rest/status', headers=header, cookies=cookies, verify=verify).json()
print('authenticated')


dt_stamp = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

f = csv.writer(open('replacedKeyValuePair'+dt_stamp+'.csv', 'w'))
f.writerow(['handle']+['itemID']+['oldKey']+['newKey']+['oldValue']+['newValue']+['delete']+['post'])

f2 = csv.writer(open('notReplacedKeyValuePair'+dt_stamp+'.csv', 'w'))
f2.writerow(['uri']+['oldKey']+['newKey']+['oldValue']+['newValue'])

values_changed = 0
values_unchanged = 0
row_count = 0

with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        row_count = row_count + 1
        uri = row['uri']
        uri = uri[28:]
        print(uri)
        oldKey = row['oldKey']
        newKey = row['newKey']
        oldValue = row['oldSubject']
        newValue = row['newSubject']
        if (oldValue != newValue) or (oldKey != newKey):
            uri_request = requests.get(baseURL+'/rest/'+uri, headers=header, cookies=cookies, verify=verify).json()
            itemLink = uri_request['link']
            metadata = requests.get(baseURL+itemLink+'/metadata', headers=header, cookies=cookies, verify=verify).json()
            itemMetadataProcessed = []
            for l in range(0, len(metadata)):
                metadata[l].pop('schema', None)
                metadata[l].pop('element', None)
                metadata[l].pop('qualifier', None)
                languageValue = metadata[l]['language']
                if metadata[l]['key'] == oldKey and metadata[l]['value'] == oldValue:
                    updatedMetadataElement = {}
                    updatedMetadataElement['key'] = newKey
                    updatedMetadataElement['value'] = newValue
                    updatedMetadataElement['language'] = languageValue
                    itemMetadataProcessed.append(updatedMetadataElement)

                    provNote = '\''+oldKey+': '+oldValue+'\' was replaced by \''+newKey+': '+newValue+'\' through a batch process on '+dt_stamp+'.'
                    provNoteElement = {}
                    provNoteElement['key'] = 'dc.description.provenance'
                    provNoteElement['value'] = provNote
                    provNoteElement['language'] = 'en_US'
                    itemMetadataProcessed.append(provNoteElement)
                else:
                    if metadata[l] not in itemMetadataProcessed:
                        itemMetadataProcessed.append(metadata[l])
            itemMetadataProcessed = json.dumps(itemMetadataProcessed)
            delete = requests.delete(baseURL+itemLink+'/metadata', headers=header, cookies=cookies, verify=verify)
            print(delete)
            post = requests.put(baseURL+itemLink+'/metadata', headers=header, cookies=cookies, verify=verify, data=itemMetadataProcessed)
            print(post)
            f.writerow([uri]+[itemLink]+[oldKey]+[newKey]+[oldValue]+[newValue]+[delete]+[post])
            if post.status_code == 200:
                values_changed = values_changed + 1
            else:
                values_unchanged = values_unchanged + 1
        else:
            f2.writerow([uri]+[oldKey]+[newKey]+[oldValue]+[newValue])

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies, verify=verify)


print('Original row count: {}'.format(row_count))
print('Total values or keys changed: {}'.format(values_changed))
print('Total values unchanged: {}'.format(values_unchanged))
print('total: '+(str(values_changed+values_unchanged)))
elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
