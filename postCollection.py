import json
import requests
import secrets
import datetime
import time
import os
import csv
import urllib3
import argparse


secretsVersion = input('To edit production server, enter the name of the secrets file: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print('Editing Production')
    except ImportError:
        print('Editing Stage')
else:
    print('Editing Stage')

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--directory', help='the directory of the files. optional - if not provided, the script will ask for raw_input')
parser.add_argument('-e', '--fileExtension', help='the file extension. optional - if not provided, the script will ask for raw_input')
parser.add_argument('-i', '--communityHandle', help='handle of the community. optional - if not provided, the script will ask for raw_input')
parser.add_argument('-n', '--collectionName', help='the name of the collection. optional - if not provided, the script will ask for raw_input')
args = parser.parse_args()

if args.directory:
    directory = args.directory
else:
    directory = input('Enter directory (C:/Test/): ')
if args.fileExtension:
    fileExtension = args.fileExtension
else:
    fileExtension = input('Enter file extension: ')
if args.communityHandle:
    communityHandle = args.communityHandle
else:
    communityHandle = input('Enter community handle: ')
if args.collectionName:
    collectionName = args.collectionName
else:
    collectionName = input('Enter collection name: ')

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
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify, params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}
cookiesFileUpload = cookies
status = requests.get(baseURL+'/rest/status', headers=header, cookies=cookies, verify=verify).json()
userFullName = status['fullname']
print('authenticated')

# create file list and export csvf
fileList = {}
for root, dirs, files in os.walk(directory, topdown=True):
    print('building file list')
    for file in files:
        if file.endswith(fileExtension):
            fileList[file[:file.index('.')]] = os.path.join(root, file).replace('\\', '/')
elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('File list creation time: ', '%d:%02d:%02d' % (h, m, s))

f = csv.writer(open(collectionName.replace(' ', '')+'fileList.csv', 'w'))
f.writerow(['itemID'])

for k, v in fileList.items():
    f.writerow([v[v.rindex('/')+1:]])

f2 = open('fileListDict.txt', 'w')
f2.write(json.dumps(fileList))

# Use this section of code if 'fileListDict.txt' has already been generated and comment out lines 64-83. This is useful if uploading a very large collection as generating the file list will take some time.
# f3=open('fileListDict.txt', 'r')
# fileList = json.load(f3)

# Get community ID
endpoint = baseURL+'/rest/handle/'+communityHandle
community = requests.get(endpoint, headers=header, cookies=cookies, verify=verify).json()
communityID = str(community['uuid'])

# Post collection
collection = json.dumps({'name': collectionName})
post = requests.post(baseURL+'/rest/communities/'+communityID+'/collections', headers=header, cookies=cookies, verify=verify, data=collection).json()
collectionID = post['link']

