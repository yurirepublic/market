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
import queue
import random

# 引入websocket相关
import websockets
import asyncio

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.loads(f.read())


def issubset(a: Set, b: Set):
    """
    判断参数1和参数2是否有子集关系
    """
    temp = a & b
    if temp == a or temp == b:
        return True
    else:
        return False


class DataCenterException(Exception):
    pass


class DataWrapper(object):
    """
    数据的抽象，数据中心存储的全是此对象
    """

    def __init__(self):
        self._data = None  # 存储的数据
        self._timestamp: int = 0  # 数据的timestamp
        self._tags = set()  # 此数据的tag

    def update(self, value, timestamp=None):
        """
        更新数据，如果不带timestamp，则会自动获取timestamp\n
        如果欲更新的数据timestamp比当前的小，则会拒绝更新\n
        """
        now_timestamp = time.time() * 1000

        # 根据时间戳判断是否要更新数据
        if timestamp is not None and timestamp > self._timestamp:
            self._data = value
            self._timestamp = timestamp
        elif timestamp is None and now_timestamp > self._timestamp:
            self._data = value
            self._timestamp = now_timestamp
        else:
            # 数据没有更新旧就直接返回
            return

    def set_tags(self, tags: Union[list, set]):
        """
        设置数据的tags，会自动将list转为set
        """
        self._tags = set(tags)

    def get_tags(self) -> Set[str]:
        return self._tags

    def get_timestamp(self) -> int:
        return self._timestamp

    def get(self):
        return self._data


class CallbackWrapper(object):
    """
    回调的包装器，和DataWrapper是一个东西，只不过这里面装的是回调
    """

    def __init__(self, func: Callable[[DataWrapper], None], tags):
        self.func = func
        if not isinstance(tags, set):
            tags = set(tags)
        self.tags = tags


class Server(object):
    """
    数据中心的服务端，纯Python对象，需要使用接口来远程使用
    """

    def __init__(self):
        self.threading_lock = threading.Lock()
        with self.threading_lock:
            """
            此字典以tag为key,set为value，set里放置DataWrapper
            查询时将不同tag的set取交集，就可以获取查询到的DataWrapper
            """
            self.database: Dict[str, Set[DataWrapper]] = {}

            """
            为了避免每次精确的update都要对集合进行缓慢的交集操作
            self.cache的职责就是将tag排序，加入横线，变成asset-main-usdt的形式作为key
            以此来快速索引单个数据
            """
            self.cache: Dict[str, DataWrapper] = {}

            """
            此字典与database特别相似，但是存储的是CallbackWrapper
            update时，取并集，再遍历结果查询其CallbackWrapper的tag是否为要update的tag的子集
            以此来判断是否要触发此Callback
            例如asset main usdt，此tag就可以触发asset main这个CallbackWrapper
            """
            self.callback: Dict[str, Set[CallbackWrapper]] = {}

            """
            此列表存储的是订阅所有数据的回调
            """
            self.subscribe: Set[CallbackWrapper] = set()

    def _select(self, tags: Set[str]) -> Set[DataWrapper]:
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

    def _callback(self, tags: Set[str]) -> Set[CallbackWrapper]:
        """
        根据输入的tags，返回匹配到的CallbackWrapper
        """
        res: Set[CallbackWrapper] = set()
        for tag in tags:
            if tag in self.callback.keys():
                res = res | self.callback[tag]
        # 逐个判断是否为子集
        temp = set()
        for e in res:
            if issubset(e.tags, tags):
                temp.add(e)
        return temp

    @staticmethod
    def tag2key(tags: Set[str]):
        """
        将tag排序后插入横线
        """
        tags = list(tags)
        tags.sort(key=lambda x: x)
        return '-'.join(tags)

    def _cache_select(self, tags: Set[str]) -> DataWrapper:
        """
        会将tag转为缓存用的kay，并在cache查询Data对象\n
        如果没有，则会引发KeyError异常
        :return: 查询到的Data对象
        """
        key = self.tag2key(tags)
        return self.cache[key]

    def update(self, tags: Set[str], value, timestamp=None):
        """
        依据tag更新值
        """
        # 根据tag筛选数据集合
        data_obj = None
        with self.threading_lock:
            try:
                data_obj = self._cache_select(tags)
                data_obj.update(value, timestamp=timestamp)
            except KeyError:
                # 还没有对应的数据则新建一个Data对象
                data_obj = DataWrapper()
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
        # 使用多线程来异步触发回调
        callbacks = self._callback(tags)
        for e in callbacks:
            try:
                threading.Thread(target=lambda: e.func(data_obj)).start()
            except Exception:
                print(traceback.format_exc())
        for e in self.subscribe:
            try:
                threading.Thread(target=lambda: e.func(data_obj)).start()
            except Exception:
                print(traceback.format_exc())

    def add_update_callback(self, callback: CallbackWrapper):
        """
        添加对应tag的回调
        """
        with self.threading_lock:
            for tag in callback.tags:
                try:
                    self.callback[tag].add(callback)
                except KeyError:
                    self.callback[tag] = set()
                    self.callback[tag].add(callback)

    def get_detail(self, tags: Set[str]) -> Union[DataWrapper, None]:
        """
        依据tag精确查询，会返回数据的包装对象\n
        因此使用此方法可以获取到时间戳之类的额外数据\n
        """
        with self.threading_lock:
            data_set = self._select(tags)
            if len(data_set) == 0:
                return None
            elif len(data_set) == 1:
                return data_set.pop()

    def get(self, tags: Set[str]):
        """
        依据tag精确查询，会返回拆箱后的数据\n
        """
        res = self.get_detail(tags)
        if res is not None:
            return res.get()
        else:
            return None

    def get_dict_detail(self, tags: Set[str]) -> Dict[str, DataWrapper]:
        """
        依据tag模糊查询，会返回数据的包装对象\n
        因此使用此方法可以获取到时间戳之类的额外数据\n
        """
        with self.threading_lock:
            result = self._select(tags)
            res = {}
            for e in result:
                if len(tags) + 1 == len(e.get_tags()):
                    unique_tag_set = e.get_tags() - tags
                    # 此时unique_tag_set虽然是set，但是必然只有一个值
                    unique_tag = unique_tag_set.pop()
                    res[unique_tag] = e
            return res

    def get_dict(self, tags: Set[str]) -> Dict:
        """
        依据tag获取值，但是只会获取模糊查询的结果\n
        模糊值返回 {unique_tag: xxx, unique_tag2: xxx}\n
        """
        res = self.get_dict_detail(tags)
        for key in res.keys():
            res[key] = res[key].get()
        return res

    def get_all(self):
        """
        返回所有的数据\n
        格式为[{'tags': [], 'data': xxx}, ...]
        """
        with self.threading_lock:
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

    def subscribe_all(self, func: CallbackWrapper):
        """
        传入一个回调，并且会在所有数据更新的时候，都触发该回调
        """
        with self.threading_lock:
            self.subscribe.add(func)


