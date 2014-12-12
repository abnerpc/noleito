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

    def _is_data_valid(self):
        """
        Check if the data loaded from config file is valid
        """

        # check if all required fields are present
        _fields = (field in self.data
                   for field in settings.FILE_REQUIRED_FIELDS)
        if not all(_fields):
            return False

        # check if all time fields are valid numbers
        _times = ''.join(self.data['first_time'].split(':') +
                         self.data['last_time'].split(':'))
        if not _times or len(_times) < 8:
            return False
        try:
            int(_times)
        except ValueError:
            return False

        return True

    def _get_date(self, _hour, _minute):
        """
        Returns a datetime object with the hour and minute provided
        """
        return datetime.now().replace(hour=int(_hour),
                                      minute=int(_minute),
                                      second=0,
                                      microsecond=0)

    def _load_configured_times(self):
        """
        Put the first and last time in an instance variable
        """
        _h, _m = self.data['first_time'].split(':')
        self.first_time = self._get_date(_h, _m)

        _h, _m = self.data['last_time'].split(':')
        self.last_time = self._get_date(_h, _m)

    def _is_time_and_type_valid(self, _time, _type):
        """
        Checks if the times and types provided in the config file are valid
        """
        if _time is None or _type is None:
            return False

        _type = _type.strip()
        if not self.data['types'].get(_type, None):
            return False

        _h, _m = _time.strip().split(':')
        current_time = self._get_date(_h, _m)

        return (self.first_time <= current_time <= self.last_time)

    def _is_tds_valid(self, tds):
        """
        Check for valid tds name
        """
        return (tds and len(tds) > 0 and tds[0].input and
                tds[0].input['name'] == 'srv_ida')

    def _get_services_data(self):
        """
        Returns only the services that matches the configuration file
        """

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

                _time, _type = tds[1].text.strip(), tds[5].text.strip()

                if self._is_time_and_type_valid(_time, _type):
                    services_data.append(
                        {
                            'city_to': city,
                            'time': _time,
                            'seats': self.data['types'][_type],
                            'service': tds[0].input['value']
                        })

        return services_data

    def _get_available_seats(self, services_data):
        """
        Returns an array with the details of matched seats available
        """
        params = {
            'desde': self.data['city_from'],
            'fecha': self.data['date'],
            'fecha_vuelta': self.data['date'],
            'op': 'servicio',
            'enviar': ''
        }

        availables = []

        for service_data in services_data:

            params['hasta'] = service_data['city_to']
            params['srv_ida'] = service_data['service']
            soup = BeautifulSoup(requests.post(settings.MAIN_URL, params).text)
            trs = soup.find_all('td', re.compile("libre"))
            seats = [tr.text for tr in trs
                     if tr.text in service_data['seats'].split(';')]
            if len(seats) > 0:
                service_data['seats'] = seats
                availables.append(service_data)

        return availables

    def run_app(self):
        """
        Start point for the app execution
        """

        file_path = join(settings.FILE_ROOT, settings.FILE_NAME)
        self.data = json.load(open(file_path))

        if not self._is_data_valid():
            print 'invalid config'
            return

        self._load_configured_times()
        services_data = self._get_services_data()
        if not services_data:
            print 'services data not found'
            return

        seats_data = self._get_available_seats(services_data)
        if not seats_data:
            print 'seats not found'
            return

        print seats_data
