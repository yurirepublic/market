"""
此文件用于提供数据中心服务\n
说明，所有数据采用多key索引，称之为tag\n
更新数据时，会更新所有满足tag的值\n
获取数据时，也会获取满足所有tag的值\n
"""
import json
import traceback
import requests
from typing import Dict, List, Set, Union, Callable
import threading


class DataCenterException(Exception):
    pass


class Data(object):
    """
    数据的抽象，数据中心存储的全是此对象
    """

    def __init__(self):
        self._data = None  # 存储的数据
        self._tags = set()  # 此数据的tag

        self.callback: List[Callable] = []  # 更新数据后会触发的回调函数队列

    def update(self, value):
        self._data = value
        for func in self.callback:
            try:
                handle = threading.Thread(target=func, args=(value,))
                handle.start()
            except Exception:
                print(traceback.format_exc())

    def set_tags(self, tags: Union[list, set]):
        """
        设置数据的tags，会自动将list转为set
        """
        self._tags = set(tags)

    def get_tags(self) -> Set[str]:
        return self._tags

    def append_update_callback(self, func):
        self.callback.append(func)

    def get(self):
        return self._data


class Server(object):
    """
    数据中心的服务端
    """

    def __init__(self):
        self.database: Dict[str, Set[Data]] = {}  # 每个tag下都存放对应tag下的set

    def _select(self, tags: Union[List[str], Set[str]]) -> Set[Data]:
        """
        根据对应标签，选择出满足的对象
        """
        keys = self.database.keys()
        res = None
        for tag in tags:
            if tag not in keys:
                return set()
            if res is None:
                res = self.database[tag]
            else:
                res = res & self.database[tag]
        return res

    def update(self, tags: Union[List[str], Set[str]], value):
        """
        依据tag更新值
        """
        # 根据tag筛选数据集合
        data_set = self._select(tags)
        # 如果筛选出的数据为空，则新建一个对应tag的数据
        if len(data_set) == 0:
            data_obj = Data()
            data_obj.update(value)
            data_obj.set_tags(tags)
            for tag in tags:
                try:
                    self.database[tag].add(data_obj)
                except KeyError:
                    self.database[tag] = set()
                    self.database[tag].add(data_obj)
        else:
            # 为每个数据更新
            for e in data_set:
                e.update(value)

    def append_update_callback(self, tags: Union[List[str], Set[str]], func: Callable):
        """
        依据tag更新刷新回调
        """
        # 根据tag筛选数据集合
        data_set = self._select(tags)
        # 如果筛选出的数据为空，则新建一个对应tag的数据
        if len(data_set) == 0:
            data_obj = Data()
            data_obj.set_tags(tags)
            for tag in tags:
                try:
                    self.database[tag].add(data_obj)
                except KeyError:
                    self.database[tag] = set()
                    self.database[tag].add(data_obj)
        else:
            # 为每个数据更新
            for e in data_set:
                e.append_update_callback(func)

    def get(self, tags: Union[List[str], Set[str]]):
        """
        依据tag获取值，如果有精确值则返回精确值，没有精确值则返回模糊值\n
        精确值返回 xxx\n
        模糊值返回 {unique_tag: xxx, unique_tag2: xxx}\n
        没有多出来的tag则不返回这个数据
        """
        tags = set(tags)
        data_set = self._select(tags)
        if len(data_set) == 0:
            return None
        elif len(data_set) == 1:
            for e in data_set:
                return e.get()
        else:
            # 若数据的tag比tags+1，则以多出的tag做键返回字典
            res = {}
            for e in data_set:
                if len(tags) + 1 == len(e.get_tags()):
                    print(e.get_tags())
                    unique_tag_set = e.get_tags() - tags
                    unique_tag = None
                    # 此时unique_tag虽然是set，但是必然只有一个值
                    for x in unique_tag_set:
                        unique_tag = x
                    res[unique_tag] = e.get()
            return res

    def get_all(self):
        """
        返回所有的数据\n
        格式为[{'tags': [], 'data': xxx}, ...]
        """
        # 数据库所有的tag
        tag_all = self.database.keys()
        # 将所有的数据取个并集
        data_all = set()
        for tag in tag_all:
            data_all = self.database[tag] | data_all
        # 处理成返回格式
        res = []
        for e in data_all:
            res.append({
                'tags': list(e.get_tags()),
                'data': e.get()
            })
        return res


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

    def update(self, tags: List[str], value):
        data = {
            'password': self.password,
            'mode': 'SET',
            'msg': json.dumps({
                'tags': tags,
                'value': value
            })
        }
        r = requests.post(self.url, data=data)
        if r.status_code != 200:
            raise DataCenterException(r.text)
        if r.json()['msg'] != 'success':
            raise DataCenterException(r.text)

    def get(self, tags: List[str]):
        data = {
            'password': self.password,
            'mode': 'GET',
            'msg': json.dumps({
                'tags': tags
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
