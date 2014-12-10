# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import re
from os.path import join
from datetime import datetime
import settings


class App(object):

    def __init__(self):
        self.data = {}
        self.services = {}

    def _load_data(self, json_data):
        for field in settings.FILE_REQUIRED_FIELDS:
            _value = json_data.get(field, None)
            if _value:
                self.data[field] = _value

    def _is_data_valid(self):
        _fields = (field in self.data
                   for field in settings.FILE_REQUIRED_FIELDS)
        if not all(_fields):
            return False
        _values = '{}:{}'.format(self.data['first_time'].strip(),
                                 self.data['last_time'].strip()).split(':')
        if not all(_values) or len(_values) < 4:
            return False
        try:
            for _v in _values:
                int(_v)
        except ValueError:
            return False
        return True

    def _get_date(self, _hour, _minute):
        return datetime.now().replace(hour=int(_hour),
                                      minute=int(_minute),
                                      second=0,
                                      microsecond=0)

    def _load_configured_times(self):

        _h, _m = self.data['first_time'].split(':')
        self.first_time = self._get_date(_h, _m)

        _h, _m = self.data['last_time'].split(':')
        self.last_time = self._get_date(_h, _m)

    def _is_time_type_in_data(self, _time, _type):

        if _time is None or _type is None:
            return False

        _type = _type.strip()
        if not self.data['types'].get(_type, None):
            return False

        _h, _m = _time.strip().split(':')
        current_time = self._get_date(_h, _m)

        return (self.first_time <= current_time <= self.last_time)

    def _is_tds_valid(self, tds):
        return (tds and len(tds) > 0 and tds[0].input and
                tds[0].input['name'] == 'srv_ida')

    def _get_services_data(self):

        params = {
            'txt_desde': self.data['city_from'],
            'fecha': self.data['date'],
            'fecha_vuelta': self.data['date'],
            'Ida': 'soloida',
            'Submit2': ''
        }

        cities = self.data['cities_to'].split(';')
        services_data = []

        for city in cities:
            params['txt_hasta'] = city
            soup = BeautifulSoup(requests.post(settings.MAIN_URL, params).text)
            trs = soup.find_all('tr', re.compile("fila_"))
            for tr in trs:
                tds = tr.find_all('td')
                if not self._is_tds_valid(tds):
                    continue
                _time, _type = tds[1].text, tds[5].text
                _time = _time.strip()
                _type = _type.strip()

                if self._is_time_type_in_data(_time, _type):
                    services_data.append(
                        {
                            'city_to': city,
                            'seats': self.data['types'][_type],
                            'service': tds[0].input['value']
                        })

        return services_data

    def _get_seats_data(self, services_data):

        params = {
            'desde': self.data['city_from'],
            'fecha': self.data['date'],
            'fecha_vuelta': self.data['date'],
            'op': 'servicio',
            'enviar': ''
        }

        seats = []

        for service_data in services_data:
            params['hasta'] = service_data['city_to']
            params['srv_ida'] = service_data['service']
            soup = BeautifulSoup(requests.post(settings.MAIN_URL, params).text)
            trs = soup.find_all('td', re.compile("libre"))
            for tr in trs:
                if tr.text in service_data['seats'].split(';'):
                    seats.append(tr.text)

        return seats

    def run_app(self):

        file_path = join(settings.FILE_ROOT, settings.FILE_NAME)
        json_data = json.load(open(file_path))

        self._load_data(json_data)
        if not self._is_data_valid():
            print 'invalid config'
            return

        self._load_configured_times()
        services_data = self._get_services_data()
        if not services_data:
            print 'services data not found'
            return

        seats_data = self._get_seats_data(services_data)
        if not seats_data:
            print 'seats not found'
            return

        print seats_data
