# -*- coding: utf-8 -*-
import json
import csv


def createMetadataElementCSV(key, valueSource, lang):
    value = row[valueSource].strip()
    if value != '':
        if lang != '':
            metadataElement = {'key': key, 'lang': lang, 'value': value}
            metadata.append(metadataElement)
        elif key == 'dc.date.issued' and '/' in value:
            value = value.replace('/', '--')
            metadataElement = {'key': key, 'lang': lang, 'value': value}
            metadata.append(metadataElement)
        else:
            metadataElement = {'key': key, 'value': value}
            metadata.append(metadataElement)
    else:
        pass


def createMetadataElementCSVSplitField(key, valueSource, lang):
    if row[valueSource] != '':
        if '|' in row[valueSource]:
            values = row[valueSource].split('|')
            for value in values:
                if lang != '':
                    metadataElement = {'key': key, 'lang': lang, 'value': value}
                    metadata.append(metadataElement)
                else:
                    metadataElement = {'key': key, 'value': value}
                    metadata.append(metadataElement)
        else:
            value = row[valueSource]
            if lang != '':
                metadataElement = {'key': key, 'lang': lang, 'value': value}
                metadata.append(metadataElement)
            else:
                metadataElement = {'key': key, 'value': value}
                metadata.append(metadataElement)
    else:
        pass


def createMetadataElementDirect(key, value, lang):
    if lang != '':
        metadataElement = {'key': key, 'lang': lang, 'value': value}
        metadata.append(metadataElement)
    else:
        metadataElement = {'key': key, 'value': value}
        metadata.append(metadataElement)


fileName = input('Enter fileName (including \'.csv\'): ')

with open(fileName) as csvfile:
    reader = csv.DictReader(csvfile)
    counter = 0
    metadataGroup = []
    for row in reader:
        metadata = []
        createMetadataElementCSV('fileIdentifier', '????', '')
        createMetadataElementCSV('dc.contributor.author', '????', 'en_US')
        createMetadataElementCSV('dc.contributor.other', '????', '')
        createMetadataElementCSV('dc.date.issued', '????', '')
        createMetadataElementCSV('local.embargo.lift', '????', '')
        createMetadataElementCSV('local.embargo.terms', '????', '')
        createMetadataElementCSV('dc.description.abstract', '????', 'en_US')
        createMetadataElementCSV('dc.format.extent', '????', '')
        createMetadataElementDirect('dc.format.mimetype', '????', 'en_US')
        createMetadataElementDirect('dc.identifier.other', '????', '')
        createMetadataElementDirect('dc.lang.iso', '????', 'en_US')
        createMetadataElementDirect('dc.publisher', '????', 'en_US')
        createMetadataElementDirect('dc.relation', '????', 'en_US')
        createMetadataElementDirect('dc.rights', '????', 'en_US')
        createMetadataElementCSVSplitField('dc.subject', '????', 'en_US')
        createMetadataElementCSV('dc.title', '????', 'en_US')
        createMetadataElementCSV('dc.type', '????', 'en_US')

        print(len(metadata))
        item = {'metadata': metadata}
        metadataGroup.append(item)
        counter = counter + 1
        print(counter)

f = open('metadata.json', 'w')
json.dump(metadataGroup, f)
