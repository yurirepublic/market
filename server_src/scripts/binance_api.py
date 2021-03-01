import json
import hmac
import time
from typing import Union
import requests
import math
import threading
from hashlib import sha256

"""
此脚本用于放置对币安API的封装
"""

base_url = 'binance.com'  # 基本网址，用于快速切换国内地址和国际地址，国际地址是binance.com，国内地址是binancezh.pro
request_trace = True  # 是否追踪请求，开启会打印出每次请求的url、状态码、返回的文本


class BinanceException(Exception):

    def __init__(self, status_code, response):
        """
        币安的请求没有返回200就抛出此异常
        """
        self.status_code = status_code
        self.response = response


class CantRetryException(Exception):
    def __init__(self, status_code, response):
        """
        经过一定程度的判断，无法简单retry解决就返回此异常
        """
        self.status_code = status_code
        self.response = response


def get_timestamp():
    """
    获取币安常用的毫秒级timestamp
    """
    return str(round(time.time() * 1000))


def float_to_str_floor(amount: float, precision: int = 8) -> str:
    """
    将float转为指定精度的str格式，一般用于对高精度计算结果下单，会向下取整避免多下\n
    如不指定精度，则默认为币安最大精度8
    """
    return str(math.floor(amount * (10 ** precision)) / (10 ** precision))


def float_to_str_ceil(amount: float, precision: int = 8) -> str:
    """
    将float转为指定精度的str格式，一般用于对高精度计算结果下单，会向上取整避免少下\n
    如不指定精度，则默认币安最大精度8
    """
    return str(math.ceil(amount * (10 ** precision)) / (10 ** precision))


def float_to_str_round(amount: float, precision: int = 8) -> str:
    """
    将float转为指定精度的str格式，一般用于消除0.000000000001和0.9999999999\n
    会对指定精度四舍五入，如不指定精度，则默认币安最大精度8
    """
    return str(round(amount * (10 ** precision)) / (10 ** precision))


def make_query_string(**kwargs) -> str:
    """
    这个函数会接收任意个参数，并返回对应的GET STRING
    :return: 返回格式为aaa=xxx&bbb=xxx&ccc=xxx

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
            self.subscribe_id_lock = threading.Lock()  # 订阅id线程锁

            # self.price = {}  # 当前已订阅交易对的最新价格

    def get_subscribe_id(self) -> int:
        """
        返回订阅时要发送的id\n
        该函数是线程安全的
        """
        self.subscribe_id_lock.acquire()
        res = self.subscribe_id
        self.subscribe_id += 1
        self.subscribe_id_lock.release()
        return res

    def request(self, area_url: str, path_url, method: str, data: dict, test=False, send_signature=True,
                retry_count: int = 3, retry_interval: int = 0) -> str:
        """
        用于向币安发送请求的内部API\n
        如果请求状态码不是200，会引发BinanceException\n
        :param area_url: 头部的地址，例如api、fapi、dapi
        :param path_url: 路径地址，例如/fapi/v2/account
        :param method: 请求方法，仅限POST和GET
        :param data: 发送的数据，dict会自动转换成http参数，str则不转换
        :param test: 是否添加/test路径，用于测试下单，默认False
        :param send_signature: 是否发送签名，有的api不接受多余的参数，就不能默认发送签名
        :param retry_count: 返回状态码不为200时，自动重试的次数
        :param retry_interval: 自动尝试的间隔(秒)
        :return: 返回的数据文本格式
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
        if isinstance(data, dict):
            data = make_query_string(**data)
        elif isinstance(data, str):
            pass
        else:
            raise Exception('data格式错误，必须为dict，或者使用make_query_string转换后的str')
        signature = hmac.new(self.private_key.encode('ascii'),
                             data.encode('ascii'), digestmod=sha256).hexdigest()
        if send_signature:
            url = 'https://{}.{}{}{}?{}&signature={}'.format(
                area_url, base_url, path_url, test_path, data, signature)
        else:
            url = 'https://{}.{}{}{}?{}'.format(
                area_url, base_url, path_url, test_path, data)

        while retry_count > 0:
            if method.upper() == 'GET':
                r = requests.get(url, headers=headers)
            else:
                r = requests.post(url, headers=headers)

            if request_trace:
                print('-----start-----')
                print(url)
                print(r.status_code)
                print(r.text)
                print('-----ended-----')

            if r.status_code != 200:
                if retry_count > 0:
                    retry_count -= 1
                else:
                    raise BinanceException(r.status_code, r.text)
            else:
                return r.text
            time.sleep(retry_interval)

    # def subscribe_price(self, name: str):
    #     # 订阅最新交易价格
    #     data = {
    #         'method': 'SUBSCRIBE',
    #         'params': [
    #             name.lower() + "@aggTrade",
    #         ],
    #         'id': self.subscribe_id
    #     }
    #     self.ws.send(json.dumps(data))
    #     self.subscribe_id += 1


