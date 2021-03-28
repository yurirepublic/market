"""
此文件用于提供数据中心服务\n
说明，所有数据采用多key索引，称之为tag\n
更新数据时，会更新所有满足tag的值\n
获取数据时，也会获取满足所有tag的值\n
"""
import json
import traceback
from typing import Dict, List, Set, Union, Callable
import threading
import time
import queue

# 引入websocket相关
import websockets
import asyncio
import functools

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.loads(f.read())


def issubset(a: Set, b: Set):
    """
    判断a是否是b的子集
    """
    temp = a & b
    if temp == b:
        return True
    else:
        return False


def is_proper_subset(a: Set, b: Set):
    """
    判断a是否是b的真子集
    """
    temp = a & b
    if temp == b and a != b:
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

    def __init__(self, func: Callable[[DataWrapper], None], tags: Set):
        self.func = func
        self.tags = tags


class SubscriberWrapper(object):
    """
    订阅的包装器，只不过里面包装的不是回调函数，而是socket
    """

    def __init__(self, ws, tags: Set):
        self.ws = ws
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
            如果要订阅可选回调，直接用callback功能就好了
            """
            self.subscribe: Set[CallbackWrapper] = set()

    def _select(self, tags: Set[str]) -> Set[DataWrapper]:
        """
        根据对应标签，选择出满足的对象\n
        注！此操作极度消耗性能！尽可能用在模糊查询上，精确查询请使用cache！
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
        根据输入的tags，返回匹配到的CallbackWrapper\n
        需要回调包装器的标签是
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
        # 多线程触发更新回调
        callbacks = self._callback(tags)
        for e in callbacks:
            try:
                threading.Thread(target=lambda: e.func(data_obj)).start()
            except Exception:
                print(traceback.format_exc())

        # 多线程触发所有订阅的回调
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

    def get_fuzzy(self, tags: Set[str]) -> List[Dict]:
        """
        满足tag就返回，但是不会返回成字典形式\n
        返回形式为[{tags:[xxx, xxx], data:xxx}, ...]
        """
        with self.threading_lock:
            result = self._select(tags)
            res = []
            for e in result:
                res.append({
                    'tags': list(e.get_tags()),
                    'data': e.get()
                })
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
        self.data_center = data_center

        self.connect_identification = 0  # 用于给传入连接分配识别码的
        self.identify_lock = threading.Lock()  # 计算识别码的锁

        self.subscribe_queue: queue.Queue[DataWrapper] = queue.Queue()  # 等待配布的订阅数据，由数据中心通过回调发送

        self.subscribe_send_lock = threading.Lock()  # 发送订阅的锁
        self.subscribe_all_sockets: Set[websockets.WebSocketServerProtocol] = set()  # 用来存储订阅所有消息的列表
        self.subscribe_wrapper: Set[SubscriberWrapper] = set()  # 用来存储订阅可选消息的列表

        self.adapter = None
        self.subscribe_adapter = None

    async def init(self):
        # websocket接口部分
        server_ip = config['data_center']['server_ip']
        server_port = config['data_center']['server_port']

        self.adapter = await websockets.serve(self.recv, server_ip, server_port)
        print('成功启动数据中心服务端websocket接口，运行在{}:{}'.format(server_ip, server_port))

        # websocket订阅部分
        subscribe_ip = config['data_center']['subscribe_server_ip']
        subscribe_port = config['data_center']['subscribe_server_port']

        self.subscribe_adapter = await websockets.serve(self.subscribe_recv, subscribe_ip, subscribe_port)
        print('成功启动数据中心订阅接口，运行在{}:{}'.format(subscribe_ip, subscribe_port))

        # 向数据中心挂一个全局更新回调
        self.data_center.subscribe_all(CallbackWrapper(self.subscribe_callback, set()))

        # 启动配布协程
        asyncio.get_event_loop().create_task(self.subscribe_sender())

    def subscribe_callback(self, wrp: DataWrapper):
        """
        数据中心传达订阅的回调，收到数据就塞到queue等待配布
        """
        # 将原始的DataWrapper塞进去
        self.subscribe_queue.put(wrp)

    async def subscribe_sender(self):
        """
        专用于向订阅者进行配布的协程
        """
        loop = asyncio.get_running_loop()
        while True:
            data: DataWrapper = await loop.run_in_executor(None, functools.partial(self.subscribe_queue.get))

            # 转义出直接配布的json
            msg = json.dumps({
                'tags': list(data.get_tags()),
                'data': data.get()
            })

            # 先向订阅所有的进行配布
            for ws in self.subscribe_all_sockets:
                loop.create_task(self.subscribe_sender2(ws, msg))

            # 然后向可选订阅的进行配布
            for wrp in self.subscribe_wrapper:
                if issubset(wrp.tags, data.get_tags()):
                    loop.create_task(self.subscribe_sender3(wrp, msg))

    async def subscribe_sender2(self, ws, msg):
        """
        为了解决发送时的异常，需要在这里再开一个协程
        """
        try:
            await ws.send(msg)
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed):
            try:
                self.subscribe_all_sockets.remove(ws)
            except ValueError:
                # 对于重复删除直接无视。因为有可能被发现连接断开前，有多个协程开始拿着这个ws在运作
                pass

    async def subscribe_sender3(self, wrp: SubscriberWrapper, msg):
        """
        和上面那个sender2的功能一样，只不过这个用于负责可选订阅的配布
        """
        try:
            await wrp.ws.send(msg)
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed):
            try:
                self.subscribe_wrapper.remove(wrp)
            except ValueError:
                # 对于重复删除直接无视。因为有可能被发现连接断开前，有多个协程开始拿着这个ws在运作
                pass

    def assign_identification(self):
        """
        分配线程识别码
        """
        with self.identify_lock:
            identification = self.connect_identification
            self.connect_identification += 1
            if self.connect_identification > 1000000:
                self.connect_identification = 0
        return identification

    async def subscribe_recv(self, ws: websockets.WebSocketServerProtocol, path):
        """
        用来处理传入的订阅连接
        """
        # 直接将ws塞进去
        identification = self.assign_identification()
        print('新增一个数据中心订阅，分配识别码{}'.format(identification))
        try:
            # 检验连接的口令
            pwd = await ws.recv()
            if config['password'] != pwd:
                print('{}口令验证错误，接收到 {}'.format(identification, pwd))
                await ws.close(1000, 'password error')
                return
            while True:
                msg = json.loads(await ws.recv())
                print('数据中心订阅收到消息', msg)
                # 判断用户的指令
                if msg['mode'] == 'SUBSCRIBE':
                    tags = set(msg['tags'])
                    # 将socket封装好，添加到可选订阅的列表
                    wrapper = SubscriberWrapper(ws, tags)
                    self.subscribe_wrapper.add(wrapper)
                elif msg['mode'] == 'SUBSCRIBE_ALL':
                    # 将socket添加到所有订阅的列表
                    self.subscribe_all_sockets.add(ws)
                else:
                    print('订阅接口收到未知mode', msg['mode'])
        except websockets.exceptions.ConnectionClosedOK:
            print('{}连接正常关闭'.format(identification))
        except websockets.exceptions.ConnectionClosed:
            print('{}连接断开，且没有收到关闭代码'.format(identification))

    async def recv(self, ws: websockets.WebSocketServerProtocol, path):
        """
        用此函数处理websocket数据
        """
        # 给此链接分配识别码，识别码会循环使用
        identification = self.assign_identification()
        try:
            print('新传入websocket连接，分配识别码{}'.format(identification))
            # 传入连接后首先发送的必是口令
            msg = await ws.recv()
            if config['password'] != msg:
                print('{}口令验证错误，接收到 {}'.format(identification, msg))
                await ws.close(1000, 'password error')
                return
            print('{}口令验证成功'.format(identification))
            # 循环等待websocket发送消息
            while True:
                msg = json.loads(await ws.recv())
                if msg['mode'] == 'GET':
                    tags = set(msg['tags'])
                    res = self.data_center.get(tags)
                    await ws.send(json.dumps({
                        'data': res
                    }))
                elif msg['mode'] == 'GET_DICT':
                    tags = set(msg['tags'])
                    res = self.data_center.get_dict(tags)
                    await ws.send(json.dumps({
                        'data': res
                    }))
                elif msg['mode'] == 'GET_FUZZY':
                    tags = set(msg['tags'])
                    res = self.data_center.get_fuzzy(tags)
                    await ws.send(json.dumps({
                        'data': res
                    }))
                elif msg['mode'] == 'SET':
                    tags = set(msg['tags'])
                    value = msg['value']
                    timestamp = msg['timestamp']
                    self.data_center.update(tags, value, timestamp)
                elif msg['mode'] == 'GET_ALL':
                    res = self.data_center.get_all()
                    await ws.send(json.dumps({
                        'data': res
                    }))
                else:
                    print('数据接口收到未知mode', msg['mode'])

        except websockets.exceptions.ConnectionClosedOK:
            print('{}连接正常关闭'.format(identification))
        except websockets.exceptions.ConnectionClosed:
            print('{}连接断开，且没有收到关闭代码'.format(identification))


