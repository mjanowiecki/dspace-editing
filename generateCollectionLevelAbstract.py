import json
import requests
import secrets
import csv
import argparse
import urllib3

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
parser.add_argument('-f', '--fileNameCSV', help='the metadata CSV file.')
parser.add_argument('-i', '--handle', help='handle of the collection.')
args = parser.parse_args()

if args.fileNameCSV:
    fileNameCSV = args.fileNameCSV
else:
    fileNameCSV = input('Enter the metadata CSV file (including \'.csv\'): ')
if args.handle:
    handle = args.handle
else:
    handle = input('Enter collection handle: ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify
skippedCollections = secrets.skippedCollections

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
collection = requests.get(endpoint, headers=header, cookies=cookies, verify=verify).json()
collectionID = collection['uuid']
print(collection)

# Enter abstract text here
abstractText = ''
aspaceText = ''

seriesTitles = []

with open(fileNameCSV) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        seriesTitle = row['Series title'].strip()
        if seriesTitle != '' and seriesTitle not in seriesTitles:
            seriesTitles.append(seriesTitle)

seriesLinks = []


for seriesTitle in seriesTitles:
    handleEdited = handle.replace('/', '%2F')
    editedSeriesTitle = seriesTitle.replace(' ', '+')
    try:
        editedSeriesTitle = editedSeriesTitle.replace('"', '&quot;')
    except KeyError:
        pass
    seriesLink = '<li><a href="https://jscholarship.library.jhu.edu/discover?scope='+handleEdited+'&query=%22'+editedSeriesTitle+'%22&sort_by=dc.title_sort&order=asc&submit=">'+seriesTitle+'</a></li>'
    seriesLinks += seriesLink

abstractText = '<p>'+abstractText+'</p>'
aspaceText = '<p>'+aspaceText+'</p>'
seriesLinks = '<ul>'+seriesLinks+'</ul>'
introductoryText = abstractText + aspaceText + seriesLinks

collection['introductoryText'] = introductoryText
collection = json.dumps(collection)


print(collection)
collLink = baseURL+'/rest/collections/'+collectionID
post = requests.put(collLink, headers=header, cookies=cookies, verify=verify,
                    data=collection)
print(post)

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)
