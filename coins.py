#!/usr/bin/python3

import os
import configparser
import sys
import requests
import json
import operator

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(ROOT_PATH, 'config.ini')
COINS_FILE = os.path.join(ROOT_PATH, 'coins.ini')
API_URL_TOP_100 = 'https://api.coinmarketcap.com/v1/ticker/'
API_URL_INDIVIDUAL = 'https://api.coinmarketcap.com/v1/ticker/{}/'

sort_dict = {'rank': 'rank', 'name': 'name', 'held value': 'value'}


class Config:
    def __init__(self, ini):
        if os.path.isfile(ini):
            self.config = configparser.RawConfigParser()
            self.config.read(ini)

        else:
            print('{} not found.')
            exit()


class ConfigFile(Config):
    def __init__(self):
        super().__init__(CONFIG_FILE)
        self.currency = self.config['options']['currency'].upper()
        self.dp_fiat = self.config['decimal places']['fiat']
        self.dp_crypto = self.config['decimal places']['crypto']
        self.dp_percent = self.config['decimal places']['percent']
        try:
            self.sort_by = sort_dict[self.config['sorting']['sort by']]

        except KeyError:
            print('Sort key in config file ({}) not recognised. Valid options ' \
                  'are \'rank\', \'name\' and'.format(
                  self.config['sorting']['sort by']))

            print('\'held value\'. Using the default sort key (\'rank\').')
            self.sort_by = 'rank'

        self.sort_direction = self.config['sorting']['sort direction']
        if self.sort_direction.lower() not in ['ascending', 'descending']:
            print('Sort direction in config file ({}) not recognised. Valid options ' \
                  'are \'ascending\' and \'descending\'.'.format(
                  self.config['sorting']['sort direction']))

            print('Using the default sort direction (\'ascending\').')
            self.sort_by = 'ascending'


class CoinsFile(Config):
    def __init__(self):
        super().__init__(COINS_FILE)
        self.coins = {}
        for section in self.config.sections():
            #print(section)
            self.coins[self.config[section]['name'].lower()] = float(self.config[section]['held'])


