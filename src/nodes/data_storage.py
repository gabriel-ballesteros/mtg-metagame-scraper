import logging
import os
import json
import re

logger = logging.getLogger('nodes.data_storage')


def update(client, params):
    logger.info('STARTING DATA POPULATION TO DB AT ' + params.database + ' DATABASE')
    file_list = os.listdir(params.processed_data)
    if '.DS_Store' in file_list:
        file_list.remove('.DS_Store')
    if '.gitkeep' in file_list:
        file_list.remove('.gitkeep')
    for filename in file_list:
        f = open(params.processed_data + filename, 'r')
        deck = json.loads(f.readline())
        f.close()
        site = re.search('^(\w+)_\d{4}-', filename).group(1)
        date = re.search('^\w+_(\d{4}-\d{2}-\d{2})_', filename).group(1)
        tournament = re.search('\d{4}-\d{2}-\d{2}_([0-9a-z\-]+)_\d+.json', filename).group(1)
        pos = re.search('_(\d+).json', filename).group(1)
        client.insert_deck(site, date, tournament, pos)
        for index, card in enumerate(deck['data']):
            try:
                uuid = card['id']
                name = card['name']
                set_code = card['set']
                img = card['image_uris']['png']
                card_type = card['type_line']
                cost = card['mana_cost']
                cmc = card['cmc']
                price_paper = card['prices']['usd']
                price_online = card['prices']['tix']
            except KeyError:
                uuid = card['id']
                name = card['name']
                set_code = card['set']
                img = card['card_faces'][0]['image_uris']['png']
                card_type = card['type_line']
                cost = card['card_faces'][0]['mana_cost']
                cmc = card['cmc']
                price_paper = card['prices']['usd']
                price_online = card['prices']['tix']
            finally:
                client.insert_card(uuid, name, set_code, img, card_type, cost, cmc, price_paper, price_online)
                deck_id = client.select_max_deck_id()
                client.insert_deck_card(deck_id, uuid, deck['section'][index], deck['amount'][index])


def done(client, params):
    pass
