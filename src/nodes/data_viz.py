import logging
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from math import pi
from wordcloud import (WordCloud, get_single_color_func)
import numpy as np
from PIL import Image
import squarify
import os

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
                                            blue=('blue', 'sum'), black=('black', 'sum'),
                                            red=('red', 'sum'), green=('green', 'sum'))
    fig = plt.figure(figsize=(6, 6))
    ax = plt.subplot(polar='True')
    categories = ['White', 'Blue', 'Black', 'Red', 'Green']
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
    plt.yticks([top / 5, top / 5 * 2, top / 5 * 3, top / 5 * 4, top], color='grey', size=10, labels=[])
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
    multi = []
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
        elif len(row['color']) > 1:
            multi.append(row['name'])
    color_to_words = {}
    color_to_words['#bdaa00'] = white
    color_to_words['#0099d1'] = blue
    color_to_words['#9a00bd'] = black
    color_to_words['#ff0000'] = red
    color_to_words['#119100'] = green
    color_to_words['#ff69f5'] = multi
    mask = np.array(Image.open('../viz/cards-fan.jpg'))
    wc = WordCloud(collocations=False, background_color='white', width=1000, height=800, mask=mask).generate_from_frequencies(d)
    default_color = '#424142'
    grouped_color_func = SimpleGroupedColorFunc(color_to_words, default_color)
    wc.recolor(color_func=grouped_color_func)
    plt.figure(figsize=(20, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig('../viz/nonland_name_cloud.png', bbox_inches='tight')


def plot_nonland_name_bar(client):
    query = '''select case when c.name like '%//%' then split_part(c.name, '//', 1) else c.name end as name
,case when length(c.color_identity) > 1 then '#ff69f5' else
case when c.color_identity = 'W' then '#bdaa00' else
case when c.color_identity = 'U' then '#0099d1' else
case when c.color_identity = 'B' then '#9a00bd' else
case when c.color_identity = 'R' then '#ff0000' else
case when c.color_identity = 'G' then '#119100' else
'grey'
end
end
end
end
end
end as color
,sum(dc.amount) as amount
from card as c, deck_card as dc
where c.uuid = dc.card_id
and c.type not like '%Land%'
group by c.name, c.color_identity
order by 3 desc
limit 20'''
    df = pd.read_sql_query(query, client.engine)
    name = df.iloc[:, 0].tolist()
    colors = df.iloc[:, 1].tolist()
    number = df.iloc[:, 2].tolist()
    plt.figure(figsize=(12, 8))
    sns.barplot(y=name, x=number, palette=colors)
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Nonland card name count", size=18)
    plt.tight_layout()
    # ax.set_xticklabels(name)
    # plt.subplots_adjust(bottom=0.2)
    plt.grid(axis='x')
    plt.savefig("../viz/nonland_name_count.png", dpi=100)


def plot_types_square(client):
    query = '''select case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else
SPLIT_PART(c.type,' — ',1) end as basic_type, sum(dc.amount) as amount
from card as c, deck_card as dc
where c.type not like '%Basic Land%'
and c.uuid = dc.card_id
group by basic_type
order by 2 desc;
    '''
    df = pd.read_sql_query(query, client.engine)
    types = df.iloc[:, 0].tolist()
    number = df.iloc[:, 1].tolist()
    plt.figure(figsize=(17, 8))
    types = [x.replace(' ', '\n') for x in types]
    squarify.plot(sizes=number, label=types[:9], alpha=0.8, text_kwargs={'fontsize': 16})
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("../viz/types_square.png", dpi=100)


def plot_types_bar(client):
    query = '''select case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else
SPLIT_PART(c.type,' — ',1) end as basic_type, sum(dc.amount) as amount
from card as c, deck_card as dc
where c.type not like '%Basic Land%'
and c.uuid = dc.card_id
group by basic_type
order by 2 desc;'''
    df = pd.read_sql_query(query, client.engine)
    types = df.iloc[:, 0].tolist()
    number = df.iloc[:, 1].tolist()
    plt.figure(figsize=(12, 8))
    sns.barplot(y=types, x=number, palette='muted')
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Card type count", size=18)
    plt.tight_layout()
    # ax.set_xticklabels(name)
    # plt.subplots_adjust(bottom=0.2)
    plt.grid(axis='x')
    plt.savefig("../viz/types_count.png", dpi=100)


def plot_set_type_count(client):
    query = '''select c.set
,case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else
SPLIT_PART(c.type,' — ',1) end as basic_type
,sum(dc.amount) as cards
from card as c, deck_card as dc
where c.uuid = dc.card_id
and c.type not like '%Basic Land%' and set in ('znr','iko','m21','thb','eld')
group by c.set, basic_type
order by 1,2;
'''
    df = pd.read_sql_query(query, client.engine)
    sets = df.iloc[:, 0].tolist()
    types = df.iloc[:, 1].tolist()
    number = df.iloc[:, 2].tolist()
    plt.figure(figsize=(12, 8))
    sets = [a.upper() for a in sets]
    # make barplot
    sns.barplot(x=sets, y=number, hue=types, palette='tab10')
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Card set count", size=18)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("../viz/sets_type_count.png", dpi=100)


def plot_amount_price_by_rarity(client):
    query = '''select c.rarity as rarity
, sum(dc.amount) as amount
,round(avg(dc.amount * c.price_paper),2) as avg_price
from card as c, deck_card as dc
where c.uuid = dc.card_id
and c.type not like '%Basic Land%'
group by 1
order by 2 desc;
    '''
    df = pd.read_sql_query(query, client.engine)

    df[['amount']].plot(kind='bar')
    df['avg_price'].plot(secondary_y=True, color='r')

    ax = plt.gca()
    # plt.xlim([-width, len(m1_t['normal'])-width])
    ax.set_xticklabels((df['rarity']))

    plt.savefig("../viz/amount_price_rarity.png", dpi=100)


def plot_cmc_count(client):
    query = '''select
c.cmc as cmc,sum(dc.amount) as number
from card as c, deck_card as dc
where c.uuid = dc.card_id
and case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else
SPLIT_PART(c.type,' — ',1) end not like '%Land%'
group by c.cmc
order by 1'''
    df = pd.read_sql_query(query, client.engine)
    cmcs = df['cmc'].tolist()
    number = df['number'].tolist()
    plt.figure(figsize=(12, 8))
    sns.barplot(x=cmcs, y=number, palette='flare')
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Card CMC distribution", size=18)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("../viz/cmc_count.png", dpi=100)


def plot_cmc_type_count(client):
    query = '''select
c.cmc as cmc
,case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end as basic_type
,sum(dc.amount) as number
from card as c, deck_card as dc
where c.uuid = dc.card_id
and case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end not like '%Land%'
group by c.cmc, basic_type
order by 1'''
    df = pd.read_sql_query(query, client.engine)
    cmcs = df['cmc'].tolist()
    types = df['basic_type']
    number = df['number'].tolist()
    plt.figure(figsize=(12, 8))
    sns.barplot(x=cmcs, y=number, hue=types, palette='muted')
    # set labels
    # plt.ylabel("Sets", size=15)
    # plt.ylabel("Card count", size=15)
    plt.title("Card type distribution by CMC", size=18)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("../viz/cmc_type_count.png", dpi=100)


def plot_winner_price_in_tournament(client):
    query_winners = '''select SPLIT_PART(d.tournament,'-',3) as tournament, sum(c.price_paper) as price
from card as c, deck as d, deck_card as dc
where c.uuid = dc.card_id and d.id = dc.deck_id
and d.position = 1
and d.site != 'magic'
group by d.tournament
order by 1 desc;'''
    query_avg = '''with tournaments_decks as (select SPLIT_PART(d.tournament,'-',3) as tournament, d.id as deck_id, sum(c.price_paper) as price
from card as c, deck as d, deck_card as dc
where c.uuid = dc.card_id and d.id = dc.deck_id
and d.site != 'magic'
group by d.tournament, d.id)
select tournament, round(avg(price),2) as price
from tournaments_decks
group by tournament
order by 1 desc;'''
    df_w = pd.read_sql_query(query_winners, client.engine)
    df_w['deck'] = 'winner'
    df = pd.read_sql_query(query_avg, client.engine)
    df['deck'] = 'average'
    result = pd.concat([df_w, df])

    plt.figure(figsize=(14, 10))
    s = sns.barplot(data=result, x='tournament', y='price', hue='deck')
    s.set_xlabel('')
    plt.ylabel('Deck price in USD', size=14)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig("../viz/avg_winner_price.png")


def plot_correlation(client):
    query = '''select CAST(SPLIT_PART(d.tournament,'-',3) as INTEGER) as tou, CAST(d.position as INTEGER) as pos, sum(c.price_paper * dc.amount) as price,

sum(case when (c.color_identity) like '%W%' then 1 else 0 end) as white,
sum(case when (c.color_identity) like '%U%' then 1 else 0 end) as blue,
sum(case when (c.color_identity) like '%B%' then 1 else 0 end) as black,
sum(case when (c.color_identity) like '%R%' then 1 else 0 end) as red,
sum(case when (c.color_identity) like '%G%' then 1 else 0 end) as green,

ROUND((CAST (SUM(c.cmc) as NUMERIC) / CAST (SUM(dc.amount) as NUMERIC)),2) as cmc_ratio,

sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) like '%Creature%' then dc.amount else 0 end) as creatures,
sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) = 'Instant' then dc.amount else 0 end) as instants,
sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) = 'Sorcery' then dc.amount else 0 end) as sorceries,
sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) in ('Enchantment','Legendary Enchantment') then dc.amount else 0 end) as enchantments,
sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) in ('Artifact','Legendary Artifact') then dc.amount else 0 end) as artifacts,
sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) = 'Legendary Planeswalker' then dc.amount else 0 end) as planeswalkers,
sum(case when (case when c.type like '%//%' then SPLIT_PART(SPLIT_PART(c.type,' // ',1),' — ',1 ) else SPLIT_PART(c.type,' — ',1) end) in ('Land','Basic Land') then dc.amount else 0 end) as lands,

sum(dc.amount) as total_cards
from card as c, deck as d, deck_card as dc
where c.uuid = dc.card_id and d.id = dc.deck_id
and d.site != 'magic'
group by d.tournament, d.id, d.position;
    '''
    df = pd.read_sql_query(query, client.engine)
    correlation = df.corr()

    plt.figure(figsize=(16, 8))
    sns.heatmap(data=correlation, annot=True)
    plt.title("Correlation between variables", size=18)
    plt.savefig("../viz/correlation.png", dpi=100)


def plot_winner_colors(client):
    query = '''select 1 as uno, d.id as id,
case when string_agg(c.color_identity, '') like '%W%' then 1 else 0 end as white,
case when string_agg(c.color_identity, '') like '%U%' then 1 else 0 end as blue,
case when string_agg(c.color_identity, '') like '%B%' then 1 else 0 end as black,
case when string_agg(c.color_identity, '') like '%R%' then 1 else 0 end as red,
case when string_agg(c.color_identity, '') like '%G%' then 1 else 0 end as green
from deck as d,card as c, deck_card as dc
where d.position = 1
and dc.deck_id = d.id
and dc.card_id = c.uuid
group by d.id;
    '''
    decks_colors = pd.read_sql_query(query, client.engine)
    df = decks_colors.groupby(by='uno').agg(white=('white', 'sum'),
                                            blue=('blue', 'sum'), black=('black', 'sum'),
                                            red=('red', 'sum'), green=('green', 'sum'))
    fig = plt.figure(figsize=(6, 6))
    ax = plt.subplot(polar='True')
    categories = ['White', 'Blue', 'Black', 'Red', 'Green']
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
    plt.yticks([top / 5, top / 5 * 2, top / 5 * 3, top / 5 * 4, top], color='grey', size=10, labels=[])
    plt.ylim(0, top)
    plt.savefig('../viz/winner_colors.png')


def update(client, params):
    logger.info('CREATING VISUALIZATIONS')
    plot_decks_colors(client)
    plot_nonland_name_cloud(client)
    plot_nonland_name_bar(client)
    plot_types_square(client)
    plot_types_bar(client)
    plot_set_type_count(client)
    plot_cmc_count(client)
    plot_cmc_type_count(client)
    plot_winner_colors(client)
    plot_winner_price_in_tournament(client)
    plot_correlation(client)
    plot_amount_price_by_rarity(client)

    logger.info('Created ' + str(len(os.listdir('../viz/')) - 2) + ' visualization figures at ../viz/')


def done(client, params):
    pass
