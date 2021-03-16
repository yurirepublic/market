"""
此文件用于提供数据中心服务
"""
import json
import traceback
import requests


class DataCenterException(Exception):
    pass


class Data(object):
    """
    数据的抽象，数据中心存储的全是此对象
    """

    def __init__(self):
        self.data = None  # 存储的数据

        self.callback = []  # 更新数据后会触发的回调函数队列

    def update(self, data):
        self.data = data
        for func in self.callback:
            try:
                func(data)
            except Exception:
                print(traceback.format_exc())

    def append_callback(self, func):
        self.callback.append(func)

    def get(self):
        return self.data


class Client(object):
    """
    数据中心的客户端服务
    """

    def __init__(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
        self.url = 'https://{}:{}/data'.format(
            config['data_center_http_client_connect_ip'],
            config['data_center_http_client_connect_port']
        )
        self.password = config['password']

    def set(self, key, value):
        data = {
            'password': self.password,
            'mode': 'SET',
            'msg': json.dumps({
                'key': key,
                'value': value
            })
        }
        r = requests.post(self.url, data=data)
        if r.status_code != 200:
            raise DataCenterException(r.text)
        if r.json()['msg'] != 'success':
            raise DataCenterException(r.text)

    def get(self, key):
        data = {
            'password': self.password,
            'mode': 'GET',
            'msg': json.dumps({
                'key': key
            })
        }
        r = requests.post(self.url, data=data)
        if r.status_code != 200:
            raise DataCenterException(r.text)
        if r.json()['msg'] != 'success':
            raise DataCenterException(r.text)
        return r.json()['data']

    def get_all(self):
        data = {
            'password': self.password,
            'mode': 'ALL'
        }
        r = requests.post(self.url, data=data)
        if r.status_code != 200:
            raise DataCenterException(r.text)
        if r.json()['msg'] != 'success':
            raise DataCenterException(r.text)
        return r.json()['data']