class Coin:
    total_value = 0
    m_name = m_symbol = m_price = m_price_btc = m_price_eth = 0
    m_held = m_value = m_value_btc = m_value_eth = m_percent = 0

    def __init__(self, data, config, held=None, comparison=None):
        self.data = data
        self.rank = int(self.data['rank'])
        self.name = self.data['name']
        self.symbol = self.data['symbol']
        self.price_usd = self.data['price_usd']
        if config.currency.lower() == 'usd':
            self.local_price = float(self.price_usd)

        else:
            self.local_price = float(self.data['price_{}'.format(config.currency.lower())])

        self.formatted_local_price = '{} {}'.format('{0:,.{p}f}'.format(
            self.local_price, p=config.dp_fiat), config.currency)

        if comparison:
            self.price_in_btc = self.local_price / comparison['bitcoin'].local_price
            self.formatted_price_in_btc = '{} {}'.format('{0:,.{p}f}'.format(
                self.price_in_btc, p=config.dp_crypto), comparison['bitcoin'].symbol.upper())

            self.price_in_eth = self.local_price / comparison['ethereum'].local_price
            self.formatted_price_in_eth = '{} {}'.format('{0:,.{p}f}'.format(
                self.price_in_eth, p=config.dp_crypto), comparison['ethereum'].symbol.upper())

        if held:
            self.held = held
            self.formatted_held = '{0:,.{p}f}'.format(self.held, p=config.dp_crypto)

            self.value = self.local_price * self.held
            Coin.total_value += self.value
            self.formatted_value = '{} {}'.format('{0:,.{p}f}'.format(self.value, p=config.dp_fiat),
                                                    config.currency)

            if len(self.name) > Coin.m_name:
                Coin.m_name = len(self.name)

            if len(self.symbol) > Coin.m_symbol:
                Coin.m_symbol = len(self.symbol)

            if len(self.formatted_local_price) > Coin.m_price:
                Coin.m_price = len(self.formatted_local_price)

            if len(self.formatted_price_in_btc) > Coin.m_price_btc:
                Coin.m_price_btc = len(self.formatted_price_in_btc)

            if len(self.formatted_price_in_eth) > Coin.m_price_eth:
                Coin.m_price_eth = len(self.formatted_price_in_eth)

            if len(self.formatted_held) > Coin.m_held:
                Coin.m_held = len(self.formatted_held)

            if len(self.formatted_value) > Coin.m_value:
                Coin.m_value = len(self.formatted_value)

        if comparison:
            self.value_in_btc = self.value / comparison['bitcoin'].local_price
            self.formatted_value_in_btc = '{} {}'.format('{0:,.{p}f}'.format(self.value_in_btc, p=config.dp_crypto),
                                                         comparison['bitcoin'].symbol)

            self.value_in_eth = self.value / comparison['ethereum'].local_price
            self.formatted_value_in_eth = '{} {}'.format('{0:,.{p}f}'.format(self.value_in_eth, p=config.dp_crypto),
                                                         comparison['ethereum'].symbol)

            if len(self.formatted_value_in_btc) > Coin.m_value_btc:
                Coin.m_value_btc = len(self.formatted_value_in_btc)

            if len(self.formatted_value_in_eth) > Coin.m_value_eth:
                Coin.m_value_eth = len(self.formatted_value_in_eth)

            if len(self.formatted_value) > Coin.m_value:
                Coin.m_value = len(self.formatted_value)

    def get_percent(self):
        self.percent = (self.value / Coin.total_value) * 100
        self.formatted_percent = '{}%'.format('{0:,.{p}f}'.format(self.percent, p=config.dp_percent))

        if len(self.formatted_percent) > Coin.m_percent:
            Coin.m_percent = len(self.formatted_percent)



    @classmethod
    def format_totals(cls):
        cls.formatted_total_value = '{} {}'.format('{0:,.{p}f}'.format(cls.total_value, p=config.dp_fiat),
                                                   config.currency)

        cls.formatted_total_value_in_btc = '{} {}'.format('{0:,.{p}f}'.format(
            cls.total_value / comparison['bitcoin'].local_price,
            p=config.dp_crypto), comparison['bitcoin'].symbol)

        cls.formatted_total_value_in_eth = '{} {}'.format('{0:,.{p}f}'.format(
            cls.total_value / comparison['ethereum'].local_price,
            p=config.dp_crypto), comparison['ethereum'].symbol)

        cls.totals_str = '{:>{v}}{:>{b}}{:>{e}}'.format(cls.formatted_total_value,
                                                        cls.formatted_total_value_in_btc,
                                                        cls.formatted_total_value_in_eth,
                                                        v=cls.m_value+2, b=cls.m_value_btc+2,
                                                        e=cls.m_value_eth+2)


def get_response(url):
    try:
        return requests.get(url, timeout=5).json()

    except:
        print('error')


def calc_percents(results):
    for coin in results:
        coin.percent = (coin.value / Coin.total_value) * 100
        print(coin.name, coin.percent)



def draw_border(name, a, b, c, d, e, f):
    if name == 't':
        return (a + (h*(4+4)) + b
                + (h*(Coin.m_name+4)) + b
                + (h*(Coin.m_price+Coin.m_price_btc+Coin.m_price_eth+8)) + c
                + (h*(Coin.m_held+Coin.m_symbol+5)) + d
                + (h*(Coin.m_value+Coin.m_value_btc+Coin.m_value_eth+8)) + e)

    else:
        return (a + (h*(4+4)) + b
                + (h*(Coin.m_name+4)) + b
                + (h*(Coin.m_price+Coin.m_price_btc+Coin.m_price_eth+8)) + c
                + (h*(Coin.m_held+Coin.m_symbol+5)) + d
                + (h*(Coin.m_value+Coin.m_value_btc+Coin.m_value_eth+8)) + d
                + (h*(Coin.m_percent+4)) + f)