# class Operator(BaseOperator):
#     """
#     现货API操作
#     """

#     def __init__(self):
#         super(Operator, self).__init__()
#         self.ws = None

#     def connect_websocket(self):
#         """
#         调用此函数连接到websocket，以启用websocket相关api
#         """
#         self.ws = websocket.WebSocketApp(
#             'wss://stream.' + base_url + ':9443/ws')
#         self.ws.connect_completed = False  # 自己加的一个成员，用来外部等待连接成功再放行

#         def on_open(ws):
#             print('成功建立现货websocket连接')
#             ws.connect_completed = True

#         def on_message(ws, data):
#             # 收到websocket时使用的处理函数
#             data = json.loads(data)
#             if 'e' in data.keys() and data['e'] == 'aggTrade':
#                 self.price[data['s']] = float(data['p'])
#             else:
#                 print(data)

#         self.ws.on_message = on_message
#         self.ws.on_open = on_open
#         # 额外开一个线程用来运行此websocket
#         self.ws_handle = _thread.start_new_thread(
#             lambda: self.ws.run_forever(ping_interval=300), ())

#         # 等待直到websocket连接成功
#         while not self.ws.connect_completed:
#             time.sleep(0.1)

#     def trade(self, symbol: str, quantity, side, test=False):
#         """
#         在现货下单
#         """
#         if test:
#             test_trade = '/test'
#         else:
#             test_trade = ''
#         headers = {
#             'X-MBX-APIKEY': self.public_key
#         }
#         data = make_query_string(
#             symbol=symbol.upper(),
#             side=side,
#             type='MARKET',
#             quantity=quantity,
#             timestamp=str(round(time.time() * 1000))
#         )
#         signature = hmac.new(self.private_key.encode('ascii'),
#                              data.encode('ascii'), digestmod=sha256).hexdigest()
#         url = 'https://api.' + base_url + '/api/v3/order' + \
#             test_trade + '?' + data + '&signature=' + signature
#         print(url)
#         r = requests.post(url, headers=headers)
#         print(r.status_code)
#         print(r.text)


# class OperatorFuture(BaseOperator):
#     """
#     期货API操作
#     """

#     def __init__(self):
#         super(OperatorFuture, self).__init__()
#         self.ws = None

#     def connect_websocket(self):
#         self.ws = websocket.WebSocketApp('wss://fstream.' + base_url + '/ws')
#         self.ws.connect_completed = False  # 自己加的一个成员，用来外部等待连接成功再放行

#         def on_open(ws):
#             print('成功建立USDT期货websocket连接')
#             ws.connect_completed = True

#         def on_message(ws, data):
#             # 收到websocket时使用的处理函数
#             data = json.loads(data)
#             if 'e' in data.keys() and data['e'] == 'aggTrade':
#                 self.price[data['s']] = float(data['p'])
#             else:
#                 print(data)

#         self.ws.on_message = on_message
#         self.ws.on_open = on_open
#         # 额外开一个线程用来运行此websocket
#         self.ws_handle = _thread.start_new_thread(
#             lambda: self.ws.run_forever(ping_interval=300), ())

#         while not self.ws.connect_completed:
#             time.sleep(0.1)

#     def trade(self, symbol: str, quantity, side, test=True):
#         headers = {
#             'X-MBX-APIKEY': self.public_key
#         }
#         data = make_query_string(
#             symbol=symbol.upper(),
#             side=side,
#             type='MARKET',
#             quantity=quantity,
#             timestamp=str(round(time.time() * 1000))
#         )
#         if test:
#             test_trade = '/test'
#         else:
#             test_trade = ''
#         signature = hmac.new(self.private_key.encode('ascii'),
#                              data.encode('ascii'), digestmod=sha256).hexdigest()
#         url = 'https://fapi.' + base_url + '/fapi/v1/order' + \
#             test_trade + '?' + data + '&signature=' + signature
#         print(url)
#         r = requests.post(url, headers=headers)
#         print(r.status_code)
#         print(r.text)

