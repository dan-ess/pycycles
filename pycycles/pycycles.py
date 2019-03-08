from abc import ABCMeta, abstractmethod
from datetime import datetime
from enum import Enum
import re
from typing import Any, Dict, List

from requests_html import HTMLSession

# types
# TODO: make generic type to handle one/many responses: Dict[str, Any] and List[Dict[str, Any]]
RequestParams = Dict[str, str]
Response = Dict[str, Any]
Cycleport = Dict[str, Any]
Cycleports = List[Cycleport]
Cycle = Dict[str, Any]
Cycles = List[Cycle]


class ServiceArea(Enum):
    CHIYODA = 1
    CHUO = 2
    MINATO = 3
    KOTO = 4
    SHINJUKU = 5
    BUNKYOU = 6
    DAITA = 7
    SHIBUYA = 8
    NAZO = 9
    SHINAGAWA = 10


class BaseRequest(metaclass=ABCMeta):
    BASE_URL = 'https://tcc.docomo-cycle.jp/cycle/TYO/cs_web_main.php'

    @abstractmethod
    def auth_params(self) -> RequestParams:
        pass

    @abstractmethod
    def request_params(self) -> RequestParams:
        pass

    def params(self) -> RequestParams:
        return {**self.auth_params(), **self.request_params()}

    def make_request(self):
        session = HTMLSession()
        response = session.post(BaseRequest.BASE_URL, data=self.params())
        return response

    @abstractmethod
    def parse_response(self, r):
        pass

    def response(self):
        response = self.make_request()
        parsed_response = self.parse_response(response)
        return parsed_response


class LoginRequest(BaseRequest):
    _username: str
    _password: str

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def auth_params(self) -> RequestParams:
        return {
            'MemberID': self._username,
            'Password': self._password,
        }

    def request_params(self) -> RequestParams:
        return {
            'GarblePrevention': 'ＰＯＳＴデータ',
            'EventNo': '21401',
        }

    def parse_response(self, r):
        session_id = r.html.find("input[name='SessionID']", first=True)
        return { 'SessionID': session_id.attrs.get('value') }


class SessionRequest(BaseRequest):
    _username: str
    _session_id: str

    def __init__(self, username: str, session_id: str) -> None:
        super().__init__()
        self._username = username
        self._session_id = session_id

    def auth_params(self) -> RequestParams:
        return {
            'MemberID': self._username,
            'SessionID': self._session_id
        }


class CycleportsRequest(SessionRequest):
    _area: ServiceArea

    def __init__(self, username: str, session_id: str, area: ServiceArea):
        super().__init__(username, session_id)
        self._area = area

    def request_params(self) -> RequestParams:
        return {
            'EventNo': '25706',
            'UserID': 'TYO',
            'GetInfoNum': '100',
            'GetInfoTopNum': '1',
            'MapType': '1',
            'MapCenterLat': '',
            'MapCenterLon': '',
            'MapZoom': '13',
            'EntServiceID': 'TYO0001',
            'AreaID': self._area.value
        }

    def parse_response(self, r):
        cycleports = []

        for form in r.html.find('.sp_view form'):
            cycleport = { input.attrs['name']: input.attrs['value'] for input in form.find('input') }
            cycleport['formName'] = form.attrs['name']
            name_element = form.find('.port_list_btn a', first=True)
            matches = re.findall('\.([^\\n]*)', name_element.text)

            if len(matches) == 2:
                cycleport['name_ja'] = matches[0]
                cycleport['name_en'] = matches[1]
                cycleports.append(cycleport)

        return cycleports


class CyclesRequest(SessionRequest):
    cycleport: Cycleport

    def __init__(self, username: str, session_id: str, cycleport: Cycleport) -> None:
        super().__init__(username, session_id)
        self._cycleport = cycleport

    def request_params(self) -> RequestParams:
        return {
            'EventNo': '25701',
            'UserID': 'TYO',
            'GetInfoNum': '40',
            'GetInfoTopNum': '1',
            'ParkingEntID': 'TYO',
            'ParkingID': self._cycleport['ParkingID'],
            'ParkingLat': self._cycleport['ParkingLat'],
            'ParkingLon': self._cycleport['ParkingLon'],
        }

    def parse_response(self, r):
        cycles = []

        for form in r.html.find('.sp_view form'):
            cycle = { input.attrs['name']: input.attrs['value'] for input in form.find('input') }
            display_name = form.find('.cycle_list_btn a', first=True)
            cycle['displayname'] = display_name.text
            cycle['cycleport'] = self._cycleport
            cycles.append(cycle)

        return cycles


class RentalRequest(SessionRequest):
    cycle: Cycle

    def __init__(self, username: str, session_id: str, cycle: Cycle) -> None:
        super().__init__(username, session_id)
        self._cycle = cycle

    def request_params(self) -> RequestParams:
        return {
            'EventNo': '25901',
            'UserID': 'TYO',
            'CenterLat': self._cycle['CenterLat'],
            'CenterLon': self._cycle['CenterLon'],
            'CycLat': self._cycle['CycLat'],
            'CycLon': self._cycle['CycLon'],
            'CycleID': self._cycle['CycleID'],
            'AttachID': self._cycle['AttachID'],
            'CycleTypeNo': self._cycle['CycleTypeNo'],
            'CycleEntID': self._cycle['CycleEntID'],
        }

    def parse_response(self, r):
        pin = ''
        pin_element = r.html.find('.main_inner_wide font', first=True)
        if pin_element:
            pin = pin_element.text.strip()

        return {
            'rental_date': datetime.now(),
            'cycle': self._cycle,
            'cycleport': self._cycle['cycleport'],
            'pin': pin
        }


class CancellationRequest(SessionRequest):
    def request_params(self) -> RequestParams:
        return {
            'EventNo': '27901',
            'UserID': 'TYO',
        }

    def parse_response(s, r):
        return { 'success': 'true' }


class Client:
    _username: str
    _password: str
    _session_id: str

    def __init__(self, username, password):
        self._username = username
        self._password = password

    def login(self):
        response = LoginRequest(self._username, self._password).response()
        self._session_id = response['SessionID']
        return response

    def cycleports(self, area: ServiceArea):
        response = CycleportsRequest(self._username, self._session_id, area).response()
        return response

    def cycles(self, cycleport: Cycleport):
        response = CyclesRequest(self._username, self._session_id, cycleport).response()
        return response

    def rent(self, cycle: Cycle):
        response = RentalRequest(self._username, self._session_id, cycle).response()
        return response

    def cancel(self):
        response = CancellationRequest(self._username, self._session_id).response()
        return response
