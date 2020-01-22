import csv
import argparse
from datetime import datetime
import ast

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='enter filename with csv.')
parser.add_argument('-b', '--batch', help='Batch letter to name outputs.')
args = parser.parse_args()

if args.file:
    filename = args.file
else:
    filename = input('Enter filename (including \'.csv\'): ')
if args.batch:
    batch = args.batch
else:
    batch = input('Enter batch letter: ')

dt_stamp = datetime.now().strftime('%Y-%m-%d %H.%M.%S')

subjectFile = 'subjectsCombined'+'_Batch'+batch+'_'+dt_stamp+'.csv'

f = csv.writer(open(subjectFile, 'w'))
f.writerow(['uri']+['oldKey']+['oldSubject']+['newKey']+['newSubject'])

f2 = csv.writer(open('errors'+'_Batch'+batch+'_'+dt_stamp+'.csv', 'w'))
f2.writerow(['uri']+['oldSubject']+['cleanedSubject']+['results']+['selection'])

error = 0
total_count = 0

with open(filename, 'r', encoding='UTF-8', errors='strict') as metadataFile:
    itemMetadata = csv.DictReader(metadataFile)
    for row in itemMetadata:
        uris = row['uri'].split(',')
        total_count = total_count + len(uris)
        if total_count % 10 == 0:
            print(total_count)
        for uri in uris:
            oldKey = 'dc.subject'
            oldSubject = row['dc.subject']
            cleanedSubject = row['cleanedSubject']
            type = row['type']
            results = row['results'].strip()
            selection = row['selection'].strip()
            try:
                selection = int(selection)
            except ValueError:
                try:
                    selection = ast.literal_eval(selection)
                except:
                    selection = str(selection)
            newKey = ''
            newSubject = ''
            if type == 'fast_exact':
                newSubject = results
                newKey = 'dc.subject.fast'
                f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
            elif type == 'mesh_exact':
                newSubject = results
                newKey = 'dc.subject.mesh'
                f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
            elif type == 'fast' and isinstance(selection, int):
                results = ast.literal_eval(results)
                selection = selection - 1
                newSubject = results[selection]
                newKey = 'dc.subject.fast'
                f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
            elif type == 'fast' and isinstance(selection, list):
                results = ast.literal_eval(results)
                newSubject = []
                for x in selection:
                    x = int(x)
                    subject = results[x-1]
                    newSubject.append(subject)
                newKey = 'dc.subject.fast'
                newSubject = '|'.join(newSubject)
                f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
            elif selection == 'new selection':
                newSubject = results
                if type == 'fast':
                    newKey = 'dc.subject.fast'
                    f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
                elif type == 'mesh':
                    newKey = 'dc.subject.mesh'
                    f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
                else:
                    print('Error found')
                    error = error + 1
                    f2.writerow([uri]+[oldSubject]+[cleanedSubject]+[results]+[selection])
            elif type == 'not found' or selection == 'none':
                newSubject = cleanedSubject
                newKey = 'dc.subject'
                f.writerow([uri]+[oldKey]+[oldSubject]+[newKey]+[newSubject])
            else:
                print('Error found')
                error = error + 1
                f2.writerow([uri]+[oldSubject]+[cleanedSubject]+[results]+[selection])

print('{} total rows'.format(total_count))
print('{} errors found'.format(error))