files_added = 0
items_total = 0
embargo_items = 0
# Post items
collectionMetadata = json.load(open('metadata.json'))
for itemMetadata in collectionMetadata:
    fileExists = ''
    updatedItemMetadata = {}
    updatedItemMetadataList = []
    for element in itemMetadata['metadata']:
        if element['key'] == 'fileIdentifier':
            fileIdentifier = element['value']
        else:
            updatedItemMetadataList.append(element)
    updatedItemMetadata['metadata'] = updatedItemMetadataList
    updatedItemMetadata = json.dumps(updatedItemMetadata)
    for k in fileList:
        if fileIdentifier in k:
            fileExists = True
    if fileExists is True:
        print(fileIdentifier)
        post = requests.post(baseURL+collectionID+'/items', headers=header, cookies=cookies, verify=verify, data=updatedItemMetadata).json()
        # print(json.dumps(post))
        itemID = post['link']
        itemID_name = itemID[13:]
        items_total = items_total + 1
        print('Created item: {}'.format(itemID_name))
        print('Total items: {}'.format(items_total))

        # #Post bitstream - front and back. Deprecated method, preserved for reference
        # for k,v in fileList.items():
        #     if k == fileIdentifier + '-Front':
        #         bitstream = fileList[k]
        #         fileName = bitstream[bitstream.rfind('/')+1:]
        #         data = open(bitstream, 'r')
        #         post = requests.post(baseURL+itemID+'/bitstreams?name='+fileName, headers=headerFileUpload, verify=verify, data=data).json()
        #         print(post)
        #
        # for k,v in fileList.items():
        #     if k == fileIdentifier + '-Back':
        #         bitstream = fileList[k]
        #         fileName = bitstream[bitstream.rfind('/')+1:]
        #         data = open(bitstream, 'r')
        #         post = requests.post(baseURL+itemID+'/bitstreams?name='+fileName, headers=headerFileUpload, verify=verify, data=data).json()
        #         print(post)

        # Post bitstream - starts with file identifier
        for k, v in fileList.items():
            if k.startswith(fileIdentifier):
                bitstream = fileList[k]
                fileName = bitstream[bitstream.rfind('/')+1:]
                data = open(bitstream, 'r')
                post = requests.post(baseURL+itemID+'/bitstreams?name='+fileName, headers=headerFileUpload, cookies=cookies, verify=verify, data=data).json()
                print('Added bitstream for item {}'.format(itemID_name))
                files_added = files_added + 1
                print('Total files added: {}'.format(files_added))
                bitstream = requests.get(baseURL+itemID+'/bitstreams', headers=header, cookies=cookies, verify=verify).json()
                uuid = post.get('uuid')
                metadata = requests.get(baseURL+itemID+'/metadata', headers=header, cookies=cookies, verify=verify).json()
                for element in metadata:
                    if element['key'] == 'local.embargo.lift':
                        embargo = element['value']
                        print('Item {} has embargo until {}. Updating policy...'.format(itemID_name, embargo))
                        policy = {}
                        policy['resourceId'] = uuid
                        policy['rpDescription'] = None
                        policy['endDate'] = None
                        policy['startDate'] = embargo
                        policy['resourceType'] = 'bitstream'
                        policy['rpName'] = None
                        policy['action'] = 'READ'
                        policy['epersonId'] = None
                        policy['groupId'] = 'afbf5aff-3555-46eb-859a-328aa5cf10c9'
                        default_policy = requests.get(baseURL+'/rest/bitstreams/'+uuid+'/policy', headers=header, cookies=cookies, verify=verify).json()
                        default_policy = default_policy[0]
                        bitstream_id = default_policy['id']
                        bitstream_id = str(bitstream_id).encode('utf8')
                        antipost = requests.delete(baseURL+'/rest/bitstreams/'+uuid+'/policy/'+bitstream_id, headers=header, cookies=cookies, verify=verify)
                        if antipost.status_code == 200:
                            print('Deleted default policy for item {}'.format(itemID_name))
                        else:
                            print('Failed to delete default policy for item {}'.format(itemID))
                        post = requests.post(baseURL+'/rest/bitstreams/'+uuid+'/policy', headers=header, cookies=cookies, verify=verify, data=json.dumps(policy))
                        if post.status_code == 200:
                            print('Added embargo for item {}'.format(itemID_name))
                            embargo_items = embargo_items + 1

                        else:
                            print('Failed to update for item {}'.format(itemID_name))
                print('Total embargo items: {}'.format(embargo_items))

        # Create provenance notes
        provNote = {}
        provNote['key'] = 'dc.description.provenance'
        provNote['language'] = 'en_US'
        utc = datetime.datetime.utcnow()
        utcTime = utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        bitstreams = requests.get(baseURL+itemID+'/bitstreams', headers=header, cookies=cookies, verify=verify).json()
        bitstreamCount = len(bitstreams)
        provNoteValue = 'Submitted by '+userFullName+' ('+email+') on '+utcTime+' (GMT). No. of bitstreams: '+str(bitstreamCount)
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

        provNote2Value = 'Made available in DSpace on '+utcTime+' (GMT). No. of bitstreams: '+str(bitstreamCount)
        for bitstream in bitstreams:
            fileName = bitstream['name']
            size = str(bitstream['sizeBytes'])
            checksum = bitstream['checkSum']['value']
            algorithm = bitstream['checkSum']['checkSumAlgorithm']
            provNote2Value = provNote2Value+' '+fileName+': '+size+' bytes, checkSum: '+checksum+' ('+algorithm+')'
        provNote2['value'] = provNote2Value

        # Post provenance notes
        provNote = json.dumps([provNote, provNote2])
        post = requests.put(baseURL+itemID+'/metadata', headers=header, cookies=cookies, verify=verify, data=provNote)
        print(post)
        print(' ')

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies, verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print('Total script run time: ', '%d:%02d:%02d' % (h, m, s))
