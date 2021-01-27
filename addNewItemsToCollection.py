import json
import requests
import secrets
from datetime import datetime
import time
import pandas as pd
import urllib3
import argparse

secretsVersion = input('To edit prod server, enter name of secrets file: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print('Editing Production')
    except ImportError:
        print('Editing Stage')
else:
    print('Editing Stage')

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--directory', help='directory of files to ingest')
parser.add_argument('-i', '--handle', help='handle of the object to retreive.')
parser.add_argument('-f', '--filename', help='file listings CSV')
args = parser.parse_args()

if args.directory:
    directory = args.directory
else:
    directory = input('Enter directory name: ')
if args.handle:
    handle = args.handle
else:
    handle = input('Enter handle: ')
if args.filename:
    filename = args.filename
else:
    filename = input('Enter file listing CSV: ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify
skippedCollections = secrets.skippedCollections

# create file list and export csv
df_files = pd.read_csv(filename)


startTime = time.time()
data = {'email': email, 'password': password}
header = {'content-type': 'application/json', 'accept': 'application/json'}
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify,
                        params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}
cookiesFileUpload = cookies
status = requests.get(baseURL+'/rest/status', headers=header,
                      cookies=cookies, verify=verify).json()
userFullName = status['fullname']
print('authenticated')

# Get collection ID
endpoint = baseURL+'/rest/handle/'+handle
collection = requests.get(endpoint, headers=header,
                          cookies=cookies, verify=verify).json()
collectionID = str(collection['uuid'])
print(collectionID)

# Post items
log = []

collectionMetadata = json.load(open(directory+'/'+'metadata.json'))
for count, itemMetadata in enumerate(collectionMetadata):
    print(count)
    itemLog = {}
    updatedItemMetadata = {}
    updatedItemMetadataList = []
    for element in itemMetadata['metadata']:
        if element['key'] == 'fileIdentifier':
            fileIdentifier = element['value']
        else:
            updatedItemMetadataList.append(element)
    updatedItemMetadata['metadata'] = updatedItemMetadataList
    updatedItemMetadata = json.dumps(updatedItemMetadata)
    print(fileIdentifier)
    post = requests.post(baseURL+'/rest/collections/'+collectionID+'/items',
                         headers=header, cookies=cookies, verify=verify,
                         data=updatedItemMetadata).json()
    print(json.dumps(post))

    itemLog['metadataPost'] = post
    itemID = post['link']
    itemLog['link'] = itemID
    itemLog['handle'] = handle
    itemLog['fileIdentifier'] = fileIdentifier

    # Post bitstream - starts with file identifier
    fileId = df_files.fileIdentifier
    index = fileId[fileId == fileIdentifier].index[0]
    fileList = df_files.loc[index, 'file']
    fileList = fileList.split('|')
    for count, file in enumerate(fileList):
        bitstream = directory+file
        data = open(bitstream, 'rb')
        file = file.replace(fileIdentifier, '')
        file = file.replace('_.', '.')
        print(file)
        post = requests.post(baseURL+itemID+'/bitstreams?name='+file,
                             headers=headerFileUpload, cookies=cookies,
                             verify=verify, data=data).json()
        print(post)
        itemLog['bit'+str(count)] = bitstream
        itemLog['post'+str(count)] = post

    # Create provenance notes
    provNote = {}
    provNote['key'] = 'dc.description.provenance'
    provNote['language'] = 'en_US'
    dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')
    bitstreams = requests.get(baseURL+itemID+'/bitstreams', headers=header,
                              cookies=cookies, verify=verify).json()
    bitstreamCount = len(bitstreams)
    provNoteValue = ('Submitted by '+userFullName+' ('+email+') on '+dt+' (EST).\
                     No. of bitstreams: '+str(bitstreamCount))
    for bitstream in bitstreams:
        fileName = bitstream['name']
        size = str(bitstream['sizeBytes'])
        checksum = bitstream['checkSum']['value']
        algorithm = bitstream['checkSum']['checkSumAlgorithm']
        provNoteValue = provNoteValue+' '+fileName+': '+size+' bytes, checkSum: '+checksum+' ('+algorithm+')'
    provNote['value'] = provNoteValue

    provNote2 = {}
    provNote2['key'] = 'dc.description.provenance'
    provNote2['language'] = 'en_US'
    provNote2Value = ('Available in DSpace on '+dt+' (EST).\
                       No. of bitstreams: '+str(bitstreamCount))
    for bitstream in bitstreams:
        fileName = bitstream['name']
        size = str(bitstream['sizeBytes'])
        checksum = bitstream['checkSum']['value']
        algorithm = bitstream['checkSum']['checkSumAlgorithm']
        provNote2Value = provNote2Value+' '+fileName+': '+size+' bytes, checkSum: '+checksum+' ('+algorithm+')'
    provNote2['value'] = provNote2Value

    # Post provenance notes
    provNote = json.dumps([provNote, provNote2])
    post = requests.put(baseURL+itemID+'/metadata', headers=header,
                        cookies=cookies, verify=verify, data=provNote)
    itemLog['provNote'] = post
    log.append(itemLog)

log = pd.DataFrame.from_dict(log)
dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')
pHandle = handle.replace('/', '-')
log.to_csv('logOfItemsAddedTo'+pHandle+'_'+dt+'.csv')


elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
