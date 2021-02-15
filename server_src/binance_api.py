import json
import hmac
import time
from typing import Union
import requests
import _thread
import websocket
import math
import threading
from hashlib import sha256

"""
随着脚本的增多，需要抽取一些常用的币安api，以及常用如对冲操作在此文件
备注：尽量不要给两边单独写API，维护两套API很烦，最好只写最常用的例如trade
    其他API尽量使用request自行访问
    可以写高层的API，跨期货现货的，例如对冲下单这种
"""

base_url = 'binance.com'  # 基本网址，用于快速切换国内地址和国地址，国际地址是binance.com，国内地址是binancezh.pro
request_trace = True  # 是否追踪请求，开启会打印出每次请求的url、状态码、返回的文本


def get_timestamp():
    """
    获取币安常用的毫秒级timestamp
    """
    return str(round(time.time() * 1000))


def float_to_str_floor(amount: float, precision: int = 8) -> str:
    """
    将float转为指定精度的str格式，一般用于对高精度计算结果下单，会向下取整避免多下
    如不指定精度，则默认为币安最大精度8
    """
    return str(math.floor(amount * (10 ** precision)) / (10 ** precision))


def float_to_str_ceil(amount: float, precision: int = 8) -> str:
    """
    将float转为指定精度的str格式，一般用于对高精度计算结果下单，会向上取整避免少下
    如不指定精度，则默认币安最大精度8
    """
    return str(math.ceil(amount * (10 ** precision)) / (10 ** precision))


def float_to_str_round(amount: float, precision: int = 8) -> str:
    """
    将float转为指定精度的str格式，一般用于消除0.000000000001和0.9999999999
    会对指定精度四舍五入，如不指定精度，则默认币安最大精度8
    """
    return str(round(amount * (10 ** precision)) / (10 ** precision))


def make_query_string(**kwargs):
    """
    这个函数会接收任意个参数，并返回对应的GET STRING
    返回格式为aaa=xxx&bbb=xxx&ccc=xxx
    """
    res = ''
    if len(kwargs.keys()) != 0:
        pass
    else:
        return ''
    for key in kwargs.keys():
        res += key + '=' + kwargs[key] + '&'
    res = res[:len(res) - 1]  # 删掉最后多余的&
    return res


class BaseOperator(object):
    """
    基本操作
    """

    def __init__(self):
        # 读取配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            jsons = json.loads(f.read())

            self.public_key = jsons['binance_public_key']
            self.private_key = jsons['binance_private_key']

            self.subscribe_id = 1  # 订阅时要发送的id，每次+1（似乎每次发一样的也行）
            self.subscribe_id_lock = threading.Lock()       # 订阅id线程锁

            self.price = {}  # 当前已订阅交易对的最新价格

    def get_subscribe_id(self) -> int:
        """
        返回订阅时要发送的id
        该函数是线程安全的
        """
        self.subscribe_id_lock.acquire()
        res = self.subscribe_id
        self.subscribe_id += 1
        self.subscribe_id_lock.release()
        return res

    def request(self, area_url: str, path_url, method: str, data: dict, test=False, send_signature=True):
        """
        用于发出请求的内部API
        :param test: 是否添加/test路径，用于测试下单，默认False
        :param area_url: 头部的地址，例如api、fapi、dapi
        :param path_url: 路径地址，例如/fapi/v2/account
        :param method: 请求方法，仅限POST和GET
        :param data: 发送的数据
        :return:
        """
        if method.upper() != 'POST' and method.upper() != 'GET':
            raise Exception('请求方法必须为POST或者GET，大小写不限')
        headers = {
            'X-MBX-APIKEY': self.public_key
        }
        if test:
            test_path = '/test'
        else:
            test_path = ''
        data = make_query_string(**data)
        signature = hmac.new(self.private_key.encode('ascii'),
                             data.encode('ascii'), digestmod=sha256).hexdigest()
        if send_signature:
            url = 'https://{}.{}{}{}?{}&signature={}'.format(
                area_url, base_url, path_url, test_path, data, signature)
        else:
            url = 'https://{}.{}{}{}?{}'.format(
                area_url, base_url, path_url, test_path, data)
        if method.upper() == 'GET':
            r = requests.get(url, headers=headers)
        else:
            r = requests.post(url, headers=headers)
        if request_trace:
            print(url)
            print(r.status_code)
            print(r.text)
        return r.text

    def subscribe_price(self, name: str):
        # 订阅最新交易价格
        data = {
            'method': 'SUBSCRIBE',
            'params': [
                name.lower() + "@aggTrade",
            ],
            'id': self.subscribe_id
        }
        self.ws.send(json.dumps(data))
        self.subscribe_id += 1


