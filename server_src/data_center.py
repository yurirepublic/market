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

# 引入websocket相关
import websockets
import asyncio
import ssl

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.loads(f.read())


def issubset(a: Set, b: Set):
    """
    判断a是否是b的子集
    """
    temp = a | b
    if temp == b:
        return True
    else:
        return False


def is_proper_subset(a: Set, b: Set):
    """
    判断a是否是b的真子集
    """
    temp = a | b
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
    会使用asyncio.create_task来运行它
    """

    def __init__(self, func, tags: Set):
        self.func = func
        self.tags = tags


class SubscriberWrapper(object):
    """
    订阅的包装器，只不过里面包装的不是回调函数，而是socket
    """

    def __init__(self, ws, tags: Set[str], comment: str):
        self.ws: websockets.WebSocketClientProtocol = ws
        self.tags = tags
        self.comment = comment  # 用户对于该订阅的备注，传输订阅时会一起发送，用于连接复用时区分消息


class Server(object):
    """
    数据中心的服务端，纯Python对象，需要使用接口来远程使用
    """

    def __init__(self):
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

    def update(self, tags: Set[str], value, timestamp=None):
        """
        依据tag更新值
        """
        # 根据tag筛选数据集合
        data_obj = None
        try:
            data_obj = self.cache[self.tag2key(tags)]
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
                print('警告，这里的代码不应该被运行')
                threading.Thread(target=lambda: e.func(data_obj)).start()
            except Exception:
                print(traceback.format_exc())

        # 多线程触发所有订阅的回调
        for e in self.subscribe:
            asyncio.create_task(e.func(data_obj))

    def add_update_callback(self, callback: CallbackWrapper):
        """
        添加对应tag的回调
        """
        for tag in callback.tags:
            try:
                self.callback[tag].add(callback)
            except KeyError:
                self.callback[tag] = set()
                self.callback[tag].add(callback)

    def _get_detail(self, tags: Set[str]) -> Union[DataWrapper, None]:
        """
        依据tag精确查询，会返回数据的包装对象\n
        因此使用此方法可以获取到时间戳之类的额外数据\n
        """
        data_set = self._select(tags)
        if len(data_set) == 0:
            return None
        elif len(data_set) == 1:
            return list(data_set)[0]

    def get(self, tags: Set[str]):
        """
        依据tag精确查询，会返回拆箱后的数据\n
        """
        res = self._get_detail(tags)
        if res is not None:
            return res.get()
        else:
            return None

    def _get_dict_detail(self, tags: Set[str]) -> Dict[str, DataWrapper]:
        """
        依据tag模糊查询，会返回数据的包装对象\n
        因此使用此方法可以获取到时间戳之类的额外数据\n
        """
        result = self._select(tags)
        res = {}
        for e in result:
            if len(tags) + 1 == len(e.get_tags()):
                unique_tag_set = e.get_tags() - tags
                # 此时unique_tag_set虽然是set，但是必然只有一个值
                unique_tag = list(unique_tag_set)[0]
                res[unique_tag] = e
        return res

    def get_dict(self, tags: Set[str]) -> Dict:
        """
        依据tag获取值，但是只会获取模糊查询的结果\n
        模糊值返回 {unique_tag: xxx, unique_tag2: xxx}\n
        """
        res = self._get_dict_detail(tags)
        for key in res.keys():
            res[key] = res[key].get()
        return res

    def get_fuzzy(self, tags: Set[str]) -> List[Dict]:
        """
        满足tag就返回，但是不会返回成字典形式\n
        返回形式为[{tags:[xxx, xxx], data:xxx}, ...]
        """
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
        self.subscribe.add(func)


class WebsocketServerAdapter(object):
    """
    数据中心的websocket接口服务端
    """

    def __init__(self, data_center: Server):
        self.data_center = data_center

        self.connect_identification = 0  # 用于给传入连接分配识别码的
        self.identify_lock = asyncio.Lock()  # 计算识别码的锁

        self.subscribe_queue: asyncio.Queue[DataWrapper] = asyncio.Queue()  # 等待配布的订阅数据，由数据中心通过回调发送

        self.subscribe_precise: Set[SubscriberWrapper] = set()  # 精确订阅列表
        self.subscribe_dict: Set[SubscriberWrapper] = set()  # 字典订阅列表
        self.subscribe_fuzzy: Set[SubscriberWrapper] = set()  # 模糊订阅列表
        self.subscribe_all: Set[SubscriberWrapper] = set()  # 所有订阅列表

        self.adapter = None
        self.subscribe_adapter = None

        self.loop = asyncio.get_event_loop()

    async def init(self):
        # 生成tls上下文
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(config['api']['ssl_pem'], config['api']['ssl_key'])

        # websocket接口部分
        server_ip = config['data_center']['server_ip']
        server_port = config['data_center']['server_port']

        self.adapter = await websockets.serve(self.recv, server_ip, server_port, ssl=ssl_context)
        print('成功启动数据中心服务端websocket接口，运行在{}:{}'.format(server_ip, server_port))

        # websocket订阅部分
        subscribe_ip = config['data_center']['subscribe_server_ip']
        subscribe_port = config['data_center']['subscribe_server_port']

        self.subscribe_adapter = await websockets.serve(self.subscribe_recv, subscribe_ip, subscribe_port,
                                                        ssl=ssl_context)
        print('成功启动数据中心订阅接口，运行在{}:{}'.format(subscribe_ip, subscribe_port))

        # 向数据中心挂一个全局更新回调
        self.data_center.subscribe_all(CallbackWrapper(self.subscribe_callback, set()))

        # 启动配布协程
        self.loop.create_task(self.subscribe_sender())

    async def subscribe_callback(self, wrp: DataWrapper):
        """
        数据中心传达订阅的回调，收到数据就塞到queue等待配布
        """
        # 将原始的DataWrapper塞进去
        await self.subscribe_queue.put(wrp)

    async def subscribe_sender(self):
        """
        专用于向订阅者进行配布的协程
        """
        while True:
            data: DataWrapper = await self.subscribe_queue.get()

            # 转义出直接配布的json
            tags = data.get_tags()
            list_tags = list(tags)  # 写个缓存优化

            # 向订阅进行配布
            msg = {
                'tags': list_tags,
                'data': data.get()
            }
            for wrp in self.subscribe_all:
                msg['comment'] = wrp.comment
                self.loop.create_task(self.subscribe_sender_all(wrp, json.dumps(msg)))

            for wrp in self.subscribe_precise:
                if wrp.tags == tags:
                    msg['comment'] = wrp.comment
                    self.loop.create_task(self.subscribe_sender_precise(wrp, json.dumps(msg)))

            for wrp in self.subscribe_fuzzy:
                if issubset(wrp.tags, tags):
                    msg['comment'] = wrp.comment
                    self.loop.create_task(self.subscribe_sender_fuzzy(wrp, json.dumps(msg)))

            for wrp in self.subscribe_dict:
                if issubset(wrp.tags, tags) and len(wrp.tags) + 1 == len(tags):
                    # 筛选出特殊的tag
                    special = tags - wrp.tags
                    special = list(special)[0]
                    msg['comment'] = wrp.comment
                    msg['special'] = special
                    self.loop.create_task(self.subscribe_sender_dict(wrp, json.dumps(msg)))

    async def subscribe_sender_all(self, wrp: SubscriberWrapper, msg):
        """
        为了解决发送时的异常，需要在这里再开一个协程
        """
        try:
            await wrp.ws.send(msg)
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed):
            try:
                self.subscribe_all.remove(wrp)
            except KeyError:
                # 对于重复删除直接无视。因为有可能被发现连接断开前，有多个协程开始拿着这个ws在运作
                pass

    async def subscribe_sender_precise(self, wrp: SubscriberWrapper, msg):
        """
        和上面那个功能一样，只不过这个用于负责精确订阅的配布
        """
        try:
            await wrp.ws.send(msg)
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed):
            try:
                self.subscribe_precise.remove(wrp)
            except KeyError:
                # 对于重复删除直接无视。因为有可能被发现连接断开前，有多个协程开始拿着这个ws在运作
                pass

    async def subscribe_sender_dict(self, wrp: SubscriberWrapper, msg):
        """
        和上面那个功能一样，只不过这个用于字典订阅的配布
        """
        try:
            await wrp.ws.send(msg)
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed):
            try:
                self.subscribe_dict.remove(wrp)
            except KeyError:
                # 对于重复删除直接无视。因为有可能被发现连接断开前，有多个协程开始拿着这个ws在运作
                pass

    async def subscribe_sender_fuzzy(self, wrp: SubscriberWrapper, msg):
        """
        和上面那个功能一样，只不过这个用于模糊订阅的配布
        """
        try:
            await wrp.ws.send(msg)
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed):
            try:
                self.subscribe_fuzzy.remove(wrp)
            except KeyError:
                # 对于重复删除直接无视。因为有可能被发现连接断开前，有多个协程开始拿着这个ws在运作
                pass

    async def assign_identification(self):
        """
        分配线程识别码
        """
        async with self.identify_lock:
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
        identification = await self.assign_identification()
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
                # 获取用户备注
                try:
                    comment = msg['comment']
                except KeyError:
                    comment = ''
                # 判断用户的指令
                if msg['mode'] == 'SUBSCRIBE_PRECISE':
                    tags = set(msg['tags'])
                    # 将socket封装好，添加到可选订阅的列表
                    wrapper = SubscriberWrapper(ws, tags, comment)
                    self.subscribe_precise.add(wrapper)
                elif msg['mode'] == 'SUBSCRIBE_DICT':
                    tags = set(msg['tags'])
                    wrapper = SubscriberWrapper(ws, tags, comment)
                    self.subscribe_dict.add(wrapper)
                elif msg['mode'] == 'SUBSCRIBE_FUZZY':
                    tags = set(msg['tags'])
                    wrapper = SubscriberWrapper(ws, tags, comment)
                    self.subscribe_fuzzy.add(wrapper)
                elif msg['mode'] == 'SUBSCRIBE_ALL':
                    # 将socket添加到所有订阅的列表
                    wrapper = SubscriberWrapper(ws, set(), comment)
                    self.subscribe_all.add(wrapper)
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
        identification = await self.assign_identification()
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
                try:
                    comment = msg['comment']
                except KeyError:
                    comment = ''
                if msg['mode'] == 'GET':
                    tags = set(msg['tags'])
                    res = self.data_center.get(tags)
                    await ws.send(json.dumps({
                        'data': res,
                        'comment': comment
                    }))
                elif msg['mode'] == 'GET_DICT':
                    tags = set(msg['tags'])
                    res = self.data_center.get_dict(tags)
                    await ws.send(json.dumps({
                        'data': res,
                        'comment': comment
                    }))
                elif msg['mode'] == 'GET_FUZZY':
                    tags = set(msg['tags'])
                    res = self.data_center.get_fuzzy(tags)
                    await ws.send(json.dumps({
                        'data': res,
                        'comment': comment
                    }))
                elif msg['mode'] == 'SET':
                    tags = set(msg['tags'])
                    value = msg['value']
                    timestamp = msg['timestamp']
                    self.data_center.update(tags, value, timestamp)
                elif msg['mode'] == 'GET_ALL':
                    res = self.data_center.get_all()
                    await ws.send(json.dumps({
                        'data': res,
                        'comment': comment
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
        self.ws: websockets.WebSocketClientProtocol = None

        self.async_lock = asyncio.Lock()

        self.buf = {}

    async def init(self):
        # 连接websocket
        client_ip = config['data_center']['client_ip']
        client_port = config['data_center']['client_port']
        url = 'wss://{}:{}'.format(client_ip, client_port)
        print('即将连接数据中心接口' + url)
        self.ws = await websockets.connect(url)
        await self.ws.send(config['password'])
        print('成功连接数据中心接口')

    async def close(self):
        await self.ws.close()

    async def update(self, tags: Set[str], value, timestamp: int = None):
        await self.ws.send(json.dumps({
            'mode': 'SET',
            'tags': list(tags),
            'value': value,
            'timestamp': timestamp
        }))

    async def get(self, tags: Set[str], comment=''):
        async with self.async_lock:
            await self.ws.send(json.dumps({
                'mode': 'GET',
                'tags': list(tags),
                'comment': comment
            }))
            res = json.loads(await self.ws.recv())
            return res['data']

    async def get_dict(self, tags: Set[str], comment=''):
        async with self.async_lock:
            await self.ws.send(json.dumps({
                'mode': 'GET_DICT',
                'tags': list(tags),
                'comment': comment
            }))
            res = json.loads(await self.ws.recv())
            return res['data']

    async def get_fuzzy(self, tags: Set[str], comment=''):
        async with self.async_lock:
            await self.ws.send(json.dumps({
                'mode': 'GET_FUZZY',
                'tags': list(tags),
                'comment': comment
            }))
            res = json.loads(await self.ws.recv())
            return res['data']

    async def get_all(self, comment=''):
        async with self.async_lock:
            await self.ws.send(json.dumps({
                'mode': 'GET_ALL',
                'comment': comment
            }))
            res = json.loads(await self.ws.recv())
            return res['data']


class WebsocketSubscribe(object):
    """
    数据中心的websocket接口客户端
    """

    def __init__(self):
        self.ws: websockets.WebSocketClientProtocol = None

        self.buf = {}
        self.order = 0
        self.order_lock = asyncio.Lock()

    async def init(self):
        # 连接subscribe
        ip = config['data_center']['subscribe_client_ip']
        port = config['data_center']['subscribe_client_port']
        url = 'wss://{}:{}'.format(ip, port)
        print('即将连接订阅接口' + url)
        self.ws = await websockets.connect(url)
        await self.ws.send(config['password'])
        print('成功连接订阅接口')
        # 启动消息接收
        asyncio.create_task(self._on_message())

    async def close(self):
        await self.ws.close()

    async def _on_message(self):
        """
        分流订阅消息
        """
        while True:
            try:
                msg = await self.ws.recv()
                msg = json.loads(msg)
                asyncio.create_task(self.buf[msg['comment']](msg))
            except websockets.exceptions.ConnectionClosedOK:
                print('客户端订阅连接正常关闭')
                break
            except websockets.exceptions.ConnectionClosed:
                print('客户端订阅连接断开，且没有收到关闭代码')
                break

    async def _get_order(self):
        async with self.order_lock:
            self.order += 1
            if self.order > 1000000:
                self.order = 0
            return self.order

    async def subscribe_dict(self, tags: Set[str], callback):
        order = await self._get_order()
        self.buf[order] = callback
        await self.ws.send(json.dumps({
            'mode': 'SUBSCRIBE_DICT',
            'tags': list(tags),
            'comment': order
        }))

    async def subscribe_fuzzy(self, tags: Set[str], callback):
        order = await self._get_order()
        self.buf[order] = callback
        await self.ws.send(json.dumps({
            'mode': 'SUBSCRIBE_FUZZY',
            'tags': list(tags),
            'comment': order
        }))


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


async def create_subscribe():
    obj = WebsocketSubscribe()
    await obj.init()
    return obj


async def _main():
    # 用于直接使用该脚本启动数据中心的情况
    server = await create_server()
    await create_server_adapter(server)


def memory_summary():
    # Only import Pympler when we need it. We don't want it to
    # affect our process if we never call memory_summary.
    while True:
        from pympler import summary, muppy
        mem_summary = summary.summarize(muppy.get_objects())
        rows = summary.format_(mem_summary)
        print('\n'.join(rows))
        time.sleep(300)


if __name__ == '__main__':
    # # 运行内存泄露检测
    # threading.Thread(target=memory_summary).start()

    asyncio.get_event_loop().run_until_complete(_main())
    asyncio.get_event_loop().run_forever()