class WebsocketServerAdapter(object):
    """
    数据中心的websocket接口服务端
    TODO: 现在是不加密的，加密后莫名其妙连不上
    """

    def __init__(self, data_center: Server):
        self.connect_identify = 0  # 用于给传入连接分配识别码的
        self.identify_lock = threading.Lock()  # 计算识别码的锁

        self.data_center = data_center

        # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # ssl_context.load_verify_locations(config['ssl_pem'])
        loop = asyncio.get_event_loop()
        server_ip = config['data_center']['server_ip']
        server_port = config['data_center']['server_port']
        loop.run_until_complete(
            websockets.serve(self.recv, server_ip, server_port))
        print('成功启动数据中心服务端websocket接口，运行在{}:{}'.format(server_ip, server_port))
        threading.Thread(target=lambda: loop.run_forever()).start()

    async def recv(self, ws: websockets.WebSocketServerProtocol, path):
        """
        用此函数处理websocket数据
        """
        # 给此链接分配识别码，识别码会循环使用
        with self.identify_lock:
            identify = self.connect_identify
            self.connect_identify += 1
            if self.connect_identify > 1000000:
                self.connect_identify = 0
        try:
            print('新传入websocket连接，分配识别码{}'.format(identify))

            # await ws.send('welcome')

            # 传入连接后首先发送的必是口令
            data = await ws.recv()
            if config['password'] != data:
                print('{}口令验证错误，接收到 {}'.format(identify, data))
                await ws.close(1000, 'password error')
                return
            print('{}口令验证成功'.format(identify))
            # 循环等待websocket发送消息
            while True:
                data = json.loads(await ws.recv())
                if data['mode'] == 'GET':
                    tags = set(data['tags'])
                    res = self.data_center.get(tags)
                    await ws.send(json.dumps({
                        'data': res
                    }))
                elif data['mode'] == 'SET':
                    tags = set(data['tags'])
                    value = data['value']
                    timestamp = data['timestamp']
                    self.data_center.update(tags, value, timestamp)
                elif data['mode'] == 'ALL':
                    res = self.data_center.get_all()
                    await ws.send(json.dumps({
                        'data': res
                    }))

        except websockets.exceptions.ConnectionClosedOK:
            print('{}连接正常关闭'.format(identify))
        except websockets.exceptions.ConnectionClosed:
            print('{}连接断开，且没有收到关闭代码'.format(identify))


class WebsocketClientAdapter(object):
    """
    数据中心的websocket接口客户端
    """

    def __init__(self):
        self.threading_lock = threading.Lock()
        with self.threading_lock:
            # 连接websocket
            self.loop = asyncio.get_event_loop()
            self.ws: websockets.WebSocketClientProtocol = \
                self.loop.run_until_complete(self.connect_server())

    @staticmethod
    async def connect_server():
        client_ip = config['data_center']['client_ip']
        client_port = config['data_center']['client_port']
        url = 'ws://{}:{}'.format(client_ip, client_port)
        print('即将连接' + url)
        ws = await websockets.connect(url)
        print('成功连接数据中心websocket')

        # greeting = await ws.recv()
        # print('收到问候语' + greeting)

        # 向数据中心发送口令验证身份
        await ws.send(config['password'])
        return ws

    def close(self):
        self.loop.run_until_complete(self.ws.close())

    def update(self, tags: Set[str], value, timestamp: int = None):
        with self.threading_lock:
            self.loop.run_until_complete(self.ws.send(json.dumps({
                'mode': 'SET',
                'tags': list(tags),
                'value': value,
                'timestamp': timestamp
            })))

    def get(self, tags: Set[str]):
        with self.threading_lock:
            self.loop.run_until_complete(self.ws.send(json.dumps({
                'mode': 'GET',
                'tags': list(tags)
            })))
            res = json.loads(self.loop.run_until_complete(self.ws.recv()))
            return res['data']

    def get_all(self):
        with self.threading_lock:
            self.loop.run_until_complete(self.ws.send(json.dumps({
                'mode': 'ALL'
            })))
            res = json.loads(self.loop.run_until_complete(self.ws.recv()))
            return res['data']
