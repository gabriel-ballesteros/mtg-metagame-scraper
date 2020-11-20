from sqlalchemy import create_engine
import logging

logger = logging.getLogger('client.py')


class Client:
    """
    Connection to the database.

    The current implementation only refers to the PostgreSQL
    database, however, this could be easily enhanced to any
    database at all, including cloud.
    """
    def insert_card(self, uuid, name, set_code, img, card_type, cost, cmc, price_paper, price_online, rarity, color_identity):
        name = name.replace("'", "''")
        card_type = card_type.replace("'", "''")
        if price_online is None:
            price_online = 0
        if price_paper is None:
            price_paper = 0
        return self.conn.execute(f"insert into card (uuid, name, set, img, type, cost, cmc, price_paper, price_online, rarity, color_identity) values ('{uuid}','{name}','{set_code}','{img}','{card_type}','{cost}','{int(cmc)}','{price_paper}','{(price_online)}','{rarity}','{color_identity}') on conflict do nothing;")

    def insert_deck(self, site, date, tournament, pos):
        return self.conn.execute(f"insert into deck (id, date, site, tournament, position) values (DEFAULT,'{date}','{site}','{tournament}','{pos}') on conflict do nothing;")

    def insert_deck_card(self, deck_id, card_id, section, amount):
        section = section.replace("'", "''")
        return self.conn.execute(f"insert into deck_card (deck_id, card_id, section, amount) values ('{deck_id}','{card_id}','{section}','{amount}') on conflict do nothing;")

    def select_max_deck_id(self):
        max_id = self.conn.execute("select max(id) from deck")
        return int(max_id.fetchone().items()[0][1])

    def __init__(self, params):
        """
        Connect to the database.

        Use the information contained in the params.py file
        to connect to the postgreSQL database.
        """
        try:
            self.engine = create_engine(f'postgresql+psycopg2://{params.user}:{params.password}@{params.host}/{params.database}')
            self.conn = self.engine.connect()
        except Exception as e:
            logger.warning('Could not connect to the database on client.py file.')
            logger.warning(f'Verify your credentials for {params.user}.')
            logger.warning(e)
