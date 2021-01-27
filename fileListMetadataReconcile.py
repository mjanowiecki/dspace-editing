import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filename', help='metadata CSV')
parser.add_argument('-f2', '--filename2', help='file listings CSV')
args = parser.parse_args()

if args.filename:
    filename = args.filename
else:
    filename = input('Enter metadata CSV: ')
if args.filename2:
    filename2 = args.filename2
else:
    filename2 = input('Enter file listing CSV: ')

df_files = pd.read_csv(filename2)
fileIdList = df_files.fileIdentifier.tolist()
print('fileIds: '+str(len(fileIdList)))

df_data = pd.read_csv(filename)
metadataIdList = df_data.fileIdentifier.tolist()
print('metadataIds: '+str(len(metadataIdList)))

fileMatches = []
for fileID in fileIdList:
    for metadataID in metadataIdList:
        if fileID == metadataID:
            fileMatches.append(fileID)
print('fileMatches: '+str(len(fileMatches)))

metadataMatches = []
for metadataID in metadataIdList:
    for fileID in fileIdList:
        if fileID == metadataID:
            metadataMatches.append(metadataID)
print('metadataMatches: '+str(len(metadataMatches)))

filesNotInMetadata = set(fileIdList) - set(fileMatches)
print('filesNotInMetadata: '+str(len(filesNotInMetadata)))
if filesNotInMetadata:
    filesNotInMetadata = {'fileItemID': filesNotInMetadata}
    notInMetadata = pd.DataFrame.from_dict(filesNotInMetadata)
    notInMetadata.to_csv('filesNotInMetadata.csv')

metadataWithNoFiles = set(metadataIdList) - set(metadataMatches)
print('metadataWithNoFiles: '+str(len(metadataWithNoFiles)))
if metadataWithNoFiles:
    noFiles = {'fileIdentifier': metadataWithNoFiles}
    df3 = pd.DataFrame.from_dict(noFiles)
    noFilesDF = df3.merge(df_data, how='left', on='fileIdentifier')
    noFilesDF.to_csv('metadataWithNoFiles.csv')

if metadataMatches:
    metadataMatches = {'fileIdentifier': metadataMatches}
    df4 = pd.DataFrame.from_dict(metadataMatches)
    matches = df4.merge(df_data, how='left', on='fileIdentifier')
    matches = matches.merge(df_files, how='left', on='fileIdentifier')
    matches.to_csv('metadataWithFiles.csv')
