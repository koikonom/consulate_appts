#!/usr/bin/env python

import datetime
import glob
import json
import os
import re
import sqlite3
import time
import traceback


from bs4 import BeautifulSoup
import requests
import twitter

category_map = {
    1: 'Passports',
    2: 'Power of Attorney',
    3: 'Military',
    4: 'Certificates',
    5: 'Permanent Residence',
    6: 'Moving to Greece',
    7: 'Nationality',
    8: 'Notarizations'
}


class InvalidConfig(Exception):
    pass


def get_cfg_file():
    if 'EMBASSY_CONFIG' in os.environ:
        return os.getenv('EMBASSY_CONFIG')
    home_dir = os.getenv('HOME')
    return os.path.join(home_dir, '.embassy.json')


def has_available(text):
    if 'no appointments available' in text.lower():
        return (0, None)
    av_re = r'.*Available (\d+) starting on ([0-9/]+).*'
    match = re.match(av_re, text.replace(u'\xa0', ''))
    if match:
        return match.groups()
    return (None, None)


def get_twitter_creds(settings):
    out = {}
    try:
        for x in ['consumer_key', 'consumer_secret',
                  'access_token_key', 'access_token_secret']:
            out[x] = settings[x]
    except KeyError, e:
        msg = 'Missing key in config: {}'.format(e.message)
        raise InvalidConfig(msg)
    return out


def get_appts(settings):
    try:
        db = sqlite3.connect('./lol.db')
        c = db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS appts (date number,'''
                  '''kind number, amount number, next_date text)''')
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537'\
            '.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

        data = requests.get(
            'http://www.greekembassy.org.uk/en-gb/Reservations',
            headers={'User-Agent': ua})
        if data.status_code != 200:
            return None
        soup = BeautifulSoup(data.text, 'html.parser')
        availability_table = soup.select(
            '#dnn_ctr484_MakeReservation_availabilityTableCell')[0]
        x = availability_table.select(
            '.DNNSpecialists_Modules_Reservations_Normal')
        out = []
        for idx, tag in enumerate(x):
            (amt, next_date) = has_available(tag.text)
            out.append((int(time.time()), idx+1, amt, next_date))
            send_message(settings, idx+1, amt, next_date)
        c.executemany('''INSERT into appts VALUES (?, ?, ?, ?)''', out)
        db.commit()
    except Exception:
        traceback.print_exc()
    finally:
        db.close()


def send_message(settings, idx, amt, next_date):
    creds = get_twitter_creds(settings)
    api = twitter.Api(**creds)
    if idx in settings['categories'] and amt > 0:
        locks = glob.glob('{}/{}*'.format(settings['lock_dir'],
                                          '{}_{}'.format(idx, amt)))
        if len(locks) > 1:
            print 'Multiple locks found: {}'.format(locks)
        nxt = datetime.datetime.strptime(next_date, '%d/%m/%Y')
        for lock in locks:
            appt_date = datetime.datetime.strptime(
                os.path.basename(lock).split('_', 2)[2],
                '%d_%m_%Y')
            if appt_date <= nxt:
                return
            os.unlink(lock)
        msg = 'New appointment available. Type: {}, Date: {}'.format(
            category_map[idx], next_date)
        api.PostDirectMessage(msg, screen_name=settings['notify'])
        lockfile = os.path.join(settings['lock_dir'], '{}_{}_{}'.format(
            idx, amt, next_date.replace('/', '_')))
        open(lockfile, 'w').close()


if __name__ == '__main__':
    settings = json.load(open(get_cfg_file()))
    while True:
        get_appts(settings)
        time.sleep(60)
