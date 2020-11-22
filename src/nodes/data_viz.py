import logging
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from math import pi
from wordcloud import (WordCloud, get_single_color_func)
import numpy as np
from PIL import Image

logger = logging.getLogger('nodes.data_viz')


class SimpleGroupedColorFunc(object):
    def __init__(self, color_to_words, default_color):
        self.word_to_color = {word: color
                              for (color, words) in color_to_words.items()
                              for word in words}

        self.default_color = default_color

    def __call__(self, word, **kwargs):
        return self.word_to_color.get(word, self.default_color)


class GroupedColorFunc(object):
    def __init__(self, color_to_words, default_color):
        self.color_func_to_words = [
            (get_single_color_func(color), set(words))
            for (color, words) in color_to_words.items()]

        self.default_color_func = get_single_color_func(default_color)

    def get_color_func(self, word):
        try:
            color_func = next(
                color_func for (color_func, words) in self.color_func_to_words
                if word in words)
        except StopIteration:
            color_func = self.default_color_func

        return color_func

    def __call__(self, word, **kwargs):
        return self.get_color_func(word)(word, **kwargs)


def plot_decks_colors(client):
    query = '''select 1 as uno, d.id as id,
case when string_agg(c.color_identity, '') like '%W%' then 1 else 0 end as white,
case when string_agg(c.color_identity, '') like '%U%' then 1 else 0 end as blue,
case when string_agg(c.color_identity, '') like '%B%' then 1 else 0 end as black,
case when string_agg(c.color_identity, '') like '%R%' then 1 else 0 end as red,
case when string_agg(c.color_identity, '') like '%G%' then 1 else 0 end as green
from deck as d,card as c, deck_card as dc
where dc.deck_id = d.id
and dc.card_id = c.uuid
group by d.id;
    '''
    decks_colors = pd.read_sql_query(query, client.engine)
    df = decks_colors.groupby(by='uno').agg(white=('white', 'sum'),
                          blue=('blue', 'sum'),
                        black=('black', 'sum'),
                          red=('red', 'sum'),
                          green=('green', 'sum'))
    fig = plt.figure(figsize=(6,6))
    ax = plt.subplot(polar='True')
    categories = ['White','Blue','Black','Red','Green']
    N = len(categories)
    values = df.iloc[0].tolist()
    values += values[:1]

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    plt.polar(angles, values, marker='.')
    plt.fill(angles, values, alpha=0.3)

    plt.xticks(angles[:-1], categories)

    ax.set_rlabel_position(0)
    top = max(df.iloc[0].tolist())
    plt.yticks([100, 200, 300, 400], color='grey', size=10)
    plt.ylim(0, top)
    plt.savefig('../viz/decks_colors.png')


def plot_nonland_name_cloud(client):
    query = '''select case when c.name like '%//%' then split_part(c.name, '//', 1) else c.name end as name
, c.color_identity as color
,sum(dc.amount) as amount
from card as c, deck_card as dc
where c.uuid = dc.card_id
and c.type not like '%Land%'
group by c.name, c.color_identity
order by 3 desc'''
    df = pd.read_sql_query(query, client.engine)
    names = df.iloc[:, 0].tolist()
    count = df.iloc[:, 2].tolist()

    d = {}
    for index in range(len(names)):
        d[names[index]] = count[index]
    white = []
    blue = []
    black = []
    red = []
    green = []
    for index, row in df.iterrows():
        if row['color'] == 'W':
            white.append(row['name'])
        elif row['color'] == 'U':
            blue.append(row['name'])
        elif row['color'] == 'B':
            black.append(row['name'])
        elif row['color'] == 'R':
            red.append(row['name'])
        elif row['color'] == 'G':
            green.append(row['name'])
    color_to_words = {}
    color_to_words['yellow'] = white
    color_to_words['blue'] = blue
    color_to_words['violet'] = black
    color_to_words['red'] = red
    color_to_words['green'] = green

    wc = WordCloud(collocations=False, background_color='white', width=1000, height=800).generate_from_frequencies(d)

    #plt.figure(figsize=(20, 15))
    default_color = 'black'

    grouped_color_func = GroupedColorFunc(color_to_words, default_color)

    wc.recolor(color_func=grouped_color_func)

    plt.figure(figsize=(20, 10), facecolor='k')
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.imshow(wc, interpolation="bilinear")
    
    plt.savefig('../viz/nonland_name_cloud.png')