#     def close_out(self, symbol: str):
#         """
#         将某个货币对平仓
#         """
#         # 先获取货币对的持仓和方向
#         headers = {
#             'X-MBX-APIKEY': self.public_key
#         }
#         data = make_query_string(
#             timestamp=str(round(time.time() * 1000))
#         )
#         signature = hmac.new(self.private_key.encode('ascii'),
#                              data.encode('ascii'), digestmod=sha256).hexdigest()
#         url = 'https://fapi.' + base_url + '/fapi/v2/account' + \
#             '?' + data + '&signature=' + signature
#         print(url)
#         r = requests.get(url, headers=headers)
#         print(r.status_code)
#         print(r.text)
#         if r.status_code != 200:
#             raise Exception('获取持仓数量错误')
#         # 遍历找到需要的货币对
#         for x in json.loads(r.text)['positions']:
#             if x['symbol'] == symbol.upper():
#                 position_amt = x['positionAmt']
#                 break
#         else:
#             raise Exception('未在返回的数据中找到持仓')
#         # 下市价单平仓
#         if float(position_amt) > 0:
#             self.trade(symbol, position_amt, 'SELL')
#         else:
#             # 这里不转为float，怕有精度问题留个0.0000001没平仓，直接使用原始的字符串
#             self.trade(symbol, position_amt.replace('-', ''), 'BUY')


