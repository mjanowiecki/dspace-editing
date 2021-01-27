import requests
import secrets
import time
import urllib3

secretsVersion = input('To edit production, enter secrets filename: ')
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
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify,
                        params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}
cookiesFileUpload = cookies
status = requests.get(baseURL+'/rest/status', headers=header, cookies=cookies,
                      verify=verify).json()
userFullName = status['fullname']
print('authenticated')

itemIds = ['/rest/items/226e5fcb-0652-4aba-8f13-674533f1bcf3']

directory = ''
filename = 'file_example.jpg'

count = 250
while count < 300:
    count = count + 1
    for item in itemIds:
        bitstream = directory+str(count).zfill(2)+filename
        data = open(bitstream, 'rb')
        link = baseURL+item+'/bitstreams?name='+str(count).zfill(2)+filename
        post = requests.post(link, headers=headerFileUpload, cookies=cookies,
                             verify=verify, data=data).json()
        print(post)
