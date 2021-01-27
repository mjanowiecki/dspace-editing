import json
import requests
import secrets
import time
import csv
from datetime import datetime
import urllib3
import argparse


# This script is meant to replace values in individual items from a CSV file.
# This is good for changing the values of keys without duplicates,
# like 'dc.title' or 'dc.type'. This script cannot not change what the keys
# are called -- it only changes the keys' values. So dc.title would remain as
# dc.title, but the title may change from 'Bee' to 'Bumblebee'.
# Warning: This script will change the value for all duplicate, matching keys.
# For instance, if you have 3 dc.subject keys, the scripts will change the
# values of all of them to whatever is in the CSV.
# You don't want three identical 'dc.subject': 'bumblebees' pairs!


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

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fileName', help='the metadata CSV file.')
parser.add_argument('-i', '--keystofind', help='handle of the collection.')
args = parser.parse_args()

if args.fileName:
    fileName = args.fileName
else:
    fileName = input('Enter the metadata CSV file (including \'.csv\'): ')
if args.keystofind:
    keystofind = args.keystofind
else:
    keystofind = input("Enter keys where the value will be replaced: ")

    # To do spaces in argparse, format like this: dc.subject\ dc.title
    # For this script to work, your 'keystofind' must correspond to your
    # column headers in the CSV fileName.

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

dt = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

f = csv.writer(open(filePath+'replacedValue_'+dt+'.csv', 'w'))

items_total = 0

keystofind = keystofind.split()
print(keystofind)


with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        itemMetadataProcessed = []
        original_element_count = 0
        element_count = 0
        itemID = row['link'].strip()
        decade = row['dc.subject'].strip()
        logInformation = [itemID]
        print(itemID)
        link = baseURL+str(itemID)+'/metadata'
        itemMetadata = requests.get(link, headers=header, cookies=cookies,
                                    verify=verify).json()
        if decade != 'not converted':
            subjectElement = {'key': 'dc.subject', 'language': 'en_US', 'value': decade}
            itemMetadataProcessed.append(subjectElement)
            element_count = element_count + 1
            logInformation.append(decade)

            provNote = "{} added as 'dc.subject' by batch process on {}.".format(decade, dt)
            provNoteElement = {}
            provNoteElement['key'] = 'dc.description.provenance'
            provNoteElement['value'] = provNote
            provNoteElement['language'] = 'en_US'
            itemMetadataProcessed.append(provNoteElement)
            element_count = element_count + 1

        elif decade == 'not converted':
            logInformation.append('No subject added')
        for element in itemMetadata:
            element.pop('schema', None)
            element.pop('element', None)
            element.pop('qualifier', None)
            original_element_count = original_element_count + 1
            languageValue = element['language']
            oldKey = element['key']
            if oldKey in keystofind:
                oldValue = element['value']
                newKey = oldKey
                newValue = row[oldKey].strip()
                if newValue == '':
                    provNote = "{} deleted by batch process on {}.".format(oldKey, dt)
                    provNoteElement = {}
                    provNoteElement['key'] = 'dc.description.provenance'
                    provNoteElement['value'] = provNote
                    provNoteElement['language'] = 'en_US'
                    itemMetadataProcessed.append(provNoteElement)
                    element_count = element_count + 1
                    logInformation.append('dc.description.abstract deleted')
                else:
                    updatedMetadataElement = {}
                    updatedMetadataElement['key'] = newKey
                    updatedMetadataElement['value'] = newValue
                    updatedMetadataElement['language'] = languageValue
                    itemMetadataProcessed.append(updatedMetadataElement)
                    element_count = element_count + 1

                    provNote = "{}: {} was replaced by {}: {} by batch process on {}.".format(oldKey, oldValue, newKey, newValue, dt)
                    provNoteElement = {}
                    provNoteElement['key'] = 'dc.description.provenance'
                    provNoteElement['value'] = provNote
                    provNoteElement['language'] = 'en_US'
                    itemMetadataProcessed.append(provNoteElement)
                    element_count = element_count + 1
                    addToLog = [oldKey, oldValue, newKey, newValue]
                    logInformation.extend(addToLog)
            elif oldKey == 'dc.identifier.uri':
                uri = element['value']
                itemMetadataProcessed.append(element)
                element_count = element_count + 1
                logInformation.append(uri)
            else:
                itemMetadataProcessed.append(element)
                element_count = element_count + 1

        # print("This item originally had {} elements, but now has {} elements.
        # Remember that each updated value comes with an additional provenance
        # element. So if you expect 2 value changes, there should be 2 added
        # elements.".format(original_element_count, element_count))

        itemMetadataProcessed = json.dumps(itemMetadataProcessed,
                                           sort_keys=True)

        delete = requests.delete(link, headers=header, cookies=cookies,
                                 verify=verify)
        print(delete)
        post = requests.put(link, headers=header, cookies=cookies,
                            verify=verify, data=itemMetadataProcessed)
        print(post)
        addToLog = [delete, post]
        logInformation.extend(addToLog)
        f.writerow(logInformation)
        if post.status_code == 200:
            items_total = items_total + 1
            print('Edited item {}; {} total items edited'.format(itemID, items_total))
            print('')
        else:
            print('Failed to update for item {}'.format(itemID))
            print('')

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies,
                       verify=verify)
