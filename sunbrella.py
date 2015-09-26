import urllib2
import json
import yaml
from os.path import expanduser, isfile
import datetime
from dateutil import parser
from pytz import reference

CACHE_PATH = expanduser('~/.sunbrella_cache.json')


def get_cache(api_key, latitude, longitude):
    if isfile(CACHE_PATH):
        try:
            cache = json.load(open(CACHE_PATH))
        except:
            return None, None
        data = cache['data']
        headers = cache['headers']
        ####
        return data, headers
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
    elif isfile('.sunbrella.yaml'):
        config = yaml.load(open('.sunbrella.yaml'))
    else:
        raise Exception('No config file found')
    data, headers = get_weather(**config)
