from os.path import abspath, dirname

MAIN_URL = 'https://vendas.expressodeprata.com.br/cgi-bin/br5.cgi'

FILE_ROOT = dirname(dirname(abspath(__file__)))
FILE_NAME = 'config.json'
FILE_REQUIRED_FIELDS = [
    'city_from',
    'cities_to',
    'date',
    'first_time',
    'last_time',
    'types']
