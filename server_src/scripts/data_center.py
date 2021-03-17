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
import time


class DataCenterException(Exception):
    pass


class Data(object):
    """
    数据的抽象，数据中心存储的全是此对象
    """

    def __init__(self):
        self._data = None  # 存储的数据
        self._timestamp: int = 0  # 数据的timestamp
        self._tags = set()  # 此数据的tag

        self.callback: List[Callable] = []  # 更新数据后会触发的回调函数队列

    def update(self, value, timestamp=None):
        """
        更新数据，如果不带timestamp，则会自动获取timestamp\n
        如果欲更新的数据timestamp比当前的小，则会拒绝更新\n
        """
        now_timestamp = time.time() * 1000
        if timestamp is not None and timestamp > self._timestamp:
            self._data = value
            self._timestamp = timestamp
        elif timestamp is None and now_timestamp > self._timestamp:
            self._data = value
            self._timestamp = now_timestamp
        else:
            return
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
        """
        为了避免每次精确的update都要对集合进行各种操作
        self.cache的职责就是将tag排序，加入横线，变成asset-main-usdt的形式作为key
        以此来快速索引单个数据
        """
        self.cache: Dict[str, Data] = {}  # 对数据的哈希式缓存

    def _select(self, tags: Union[List[str], Set[str]]) -> Set[Data]:
        """
        根据对应标签，选择出满足的对象\n
        注！此操作极度消耗性能！尽可能用在模糊查询上，勿用在精确查询上
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

    @staticmethod
    def tag2key(tags: Union[List[str], Set[str]]):
        """
        将tag排序后插入横线
        """
        tags = list(tags)
        tags.sort(key=lambda x: x)
        return '-'.join(tags)

    def _cache_select(self, tags: Union[List[str], Set[str]]) -> Data:
        """
        会将tag转为缓存用的kay，并在cache查询Data对象\n
        如果没有，则会引发KeyError异常
        :return: 查询到的Data对象
        """
        key = self.tag2key(tags)
        return self.cache[key]

    def update(self, tags: Union[List[str], Set[str]], value, timestamp=None):
        """
        依据tag更新值
        """
        # 根据tag筛选数据集合
        try:
            self._cache_select(tags).update(value, timestamp=timestamp)
        except KeyError:
            # 还没有对应的数据则新建一个Data对象
            data_obj = Data()
            data_obj.update(value, timestamp=timestamp)
            data_obj.set_tags(tags)
            # 将对象放入缓存索引和tag索引
            self.cache[self.tag2key(tags)] = data_obj
            for tag in tags:
                try:
                    self.database[tag].add(data_obj)
                except KeyError:
                    self.database[tag] = set()
                    self.database[tag].add(data_obj)

        # data_set = self._select(tags)
        # # 如果筛选出的数据为空，则新建一个对应tag的数据
        # if len(data_set) == 0:
        #     data_obj = Data()
        #     data_obj.update(value, timestamp=timestamp)
        #     data_obj.set_tags(tags)
        #     for tag in tags:
        #         try:
        #             self.database[tag].add(data_obj)
        #         except KeyError:
        #             self.database[tag] = set()
        #             self.database[tag].add(data_obj)
        # else:
        #     # 为每个数据更新
        #     for e in data_set:
        #         e.update(value, timestamp=timestamp)

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
                'data': e.get(),
                'timestamp': e.get_timestamp()
            })
        return res


class WebsocketClient(object):
    """
    数据中心的websocket接口客户端
    """

class HTTPClient(object):
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

        self.session = requests.session()

    def update(self, tags: List[str], value, timestamp: int = None):
        data = {
            'password': self.password,
            'mode': 'SET',
            'msg': json.dumps({
                'tags': tags,
                'value': value,
                'timestamp': timestamp
            })
        }
        r = self.session.post(self.url, data=data)
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
        r = self.session.post(self.url, data=data)
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
        r = self.session.post(self.url, data=data)
        if r.status_code != 200:
            raise DataCenterException(r.text)
        if r.json()['msg'] != 'success':
            raise DataCenterException(r.text)
        return r.json()['data']