class Operator(BaseOperator):
    """
    现货API操作
    """

    def __init__(self):
        super(Operator, self).__init__()
        self.ws = None

    def connect_websocket(self):
        """
        调用此函数连接到websocket，以启用websocket相关api
        """
        self.ws = websocket.WebSocketApp(
            'wss://stream.' + base_url + ':9443/ws')
        self.ws.connect_completed = False  # 自己加的一个成员，用来外部等待连接成功再放行

        def on_open(ws):
            print('成功建立现货websocket连接')
            ws.connect_completed = True

        def on_message(ws, data):
            # 收到websocket时使用的处理函数
            data = json.loads(data)
            if 'e' in data.keys() and data['e'] == 'aggTrade':
                self.price[data['s']] = float(data['p'])
            else:
                print(data)

        self.ws.on_message = on_message
        self.ws.on_open = on_open
        # 额外开一个线程用来运行此websocket
        self.ws_handle = _thread.start_new_thread(
            lambda: self.ws.run_forever(ping_interval=300), ())

        # 等待直到websocket连接成功
        while not self.ws.connect_completed:
            time.sleep(0.1)

    def trade(self, symbol: str, quantity, side, test=False):
        """
        在现货下单
        """
        if test:
            test_trade = '/test'
        else:
            test_trade = ''
        headers = {
            'X-MBX-APIKEY': self.public_key
        }
        data = make_query_string(
            symbol=symbol.upper(),
            side=side,
            type='MARKET',
            quantity=quantity,
            timestamp=str(round(time.time() * 1000))
        )
        signature = hmac.new(self.private_key.encode('ascii'),
                             data.encode('ascii'), digestmod=sha256).hexdigest()
        url = 'https://api.' + base_url + '/api/v3/order' + \
            test_trade + '?' + data + '&signature=' + signature
        print(url)
        r = requests.post(url, headers=headers)
        print(r.status_code)
        print(r.text)


class Operatorfuture(BaseOperator):
    """
    期货API操作
    """

    def __init__(self):
        super(Operatorfuture, self).__init__()
        self.ws = None

    def connect_websocket(self):
        self.ws = websocket.WebSocketApp('wss://fstream.' + base_url + '/ws')
        self.ws.connect_completed = False  # 自己加的一个成员，用来外部等待连接成功再放行

        def on_open(ws):
            print('成功建立USDT期货websocket连接')
            ws.connect_completed = True

        def on_message(ws, data):
            # 收到websocket时使用的处理函数
            data = json.loads(data)
            if 'e' in data.keys() and data['e'] == 'aggTrade':
                self.price[data['s']] = float(data['p'])
            else:
                print(data)

        self.ws.on_message = on_message
        self.ws.on_open = on_open
        # 额外开一个线程用来运行此websocket
        self.ws_handle = _thread.start_new_thread(
            lambda: self.ws.run_forever(ping_interval=300), ())

        while not self.ws.connect_completed:
            time.sleep(0.1)

    def trade(self, symbol: str, quantity, side, test=True):
        headers = {
            'X-MBX-APIKEY': self.public_key
        }
        data = make_query_string(
            symbol=symbol.upper(),
            side=side,
            type='MARKET',
            quantity=quantity,
            timestamp=str(round(time.time() * 1000))
        )
        if test:
            test_trade = '/test'
        else:
            test_trade = ''
        signature = hmac.new(self.private_key.encode('ascii'),
                             data.encode('ascii'), digestmod=sha256).hexdigest()
        url = 'https://fapi.' + base_url + '/fapi/v1/order' + \
            test_trade + '?' + data + '&signature=' + signature
        print(url)
        r = requests.post(url, headers=headers)
        print(r.status_code)
        print(r.text)

    def close_out(self, symbol: str):
        """
        将某个货币对平仓
        """
        # 先获取货币对的持仓和方向
        headers = {
            'X-MBX-APIKEY': self.public_key
        }
        data = make_query_string(
            timestamp=str(round(time.time() * 1000))
        )
        signature = hmac.new(self.private_key.encode('ascii'),
                             data.encode('ascii'), digestmod=sha256).hexdigest()
        url = 'https://fapi.' + base_url + '/fapi/v2/account' + \
            '?' + data + '&signature=' + signature
        print(url)
        r = requests.get(url, headers=headers)
        print(r.status_code)
        print(r.text)
        if r.status_code != 200:
            raise Exception('获取持仓数量错误')
        # 遍历找到需要的货币对
        for x in json.loads(r.text)['positions']:
            if x['symbol'] == symbol.upper():
                position_amt = x['positionAmt']
                break
        else:
            raise Exception('未在返回的数据中找到持仓')
        # 下市价单平仓
        if float(position_amt) > 0:
            self.trade(symbol, position_amt, 'SELL')
        else:
            # 这里不转为float，怕有精度问题留个0.0000001没平仓，直接使用原始的字符串
            self.trade(symbol, position_amt.replace('-', ''), 'BUY')