if __name__ == '__main__':
    tl, tm1, tm2, tr = '\u2554', '\u2564', '\u2566', '\u2557'
    ml, mm1, mm2, mr = '\u2560', '\u256a', '\u256c', '\u2563'
    bl, bm1, bm2, br = '\u255a', '\u2567', '\u2569', '\u255d'
    v1, v2, h = '\u2502', '\u2551', '\u2550'
    #print('tl: {}  tm1: {}  tm2: {}  tr: {}'.format(tl, tm1, tm2, tr))
    #print('ml: {}  mm1: {}  mm2: {}  mr: {}'.format(ml, mm1, mm2, mr))
    #print('bl: {}  bm1: {}  bm2: {}  br: {}'.format(bl, bm1, bm2, br))
    #print('v1: {}  v2: {}  h: {}\n'.format(v1, v2, h))
    config = ConfigFile()
    currency = config.currency
    sort_by = config.sort_by
    if currency != 'USD':
        API_URL_TOP_100 += '?convert={}'.format(currency)
        API_URL_INDIVIDUAL += '?convert={}'.format(currency)

    coins = CoinsFile().coins
    page_one = []
    results = []
    comparison = {}
    response = get_response(API_URL_TOP_100)

    # gets comparison data for btc and eth

    for n in ['bitcoin', 'ethereum']:
        try:
            data = [x for x in response if x['name'].lower() == n][0]

        except:
            print('hmm')
            continue

        else:
            comparison[n] = Coin(data, config)

    # gets data for all held coins in the top 100

    for coin in coins:
        for r in response:
            if coin == r['name'].lower() or coin == r['symbol'].lower():
                results.append(Coin(r, config, coins[coin], comparison))
                page_one.append(coin)

    # gets data for any coins that aren't in the top 100 (or to
    # raise an error if they weren't recognised)

    for coin in coins:
        if coin not in page_one:
            r = get_response(API_URL_INDIVIDUAL.format(coin.lower()))
            try:
                if r['error'] == 'id not found':
                    print('No matches found for coin name/symbol: \'{}\'.'.format(coin))

                continue

            except (KeyError, TypeError):
                results.append(Coin(r[0], config, coins[coin], comparison))

    for coin in results:
        coin.get_percent()

    if config.sort_direction == 'ascending':
        sorted_coins = sorted(results, key=operator.attrgetter(config.sort_by))

    else:
        sorted_coins = sorted(results, key=operator.attrgetter(config.sort_by), reverse=True)

    columns = ('{v2}  {:>4}  {v1}  {:{m_name}}  {v1}  {:>{m_price}}  {:>{m_price_btc}}  ' \
               '{:>{m_price_eth}}  {v2}  {:>{m_held}} {:{m_symbol}}  {v2}  {:>{m_value}}  ' \
               '{:>{m_value_btc}}  {:>{m_value_eth}}  {v2}')

    pad = (Coin.m_name + Coin.m_price + Coin.m_price_btc + Coin.m_price_eth +
           Coin.m_held + Coin.m_symbol + 29)

    Coin.format_totals()

    print(draw_border('t', tl, tm1, tm2, tm2, tr, None))
    print(columns.format('Rank', 'Name', 'Price', 'In BTC', 'In ETH',
                         'Held', '', 'Value', 'In BTC', 'In ETH', '',
                         m_name=Coin.m_name, m_price=Coin.m_price, m_price_btc=Coin.m_price_btc,
                         m_price_eth=Coin.m_price_eth, m_held=Coin.m_held,
                         m_symbol=Coin.m_symbol, m_value=Coin.m_value,
                         m_value_btc=Coin.m_value_btc, m_value_eth=Coin.m_value_eth,
                         m_percent=Coin.m_percent, v1=v1, v2=v2))

    columns += '  {:>{m_percent}}  {v2}'

    print(draw_border('m', ml, mm1, mm2, mm2, mm2, tr))
    for coin in sorted_coins:
        print(columns.format('{})'.format(coin.rank), coin.name, coin.formatted_local_price,
                             coin.formatted_price_in_btc, coin.formatted_price_in_eth,
                             coin.formatted_held, coin.symbol, coin.formatted_value,
                             coin.formatted_value_in_btc, coin.formatted_value_in_eth,
                             coin.formatted_percent,
                             m_name=Coin.m_name, m_price=Coin.m_price, m_price_btc=Coin.m_price_btc,
                             m_price_eth=Coin.m_price_eth, m_held=Coin.m_held,
                             m_symbol=Coin.m_symbol, m_value=Coin.m_value,
                             m_value_btc=Coin.m_value_btc, m_value_eth=Coin.m_value_eth,
                             m_percent=Coin.m_percent, v1=v1, v2=v2))

    print(draw_border('b', bl, bm1, bm2, mm2, mm2, br))
    print(' ' * (pad-8) + 'Totals: ' + v2 + Coin.totals_str + '  ' + v2)
    print(' ' * pad + bl + h * (len(Coin.totals_str)+2) + br)
