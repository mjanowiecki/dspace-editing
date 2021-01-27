import requests
import secrets
import time
import csv
from datetime import datetime
import pandas as pd
import urllib3
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

secretsVersion = input('To edit production, enter secrets filename: ')
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
parser.add_argument('-f', '--fileName')
parser.add_argument('-k', '--key')
args = parser.parse_args()

if args.fileName:
    fileName = args.fileName
else:
    fileName = input('Enter file name of CSV (including \'.csv\'): ')
if args.key:
    key = args.key
else:
    key = input('Enter the key: ')

key = 'dc.title.alternative'

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

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

logList = []
with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        provNoteElement = {}
        logDict = {}

        itemLink = row['itemID']
        itemLink = '/rest/items/'+itemLink
        newValue = row['local.related.conference']
        newValues = newValue.split('|')
        print(itemLink)

        provNoteElement['key'] = 'dc.description.provenance'
        provNoteElement['language'] = 'en_US'

        link = baseURL+itemLink+'/metadata'
        metadata = requests.get(link, headers=header, cookies=cookies,
                                verify=verify).json()
        df = pd.DataFrame.from_dict(metadata)
        df = df.drop(['schema', 'element', 'qualifier'], axis=1)
        keyList = df.key.tolist()
        oldkeyCount = len(keyList)
        if key in keyList:
            print('Error: '+itemLink+' already exists')
            logList.append({'itemID': itemLink, 'delete': 'ERROR',
                            'post': 'ERROR'})
            pass
        else:
            for count, nv in enumerate(newValues):
                nv = nv.strip()
                newElement = {'key': key, 'value': nv}
                print(newElement)
                provNote = key+': '+nv+' added by batch process on '+dt+'.'
                provNoteElement['value'] = provNote
                print(provNoteElement)
                df = df.append([newElement, provNoteElement],
                               ignore_index=True)
                scount = str(count)
                logDict.update({'key_'+scount: key, 'value_'+scount: nv})

            keyList = df.key.tolist()
            newkeyCount = len(keyList)
            keyChange = newkeyCount - oldkeyCount
            print(str(keyChange)+' key/value pairs added to record')
            itemMetadataProcessed = df.to_json(orient='records')
            delete = requests.delete(link, headers=header,
                                     cookies=cookies, verify=verify)
            print(delete)
            post = requests.put(link, headers=header, cookies=cookies,
                                verify=verify, data=itemMetadataProcessed)
            print(post)
            print('')
            logDict.update({'itemID': itemLink, 'delete': delete,
                            'post': post})
            logList.append(logDict)

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

log = pd.DataFrame.from_dict(logList)
print(log.head(15))
log.to_csv('logOfAddingKeyValuePairsByItemID_'+dt+'.csv', index=False)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