class SmartOperator():
    """
    智能操作者，不仅整合了期货、现货、杠杆等等所有的操作
    还增加了很多自动化的选项，例如下单前自动获取货币精度并向下取整
    相当于高度封装版本
    缺点在于需要获取额外信息，速度、灵活性不如传统api
    """

    def __init__(self) -> None:
        super().__init__()

        # 实例化一个基本操作者，用来发出request
        self.operator = BaseOperator()

        """
        注，暂不支持websocket，反正用不上
        """
    #     # 实例化期货和现货的api，注意这里并不会连接websocket
    #     self.operator = Operator()
    #     self.operator_future = Operatorfuture()

    # def connect_websocket_both(self):
    #     """
    #     连接期货和现货的websocket
    #     已经连接的话，会覆盖掉以前的连接
    #     """
    #     self.operator.connect_websocket()
    #     self.operator_future.connect_websocket()

    # def connect_websocket_base(self):
    #     """
    #     连接现货的websocket
    #     已经连接的话，会覆盖掉以前的连接
    #     """
    #     self.operator.connect_websocket()

    # def connect_websocket_future(self):
    #     """
    #     连接期货的websocket
    #     已经连接的话，会覆盖掉以前的连接
    #     """
    #     self.operator_future.connect_websocket()

    def get_symbol_precision(self, symbol: str, asset: str, mode: str) -> int:
        """
        获取交易对的报价精度，用于按照数量下单时，得知最大货币下单精度
        :param symbol: 要查询的交易对名字
        :param mode: 要查询的模式，仅可查询MAIN，FUTURE。代表现货和期货
        :return: 查询的小数位数量
        """
        # 转换符号到大写
        symbol = symbol.upper()
        mode = mode.upper()

        # 判断mode有没有输入正确
        if mode != 'MAIN' and mode != 'FUTURE':
            raise Exception('mode输入错误，仅可输入MAIN或者FUTURE')

        # 根据mode获取对应的交易对精度
        if mode == 'MAIN':
            # 获取每个 现货 交易对的规则（下单精度）
            info = json.loads(self.operator.request(
                'api', '/api/v3/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
            # 在获取的结果里面找到需要的精度信息
            for e in info:
                # 找到对应交易对
                if e['symbol'] == symbol:
                    # 根据asset返回对应的精度
                    return int(e['baseAssetPrecision'])
            else:
                raise Exception('没有找到欲查询的精度信息')
        if mode == 'FUTURE':
            info = json.loads(self.operator.request(
                'fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
            for e in info:
                if e['symbol'] == symbol:
                    return int(e['quantityPrecision'])
            else:
                raise Exception('没有找到欲查询的精度信息')

    def trade_main_market(self, symbol: str, amount: Union[str, float], side: str, test=False, volume_mode=False):
        """
        在现货下市价单
        需要注意的是，amount可以传入float和str
        传入str会直接使用此str的数字进行下单
        传入float会自动获取要下单货币对的精度，并向下取整转为str再下单
        :param symbol: 要下单的交易对符号，会自动转大写
        :param amount: 要下单的货币数量，默认是货币数量，如果开启成交额模式，则为成交额
        :param side: 下单方向，字符串格式，只能为SELL或者BUY
        :param test: 是否为测试下单，默认False。测试下单不会提交到撮合引擎，用于测试
        :volume_mode: 是否用成交额模式下单，默认False，开启后amount代表成交额而不是货币数量
        :return: 下单请求提交后，币安返回的结果
        """
        # 转化字符串
        symbol = symbol.upper()
        side = side.upper()

        # 判断是否加入test链接
        if test:
            test_trade = '/test'
        else:
            test_trade = ''

        # 判断side是否填写正确
        side = side.upper()
        if side != 'BUY' and side != 'SELL':
            raise Exception('交易side填写错误，只能为SELL或者BUY')

        # 如果amount是float格式则根据精度转换一下
        if isinstance(amount, float):
            pass

        # 判断是否成交额模式填写不同的参数
        data = make_query_string(
            symbol=symbol.upper(),
            side=side,
            type='MARKET',
            quantity=amount,
            timestamp=str(round(time.time() * 1000))
        )
        headers = {
            'X-MBX-APIKEY': self.public_key
        }
        signature = hmac.new(self.private_key.encode('ascii'),
                             data.encode('ascii'), digestmod=sha256).hexdigest()
        url = 'https://api.' + base_url + '/api/v3/order' + \
            test_trade + '?' + data + '&signature=' + signature
        print(url)
        r = requests.post(url, headers=headers)
        print(r.status_code)
        print(r.text)