class WebsocketClientAdapter(object):
    """
    数据中心的websocket接口客户端
    """

    def __init__(self):
        self.threading_lock = threading.Lock()

        self.ws = None

    async def init(self):
        # 连接websocket
        client_ip = config['data_center']['client_ip']
        client_port = config['data_center']['client_port']
        url = 'ws://{}:{}'.format(client_ip, client_port)
        print('即将连接数据中心接口' + url)
        self.ws = await websockets.connect(url)
        await self.ws.send(config['password'])
        print('成功连接数据中心接口')

    async def close(self):
        await self.ws.close()

    async def update(self, tags: Set[str], value, timestamp: int = None):
        with self.threading_lock:
            await self.ws.send(json.dumps({
                'mode': 'SET',
                'tags': list(tags),
                'value': value,
                'timestamp': timestamp
            }))

    async def get(self, tags: Set[str]):
        with self.threading_lock:
            await self.ws.send(json.dumps({
                'mode': 'GET',
                'tags': list(tags)
            }))
            res = json.loads(await self.ws.recv())
            return res['data']

    async def get_dict(self, tags: Set[str]):
        with self.threading_lock:
            await self.ws.send(json.dumps({
                'mode': 'GET_DICT',
                'tags': list(tags)
            }))
            res = json.loads(await self.ws.recv())
            return res['data']

    async def get_all(self):
        with self.threading_lock:
            await self.ws.send(json.dumps({
                'mode': 'ALL'
            }))
            res = json.loads(await self.ws.recv())
            return res['data']


async def create_server():
    return Server()


async def create_server_adapter(server):
    adapter = WebsocketServerAdapter(server)
    await adapter.init()
    return adapter


async def create_client_adapter():
    adapter = WebsocketClientAdapter()
    await adapter.init()
    return adapter
