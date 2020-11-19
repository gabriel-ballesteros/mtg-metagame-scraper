import logging
import os
import re
import requests
import time
import json

logger = logging.getLogger('nodes.data_transform')


def normalize_decklist(path, filename):
    logger.info('Normalizing data from ' + path + filename + ' to json')
    f = open(path + filename)
    lines = f.readlines()
    decklist = []
    tournament = re.search('_(.+)_', filename).group(1)
    section, card, amount = '', '', 0
    if 'magic' in filename:
        site = 'magic'
        for line in lines:
            if line.isupper():
                section = line.lower().strip().strip('\n')
            elif line.strip().strip('\n').isnumeric():
                amount = int(line)
            elif line[0] != '(':
                card = line.lower().strip().strip('\n').replace(' ', '+')
                decklist.append([section, card, amount])
    elif 'mtgmelee' in filename:
        site = 'mtgmelee'
        for line in lines:
            if line[0].isalpha():
                section = re.match('([A-Z][a-z]+) ', line).group(1).lower().strip().strip('\n')
            else:
                amount = int(re.search('\d+', line).group(0))
                card = re.search('\d+ (.+)', line).group(1).lower().strip().strip('\n').replace(' ', '+')
                decklist.append([section, card, amount])
    f.close()
    return site, tournament, decklist


def update(client, params):
    logger.info('STARTING DATA TRANSFORMATION TO JSON')
    file_list = os.listdir(params.raw_data)
    if '.DS_Store' in file_list:
        file_list.remove('.DS_Store')
    for filename in file_list:
        decklist = normalize_decklist(params.raw_data, filename)
        cards = []
        index = re.search('.+_(\d+).txt', filename).group(1)
        name = decklist[0] + '_' + decklist[1] + '_' + index + '.json'
        logger.info('Saving json file at ' + params.processed_data + name)
        f = open(params.processed_data + name, 'w')
        for card in decklist[2]:
            response = requests.get(params.scryfall_exact_name_url + card[1]).json()
            time.sleep(0.2)
            print(card[1])
            try:
                a_card = {
                    'name': response['name'],
                    'cmc': response['cmc'],
                    'cost': response['mana_cost'],
                    'type': response['type_line'],
                    'set': response['set'],
                    'rarity': response['rarity'],
                    'image': response['image_uris']['png'],
                    'price_paper': response['prices']['usd'],
                    'price_online': response['prices']['tix']
                }
            except KeyError:
                a_card = {
                    'name': response['name'],
                    'cmc': response['cmc'],
                    'cost': response['card_faces'][0]['mana_cost'],
                    'type': response['type_line'],
                    'set': response['set'],
                    'rarity': response['rarity'],
                    'image': response['card_faces'][0]['image_uris']['png'],
                    'price_paper': response['prices']['usd'],
                    'price_online': response['prices']['tix']
                }

            cards.append([card[0], a_card, card[2]])
        f.write(json.dumps(cards))
        f.close()


def done(client, params):
    pass