def plot_types_count(client):
    query = '''select SPLIT_PART(c.type, ' — ', 1), count(1)
from card as c
where c.type not like '%Basic Land%'
group by SPLIT_PART(c.type, ' — ', 1);
    '''
    df = pd.read_sql_query(query, client.engine)
    df = df.sort_values(df.columns[1],ascending=False)
    types = df.iloc[:, 0].tolist()
    values = df.iloc[:, 1].tolist()
    plt.figure(figsize=(12,10))

    # make barplot
    sns.barplot(y=types, x=values)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Card type count", size=18)
    plt.tight_layout()
    plt.savefig("../viz/types_count.png", dpi=100)


def plot_set_count(client):
    query = '''select c.set, count(1)
from card as c
where c.type not like '%Basic Land%'
group by c.set;
'''
    df = pd.read_sql_query(query, client.engine)
    df = df.sort_values(df.columns[1],ascending=False)
    sets = df.iloc[:, 0].tolist()
    values = df.iloc[:, 1].tolist()
    plt.figure(figsize=(8,10))

    # make barplot
    sns.barplot(y=sets, x=values)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Card set count", size=18)
    plt.tight_layout()
    plt.savefig("../viz/sets_count.png", dpi=100)


def plot_price_by_rarity(client):
    query = '''select c.rarity, avg(c.price_paper)
from card as c
where c.type not like '%Basic Land%'
group by c.rarity
    '''
    df = pd.read_sql_query(query, client.engine)
    df = df.sort_values(df.columns[1],ascending=False)
    rarity = df.iloc[:, 0].tolist()
    values = df.iloc[:, 1].tolist()
    plt.figure(figsize=(8,10))

    # make barplot
    sns.barplot(x=rarity, y=values)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Avg prices by rarity in USD", size=18)
    plt.tight_layout()
    plt.savefig("../viz/avg_price_rarity.png", dpi=100)


def plot_winner_price_in_time(client):
    query = '''select d.date, sum(c.price_paper)
from card as c, deck as d, deck_card as dc
where c.uuid = dc.card_id and d.id = dc.deck_id
and d.position = 1
group by d.date
order by 1 desc'''
    df = pd.read_sql_query(query, client.engine)
    #df = df.sort_values(df.columns[1],ascending=False)
    date = df.iloc[:, 0].tolist()
    prices = df.iloc[:, 1].tolist()
    plt.figure(figsize=(16,8))

    # make barplot
    sns.lineplot(x=date, y=prices)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Prices of winner decks by date", size=18)
    plt.tight_layout()
    plt.savefig("../viz/avg_price_by_date.png", dpi=100)


def plot_max_price_in_time(client):
    query = '''select d.date, sum(c.price_paper)
from card as c, deck as d, deck_card as dc
where c.uuid = dc.card_id and d.id = dc.deck_id
and d.position = 1
group by d.date
order by 1 desc'''
    df = pd.read_sql_query(query, client.engine)
    #df = df.sort_values(df.columns[1],ascending=False)
    date = df.iloc[:, 0].tolist()
    prices = df.iloc[:, 1].tolist()
    plt.figure(figsize=(16,8))

    # make barplot
    sns.lineplot(x=date, y=prices)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Prices of winner decks by date in USD", size=18)
    plt.tight_layout()
    plt.savefig("../viz/avg_price_by_date.png", dpi=100)
    query = '''with decks as (
select d.date as date, d.id as id,sum(c.price_paper) as price
from card as c, deck as d, deck_card as dc
where c.uuid = dc.card_id and d.id = dc.deck_id
group by d.date, d.id
order by 1 desc
)
select date, max(price) as price from decks group by date order by 1 desc;'''
    df = pd.read_sql_query(query, client.engine)
    #df = df.sort_values(df.columns[1],ascending=False)
    date = df.iloc[:, 0].tolist()
    prices = df.iloc[:, 1].tolist()
    plt.figure(figsize=(16,8))

    # make barplot
    sns.lineplot(x=date, y=prices)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Most expensive decks by date in USD", size=18)
    plt.tight_layout()
    plt.savefig("../viz/max_price_by_date.png", dpi=100)


def update(client, params):
    #plot_decks_colors(client)
    #plot_types_count(client)
    #plot_set_count(client)
    #plot_price_by_rarity(client)
    #plot_winner_price_in_time(client)
    #plot_max_price_in_time(client)
    plot_nonland_name_cloud(client)


def done(client, params):
    pass
