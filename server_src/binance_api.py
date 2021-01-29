import json
import hmac
import time
import requests
import _thread
import websocket
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
    # 获取币安常用的毫秒级timestamp
    return str(round(time.time() * 1000))


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
            self.price = {}  # 当前已订阅交易对的最新价格

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
        if method == 'GET':
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


# 通用的操作者，会自动创建期货和现货的操作者，可用于对冲下单等操作
class NormalOperator():
    def __init__(self) -> None:
        super().__init__()
        self.operator = Operator()
        self.operator_future = Operatorfuture()

    def multi_trade():
        pass
