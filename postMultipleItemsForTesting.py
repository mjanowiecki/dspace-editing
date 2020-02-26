import json
import requests
import secrets
from datetime import datetime
import time
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

itemIds = ['/rest/items/226e5fcb-0652-4aba-8f13-674533f1bcf3']

location = 'C:/Users/mjanowi3/cygwin64/home/mjanowi3/my-repositories/testing/'
filename = 'file_example.jpg'

count = 250
while count < 300:
    count = count + 1
    for item in itemIds:
        bitstream = location+str(count).zfill(2)+filename
        data = open(bitstream, 'rb')
        post = requests.post(baseURL+item+'/bitstreams?name='+str(count).zfill(2)+filename, headers=headerFileUpload, cookies=cookies, verify=verify, data=data).json()
        print(post)