class SmartOperator(BaseOperator):
    """
    智能操作者，不仅整合了期货、现货、杠杆等等所有的操作\n
    还增加了很多自动化的选项，例如下单前自动获取货币精度并向下取整\n
    相当于高度封装版本\n
    缺点在于需要获取额外信息，速度、灵活性不如直接用request
    """

    def __init__(self) -> None:
        super().__init__()

        # # 实例化一个基本操作者，用来发出request
        # self.operator = BaseOperator()

    def get_symbol_precision(self, symbol: str, mode: str = None) -> int:
        """
        获取交易对的报价精度，用于按照数量下单时，得知最大货币下单精度\n
        如果不传入mode，则会自动比较期货和现货，传回一个最低精度，用于双向开仓\n
        :param symbol: 要查询的交易对名字
        :param mode: 要查询的模式，仅可查询MAIN，FUTURE。代表现货和期货
        :return: 查询的小数位数量
        """
        # 转换符号到大写
        symbol = symbol.upper()
        if mode is not None:
            mode = mode.upper()

        # 判断mode有没有输入正确
        if mode != 'MAIN' and mode != 'FUTURE' and mode is not None:
            raise Exception('mode输入错误，仅可输入MAIN或者FUTURE')

        # 根据mode获取对应的交易对精度
        if mode == 'MAIN':
            # 获取每个 现货 交易对的规则（下单精度）
            info = json.loads(self.request(
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
            info = json.loads(self.request(
                'fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
            for e in info:
                if e['symbol'] == symbol:
                    return int(e['quantityPrecision'])
            else:
                raise Exception('没有找到欲查询的精度信息')
        if mode is None:
            main_precision = self.get_symbol_precision(symbol, 'MAIN')
            future_precision = self.get_symbol_precision(symbol, 'FUTURE')
            return min(main_precision, future_precision)

    def trade_market(self, symbol: str, mode: str, amount: Union[str, float, int], side: str, test=False,
                     volume_mode=False) -> str:
        """
        下市价单\n
        需要注意的是，amount可以传入float和str\n
        传入str会直接使用此str的数字进行下单\n
        传入float会自动获取要下单货币对的精度，并向下取整转为str再下单\n
        以成交额方式交易可能会有误差导致下单失败，建议确保有足够资产才使用成交额方式下单\n
        期货以成交额模式下单，会自动计算市值并下单\n
        :param symbol: 要下单的交易对符号，会自动转大写
        :param mode: 要下单的模式，可为MAIN(现货)、FUTURE(期货)、MARGIN(全仓杠杆)、ISOLATED(逐仓杠杆)
        :param amount: 要下单的货币数量，默认是货币数量，如果开启成交额模式，则为成交额
        :param side: 下单方向，字符串格式，只能为SELL或者BUY
        :param test: 是否为测试下单，默认False。测试下单不会提交到撮合引擎，用于测试
        :volume_mode: 是否用成交额模式下单，默认False，开启后amount代表成交额而不是货币数量
        :return: 下单请求提交后，币安返回的结果
        """
        # 转化字符串
        symbol = symbol.upper()
        mode = mode.upper()
        side = side.upper()

        # 判断是否加入test链接
        if test:
            test_trade = '/test'
        else:
            test_trade = ''

        # 判断mode是否填写正确
        if mode != 'MAIN' and mode != 'FUTURE' and mode != 'MARGIN' and mode != 'ISOLATED':
            raise Exception('交易mode填写错误，只能为MAIN FUTURE MARGIN ISOLATED')

        # 判断side是否填写正确
        if side != 'BUY' and side != 'SELL':
            raise Exception('交易side填写错误，只能为SELL或者BUY')

        # 如果期货用了成交额模式，则获取币价来计算下单货币数
        if mode == 'FUTURE' and volume_mode:
            # 获取期货币价最新价格
            latest_price = self.get_latest_price(symbol, 'FUTURE')
            # 一个除法计算要买多少币
            amount = float(amount) / latest_price

        # 如果amount是float格式则根据精度转换一下
        if isinstance(amount, float):
            # 以币数量下单则获取精度转换，成交额下单则直接转为最高精度
            if not volume_mode:
                if mode == 'MAIN':
                    precision = self.get_symbol_precision(symbol, 'MAIN')
                else:
                    precision = self.get_symbol_precision(symbol, 'FUTURE')
                amount = float_to_str_floor(amount, precision)
            else:
                amount = float_to_str_floor(amount)
        elif isinstance(amount, int):
            amount = str(amount)
        elif isinstance(amount, str):
            pass
        else:
            raise Exception('传入amount类型不可识别', type(amount))

        data = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'timestamp': get_timestamp()
        }
        # 使用交易额参数下单(非期货)
        if volume_mode and mode != 'FUTURE':
            data['quoteOrderQty'] = amount
        # 使用货币数下单
        else:
            data['quantity'] = amount
        # 加入全仓或者逐仓参数
        if mode == 'MARGIN':
            data['isIsolated'] = 'FALSE'
        if mode == 'ISOLATE':
            data['isIsolated'] = 'TRUE'

        # 根据期货现货不同，发出不同的请求
        if mode == 'MAIN':
            r = self.request('api', '/api/v3/order', 'POST', data)
        elif mode == 'FUTURE':
            r = self.request('fapi', '/fapi/v1/order', 'POST', data)
        else:
            r = self.request('api', '/sapi/v1/margin/order', 'POST', data)

        return r

    def get_asset_amount(self, symbol: str, mode: str) -> float:
        """
        获取可用资产数量，已冻结的资产不会在里面\n
        期货使用此函数无法查询仓位，只能查询诸如USDT、BNB之类的资产\n
        :param symbol: 要查询的资产符号
        :param mode: MAIN、MARGIN、FUTURE 代表现货、全仓、期货
        """
        symbol = symbol.upper()
        mode = mode.upper()

        if mode != 'MAIN' and mode != 'FUTURE' and mode != 'MARGIN':
            raise Exception('mode只能为MAIN、FUTURE、MARGIN')

        # 根据mode调用不同API查询
        if mode == 'MAIN':
            # 获取当前所有现货资产
            res = json.loads(self.request('api', '/api/v3/account', 'GET', {
                'timestamp': get_timestamp()
            }))['balances']
            # 遍历查找查询的symbol
            for e in res:
                if e['asset'] == symbol:
                    return float(e['free'])
            else:
                raise Exception('没有找到查询的symbol资产')
        elif mode == 'FUTURE':
            # 获取当前所有期货资产
            res = json.loads(self.request('fapi', '/fapi/v2/balance', 'GET', {
                'timestamp': get_timestamp()
            }))
            # 遍历查找查询的symbol
            for e in res:
                if e['asset'] == symbol:
                    return float(e['maxWithdrawAmount'])
            else:
                raise Exception('没有找到查询的symbol资产')
        elif mode == 'MARGIN':
            # 获取当前所有全仓资产
            res = json.loads(self.request('api', '/sapi/v1/margin/account', 'GET', {
                'timestamp': get_timestamp()
            }))['userAssets']
            # 遍历查找查询的symbol
            for e in res:
                if e['asset'] == symbol:
                    return float(e['free'])
            else:
                raise Exception('没有找到查询的symbol资产')
        else:
            raise Exception('未知的mode', mode)

    def get_future_position(self, symbol: str = None) -> Union[float, dict]:
        """
        获取期货仓位情况\n
        如果不传入symbol，则返回字典类型的所有仓位，key为大写symbol\n
        :param symbol: 要查询的交易对
        :return: 返回持仓数量，多空使用正负表示
        """
        # 获取当前所有的期货仓位（不是资产）
        res = json.loads(self.request('fapi', '/fapi/v2/account', 'GET', {
            'timestamp': get_timestamp()
        }))['positions']
        if symbol is not None:
            # 有symbol的情况下直接返回symbol的仓位
            for e in res:
                if e['symbol'] == symbol:
                    return float(e['positionAmt'])
            else:
                raise Exception('没有找到查询的交易对仓位')
        else:
            # 没有symbol的情况下返回交易对的仓位字典
            all_price = {}
            for e in res:
                all_price[e['symbol']] = e['positionAmt']
            return all_price

    def transfer_asset(self, mode: str, asset_symbol: str, amount: Union[str, float, int]):
        """
        划转指定资产，需要开通万向划转权限\n
        可用的模式如下\n
        MAIN_C2C 现货钱包转向C2C钱包\n
        MAIN_UMFUTURE 现货钱包转向U本位合约钱包\n
        MAIN_CMFUTURE 现货钱包转向币本位合约钱包\n
        MAIN_MARGIN 现货钱包转向杠杆全仓钱包\n
        MAIN_MINING 现货钱包转向矿池钱包\n
        C2C_MAIN C2C钱包转向现货钱包\n
        C2C_UMFUTURE C2C钱包转向U本位合约钱包\n
        C2C_MINING C2C钱包转向矿池钱包\n
        UMFUTURE_MAIN U本位合约钱包转向现货钱包\n
        UMFUTURE_C2C U本位合约钱包转向C2C钱包\n
        UMFUTURE_MARGIN U本位合约钱包转向杠杆全仓钱包\n
        CMFUTURE_MAIN 币本位合约钱包转向现货钱包\n
        MARGIN_MAIN 杠杆全仓钱包转向现货钱包\n
        MARGIN_UMFUTURE 杠杆全仓钱包转向U本位合约钱包\n
        MINING_MAIN 矿池钱包转向现货钱包\n
        MINING_UMFUTURE 矿池钱包转向U本位合约钱包\n
        MINING_C2C 矿池钱包转向C2C钱包\n
        MARGIN_CMFUTURE 杠杆全仓钱包转向币本位合约钱包\n
        CMFUTURE_MARGIN 币本位合约钱包转向杠杆全仓钱包\n
        MARGIN_C2C 杠杆全仓钱包转向C2C钱包\n
        C2C_MARGIN C2C钱包转向杠杆全仓钱包\n
        MARGIN_MINING 杠杆全仓钱包转向矿池钱包\n
        MINING_MARGIN 矿池钱包转向杠杆全仓钱包\n
        :param mode: 划转模式
        :param asset_symbol: 欲划转资产
        :param amount: 划转数目，str格式则直接使用，float则转换为最高精度
        """
        # 将资产和模式转为大写
        mode = mode.upper()
        asset_symbol = asset_symbol.upper()

        if isinstance(amount, float):
            amount = float_to_str_round(amount)
        elif isinstance(amount, int):
            amount = str(amount)
        elif isinstance(amount, str):
            pass
        else:
            raise Exception('传入amount类型不可识别', type(amount))

        self.request('api', '/sapi/v1/asset/transfer', 'POST', {
            'type': mode,
            'asset': asset_symbol,
            'amount': amount,
            'timestamp': get_timestamp()
        })

    def get_latest_price(self, symbol: str, mode: str) -> float:
        """
        获取某个货币对的最新价格\n
        :param symbol: 货币对的符号
        :param mode: 查询模式，MAIN或者FUTURE，代表现货或者期货
        """
        symbol = symbol.upper()
        mode = mode.upper()

        # 判断mode是否填写正确
        if mode != 'MAIN' and mode != 'FUTURE':
            raise Exception('交易mode填写错误，只能为MAIN或者FUTURE')

        if mode == 'MAIN':
            price = json.loads(self.request('api', '/api/v3/ticker/price', 'GET', {
                'symbol': symbol
            }, send_signature=False))['price']
        else:
            price = json.loads(self.request('fapi', '/fapi/v1/ticker/price', 'GET', {
                'symbol': symbol
            }, send_signature=False))['price']

        price = float(price)
        return price

    def set_bnb_burn(self, spot_bnb_burn: bool, interest_bnb_burn: bool):
        """
        设置BNB抵扣开关状态
        :param spot_bnb_burn: 是否使用bnb支付现货交易手续费
        :param interest_bnb_burn: 是否使用bnb支付杠杆贷款利息
        """
        data = {
            'spotBNBBurn': 'true' if spot_bnb_burn else 'false',
            'interestBNBBurn': 'true' if interest_bnb_burn else 'false',
        }
        self.request('api', '/sapi/v1/bnbBurn', 'POST', data)

    def get_bnb_burn(self):
        """
        获取BNB抵扣开关状态
        """
        return json.loads(self.request('api', '/sapi/v1/bnbBurn', 'GET', {}))
