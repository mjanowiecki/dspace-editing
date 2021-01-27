import json
import requests
import secrets
import time
import urllib3
import csv
from datetime import datetime
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
parser.add_argument('-f', '--fileName', help='CSV of bitstream name changes')
args = parser.parse_args()
if args.uri:
    fileName = args.fileName
else:
    fileName = input('Enter file name: ')

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

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

f = csv.writer(open(filePath+'editBitstreamName'+dt+'.csv', 'w'))
f.writerow(['itemID']+['oldBitstreamName']+['newBitstreamName']+['post'])
with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        oldValue = row['oldFileId']
        newValue = row['newFileId']
        handle = row['handle']
        endpoint = baseURL+'/rest/handle/'+handle
        item = requests.get(endpoint, headers=header, cookies=cookies,
                            verify=verify).json()
        itemID = str(item['uuid'])
        itemLink = baseURL+'/rest/items/'+itemID
        bitLink = itemLink+'/bitstreams'
        bitstreams = requests.get(bitLink, headers=header, cookies=cookies,
                                  verify=verify).json()
        for bitstream in bitstreams:
            oldBitstreamName = bitstream['name']
            bitstreamID = bitstream['link']
            updatedBitstream = json.dumps(bitstream)
            print(json.dumps(bitstream))
            updatedBitstream = updatedBitstream.replace(oldValue, newValue)
            post = requests.put(baseURL+bitstreamID, headers=header,
                                cookies=cookies, verify=verify,
                                data=updatedBitstream)
            print(post)
            f.writerow([itemID]+[oldValue]+[newValue]+[post])
            updatedItemMetadataList = []
            link = baseURL+'/rest/items/'+str(itemID)+'/metadata'
            metadata = requests.get(link, headers=header, cookies=cookies,
                                    verify=verify).json()
            for element in range(0, len(metadata)):
                metadata[element].pop('schema', None)
                metadata[element].pop('element', None)
                metadata[element].pop('qualifier', None)
                updatedItemMetadataList.append(metadata[element])
            provNote = ('Bitstream name changed from '+oldValue+' to '
                        + newValue+' by batch process on '+dt+'.')
            provNoteElement = {}
            provNoteElement['key'] = 'dc.description.provenance'
            provNoteElement['value'] = provNote
            provNoteElement['language'] = 'en_US'
            updatedItemMetadataList.append(provNoteElement)
            updatedItemMetadata = json.dumps(updatedItemMetadataList)
            delete = requests.delete(link, headers=header, cookies=cookies,
                                     verify=verify)
            print(delete)
            post = requests.put(link, headers=header, cookies=cookies,
                                verify=verify, data=updatedItemMetadata)
            print(post)

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
