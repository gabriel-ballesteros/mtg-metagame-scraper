import logging
import os
import re
import requests
import time
import json

logger = logging.getLogger('nodes.data_transform')


def normalize_decklist(path, filename):
    # logger.info('Normalizing data from ' + path + filename + ' to json')
    f = open(path + filename)
    lines = f.readlines()
    decklist = []
    tournament = re.search('\d+_(.+)_\d+', filename).group(1)
    section, card, amount = '', '', 0
    if 'magic' in filename:
        site = 'magic'
        for line in lines:
            if line.isupper():
                section = line.lower().strip().strip('\n')
            elif line.strip().strip('\n').isnumeric():
                amount = int(line)
            elif line[0] != '(':
                card = line.lower().strip().strip('\n')
                decklist.append([section, card, amount])
    elif 'mtgmelee' in filename:
        site = 'mtgmelee'
        for line in lines:
            if line[0].isalpha():
                section = re.match('([A-Z][a-z]+) ', line).group(1).lower().strip().strip('\n')
            else:
                amount = int(re.search('\d+', line).group(0))
                card = re.search('\d+ (.+)', line).group(1).lower().strip().strip('\n')
                decklist.append([section, card, amount])
    f.close()
    return site, tournament, decklist


def update(client, params):
    logger.info('STARTING DATA TRANSFORMATION TO JSON')
    file_list = os.listdir(params.raw_data)
    if '.DS_Store' in file_list:
        file_list.remove('.DS_Store')
    if '.gitkeep' in file_list:
        file_list.remove('.gitkeep')
    for filename in file_list:
        decklist = normalize_decklist(params.raw_data, filename)
        index = re.search('.+_(\d+).txt', filename).group(1)
        name = decklist[0] + '_' + decklist[1] + '_' + index + '.json'
        # logger.info('Saving json file at ' + params.processed_data + name)
        f = open(params.processed_data + name, 'w')
        dic = {'name' + str(index): i for index, i in enumerate([x[1] for x in decklist[2]])}
        result = json.dumps(dic)
        json_request = json.loads('{"identifiers": [' + re.sub('", "', '"}, {"', re.sub('[0-9]', '', result)) + ']}')
        response = requests.post(params.scryfall_collection_url, json=json_request).json()
        response['section'] = [x[0] for x in decklist[2]]
        response['amount'] = [x[2] for x in decklist[2]]
        f.write(json.dumps(response))
        f.close()
        time.sleep(0.1)
    logger.info('Normalized and saved ' + str(len(file_list)) + ' decklists in json files at ' + params.processed_data)


def done(client, params):
    pass
