#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import urllib2
import json
import yaml
from os.path import expanduser, isfile
import datetime
from dateutil import parser
from pytz import reference

CACHE_PATH = expanduser('~/.sunbrella_cache.json')

def pntime(time):
    return datetime.datetime.fromtimestamp(time, tz=reference.LocalTimezone())

def get_cache(api_key, latitude, longitude):
    if isfile(CACHE_PATH):
        try:
            cache = json.load(open(CACHE_PATH))
        except:
            return None, None
        data = cache['data']
        headers = cache['headers']
        if latitude == data['latitude'] and longitude == data['longitude']:
            now = datetime.datetime.now(tz=reference.LocalTimezone())
            if now < parser.parse(headers['expires']):
                return data, headers
    return None, None


def get_weather(api_key, latitude, longitude, cache_expiry=None):
    data, headers = get_cache(api_key, latitude, longitude)
    if data is not None and headers is not None:
        return data, headers
    url = 'https://api.forecast.io/forecast/%s/%s,%s' % (
        api_key, latitude, longitude)
    response = urllib2.urlopen(url)
    headers = dict(response.info())
    data = json.loads(response.read())
    json.dump({'data': data, 'headers': headers}, open(CACHE_PATH, 'w'))
    return data, headers


if __name__ == '__main__':
    if isfile('config.yaml'):
        config = yaml.load(open('config.yaml'))
    elif isfile(expanduser('~/.sunbrella.yaml')):
        config = yaml.load(open(expanduser('~/.sunbrella.yaml')))
    else:
        raise Exception('No config file found')
    data, headers = get_weather(api_key=config['api_key'], latitude=config['latitude'], longitude=config['longitude'])

    precipitation_tolerance = config.get('precipitation_tolerance') or 0.002
    temperature_low_tolerance = config.get('temperature_low_tolerance') or 60
    temperature_high_tolerance = config.get('temperature_high_tolerance') or 72
    lookahead= config.get('lookahead') or 60


    now = datetime.datetime.now(tz=reference.LocalTimezone())
    points = [data['currently']] + data['minutely']['data'] + data['hourly']['data'] # + data['daily']['data']
    soon_points = [p for p in points if pntime(p['time']) < (now + datetime.timedelta(minutes=lookahead))]

    tolerance_violations = []
    for d in soon_points:
        if d['precipProbability'] >0 and d['precipIntensity'] > precipitation_tolerance:
            tolerance_violations.append(
                    (pntime(d['time']), 'precipitation', (d['precipProbability'], d['precipIntensity']))
            )
        if 'temperature' in d and d['apparentTemperature'] < temperature_low_tolerance:
            tolerance_violations.append(
                    (pntime(d['time']), 'temperature low', (d['apparentTemperature']))
            )
        if 'temperature' in d and d['apparentTemperature'] > temperature_high_tolerance:
            tolerance_violations.append(
                    (pntime(d['time']), 'temperature high', (d['apparentTemperature']))
            )

    icons = {
            'precipitation':'☔️ ',
            'temperature high': '😎 ',
            'temperature low': '⛄️ ',
            }

    displayed = []
    string = ''
    for time, tolerance, level in tolerance_violations:
        if tolerance not in displayed:
            to = max(0, (time-now).total_seconds())
            hours = int(round(to/3660, 0))
            string+=icons[tolerance]
            string += str(hours)
            displayed.append(tolerance)
    print string
