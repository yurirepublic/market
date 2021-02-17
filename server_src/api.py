from flask import Flask, request
from flask_cors import CORS
from flask.wrappers import Response

from scripts import binance_api
from scripts import tools

import json
import time
import multiprocessing
import traceback
import numpy as np
import sys
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)    # 允许跨域


# 创建公用币安api对象
operator = binance_api.SmartOperator()

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.loads(f.read())


@app.route('/', methods=['POST'])
def root():
    print(request.form)
    # 接收指定函数名以及参数并运行
    # 需接收验证口令正确才可运行，口令可以为自定义字符串
    # 接收格式为表单内 { function: '函数名', args: [...参数字符串列表] }
    if request.form['password'] != config['password']:
        return json.dumps({
            'msg': 'error',
            'exception': 'password error'
        })
    try:
        res = json.dumps(eval(request.form['function'])(
            *json.loads(request.form['args'])))
        return res
    except Exception:
        return json.dumps({
            'msg': 'error',
            'exception': traceback.format_exc()
        })


def running_script():
    """
    获取运行中的脚本列表
    """
    # 开启调用脚本管理器的客户端进行操作
    client = tools.Client()
    return {
        'msg': 'success',
        'data': client.status()
    }


def script_list():
    """
    获取本地的脚本列表
    """
    client = tools.Client()
    return {
        'msg': 'success',
        'data': client.ls()
    }


def script_log(pid):
    """
    获取运行中脚本的log信息
    """
    pid = int(pid)
    client = tools.Client()
    return {
        'msg': 'success',
        'data': client.get_log(pid)
    }


def run_script(path):
    """
    运行服务器上某个脚本
    """
    client = tools.Client()
    client.exec(path)
    return {
        'msg': 'success'
    }


def stop_script(pid):
    """
    终止运行服务器上某个脚本
    """
    pid = int(pid)
    client = tools.Client()
    client.kill(pid)
    return {
        'msg': 'success'
    }


def premium_history(symbol):
    """
    查询资金费率历史
    :param symbol:  要查询的交易对
    """
    res = json.loads(operator.request('fapi', '/fapi/v1/fundingRate', 'GET', {
        'symbol': symbol
    }))
    # 清洗一下数据再发回去
    rate = [float(x['fundingRate']) for x in res]
    rate_time = [x['fundingTime'] for x in res]

    return {
        'msg': 'success',
        'data': {
            'rate': rate,
            'time': rate_time
        }
    }


def transfer(trans_type, symbol, quantity):
    """
    万向划转接口
    :param trans_type:  划转类型，看币安API
    :param symbol:  划转的资产符号
    :param quantity:  划转的资产数量

    目前支持的type划转类型:
    MAIN_C2C 现货钱包转向C2C钱包
    MAIN_UMFUTURE 现货钱包转向U本位合约钱包
    MAIN_CMFUTURE 现货钱包转向币本位合约钱包
    MAIN_MARGIN 现货钱包转向杠杆全仓钱包
    MAIN_MINING 现货钱包转向矿池钱包
    C2C_MAIN C2C钱包转向现货钱包
    C2C_UMFUTURE C2C钱包转向U本位合约钱包
    C2C_MINING C2C钱包转向矿池钱包
    UMFUTURE_MAIN U本位合约钱包转向现货钱包
    UMFUTURE_C2C U本位合约钱包转向C2C钱包
    UMFUTURE_MARGIN U本位合约钱包转向杠杆全仓钱包
    CMFUTURE_MAIN 币本位合约钱包转向现货钱包
    MARGIN_MAIN 杠杆全仓钱包转向现货钱包
    MARGIN_UMFUTURE 杠杆全仓钱包转向U本位合约钱包
    MINING_MAIN 矿池钱包转向现货钱包
    MINING_UMFUTURE 矿池钱包转向U本位合约钱包
    MINING_C2C 矿池钱包转向C2C钱包
    MARGIN_CMFUTURE 杠杆全仓钱包转向币本位合约钱包
    CMFUTURE_MARGIN 币本位合约钱包转向杠杆全仓钱包
    MARGIN_C2C 杠杆全仓钱包转向C2C钱包
    C2C_MARGIN C2C钱包转向杠杆全仓钱包
    MARGIN_MINING 杠杆全仓钱包转向矿池钱包
    MINING_MARGIN 矿池钱包转向杠杆全仓钱包
    """
    operator.request('api', '/sapi/v1/asset/transfer', 'POST', {
        'type': trans_type,
        'asset': symbol,
        'amount': quantity,
        'timestamp': binance_api.get_timestamp()
    })

    return {
        'msg': 'success'
    }


def bnb_asset():
    """
    获取账户内BNB资产
    """
    asset = operator.get_asset_amount('BNB', 'MAIN')

    # 获取期货资产
    asset_future = operator.get_asset_amount('BNB', 'FUTURE')

    # 获取BNB最新价格（用于估算USDT市值）
    bnb_price = operator.get_latest_price('BNBUSDT', 'MAIN')

    return {
        'msg': 'success',
        'data': {
            'asset': asset,
            'asset_future': asset_future,
            'asset_usdt': '{:.2f}'.format(float(asset) * float(bnb_price)),
            'asset_future_usdt': '{:.2f}'.format(float(asset_future) * float(bnb_price))
        }
    }


def wallet_money():
    """
    获取账户内余额信息
    """
    print('正在获取账户余额')

    usdt_free = operator.get_asset_amount('USDT', 'MAIN')
    usdt_future_free = operator.get_asset_amount('USDT', 'FUTURE')

    return {
        'msg': 'success',
        'data': {
            'usdt_free': binance_api.float_to_str_round(usdt_free),
            'usdt_future_free': binance_api.float_to_str_round(usdt_future_free)
        }
    }


def create_premium(symbol: str, quantity: float):
    """
    创建套利交易
    """
    def a():
        operator.trade_market(symbol, 'MAIN', quantity, 'BUY')

    def b():
        operator.trade_market(symbol, 'FUTURE', quantity, 'SELL')
    handle_a = multiprocessing.Process(target=a, args=())
    handle_b = multiprocessing.Process(target=b, args=())
    handle_a.start()
    handle_b.start()
    handle_a.join()
    handle_b.join()

    return {
        'msg': 'success'
    }


def destroy_premium(symbol: str, quantity: float):
    """
    平仓一个套利交易
    """
    def a():
        operator.trade_market(symbol, 'MAIN', quantity, 'SELL')

    def b():
        operator.trade_market(symbol, 'FUTURE', quantity, 'BUY')
    handle_a = multiprocessing.Process(target=a, args=())
    handle_b = multiprocessing.Process(target=b, args=())
    handle_a.start()
    handle_b.start()
    handle_a.join()
    handle_b.join()

    return {
        'msg': 'success',
    }


def analyze_premium():
    """
    分析并返回当前所有的套利交易对，还顺带返回孤立仓位
    """
    # 获取当前所有现货资产
    res = json.loads(operator.request('api', '/api/v3/account', 'GET', {
        'timestamp': binance_api.get_timestamp()
    }))['balances']
    # 解析成字典形式
    money = {}
    for e in res:
        money[e['asset']] = float(e['free'])

    # 获取当前所有的期货仓位（不是资产）
    res = json.loads(operator.request('fapi', '/fapi/v2/account', 'GET', {
        'timestamp': binance_api.get_timestamp()
    }))['positions']
    money_future = {}
    for e in res:
        money_future[e['symbol'].replace('USDT', '')] = float(e['positionAmt'])

    # 寻找两边资产的交集
    same = set(money.keys()) & set(money_future.keys())

    # 取两边资产最小的一方作为套利仓位并返回
    pair = []           # 配对的双向仓位（期货必须是做空期货，暂不支持做空现货）
    single = []             # 不配对的孤立仓位
    for e in same:
        if money_future[e] <= 0:
            pair.append({
                'symbol': e + 'USDT',
                'quantity': str(min(money[e], abs(money_future[e])))
            })
        # 两边有不对等的则算入孤立仓位
            single.append({
                'symbol': e + 'USDT',
                # 仅保留10位小数消除浮点精度误差
                'quantity': str(round((money[e] + money_future[e]) * 10000000000) / 10000000000),
                'type': '现货' if money[e] + money_future[e] > 0 else '期货'
            })

    # 筛选掉仓位为0的资产
    pair = list(filter(lambda x: float(x['quantity']) != 0, pair))
    single = list(filter(lambda x: float(x['quantity']) != 0, single))

    return {
        'msg': 'success',
        'data': {
            'pair': pair,
            'single': single
        }
    }


def request_premium():
    """
    获取资金费率交易所需要的表格数据
    """
    res = []    # 里面放的是字典

    # 获取每个 现货 交易对的规则（下单精度）
    info = json.loads(operator.request(
        'api', '/api/v3/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
    percision = {}
    for e in info:
        # 只需要报价单位是USDT的(排除掉BUSD之类的)
        if e['quoteAsset'] == 'USDT':
            percision[e['symbol']] = e['baseAssetPrecision']

    # 获取每个 期货 交易对的规则（下单精度）
    info = json.loads(operator.request(
        'fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
    percision_future = {}
    for e in info:
        percision_future[e['symbol']] = e['quantityPrecision']

    # 统计两边交易对的交集
    same_info = set(percision.keys()) & set(percision_future.keys())

    # 将有效的交易对symbol以及精度放入列表
    for name in same_info:
        res.append({
            "symbol": name,
            "percision": min(percision[name], percision_future[name])
        })

    # 获取期货所有交易对的资金费率（这东西可能有假的，没上市的合约也能查出资金费率）
    print('正在获取期货所有交易对的资金费率')
    premium_index = json.loads(operator.request(
        'fapi', '/fapi/v1/premiumIndex', 'GET', {}))
    premium = {}
    premium_time = {}
    for e in premium_index:
        premium[e['symbol']] = e['lastFundingRate']
        premium_time[e['symbol']] = e['nextFundingTime']

    # 将资金费率放入数据中
    for e in res:
        e['rate'] = premium[e['symbol']]
        e['next_time'] = premium_time[e['symbol']]

    # 查询现货价格
    prices = json.loads(operator.request(
        'api', '/api/v3/ticker/price', 'GET', {}, send_signature=False))
    price_dict = {}
    for e in prices:
        price_dict[e['symbol']] = e['price']
    for e in res:
        if e['symbol'] in price_dict.keys():
            e['price'] = price_dict[e['symbol']]
        else:
            e['price'] = None
    res = list(filter(lambda x: x['price'] is not None, res))

    # 查询期货价格
    prices = json.loads(operator.request(
        'fapi', '/fapi/v1/ticker/price', 'GET', {}, send_signature=False))
    price_dict = {}
    for e in prices:
        price_dict[e['symbol']] = e['price']
    for e in res:
        if e['symbol'] in price_dict.keys():
            e['price_future'] = price_dict[e['symbol']]
        else:
            e['price_future'] = None
    res = list(filter(lambda x: x['price_future'] is not None, res))

    # 计算期货溢价
    for e in res:
        e['future_premium'] = '{:.2f}'.format(
            (float(e['price_future']) / float(e['price']) - 1) * 100)

    # # 查询现货是否有全仓和逐仓交易对
    # allow_margin_symbols = json.loads(operator_future.request(
    #     'api', '/sapi/v1/margin/allPairs', 'GET', {}))
    # allow_margin_symbols_zhucang = json.loads(operator.request(
    #     'api', '/sapi/v1/margin/isolated/allPairs', 'GET', {
    #         'timestamp': binance_api.get_timestamp()
    #     }))

    # allow_margin_symbols = [x['symbol']
    #                         for x in allow_margin_symbols if x['isMarginTrade']]
    # allow_margin_symbols_zhucang = [
    #     x['symbol'] for x in allow_margin_symbols_zhucang if x['isMarginTrade']]

    # # 标记无法全仓和逐仓的交易对
    # for e in res:
    #     if e['symbol'] not in allow_margin_symbols:
    #         e['quan_cang'] = '不可全仓'
    #     else:
    #         e['quan_cang'] = ''

    #     if e['symbol'] not in allow_margin_symbols_zhucang:
    #         e['zhu_cang'] = '不可逐仓'
    #     else:
    #         e['zhu_cang'] = ''

    # 排个序
    res = sorted(res, key=lambda x: abs(float(x['rate'])), reverse=True)

    # 修改下格式
    for e in res:
        e['rate'] = '{:.4f}'.format(float(e['rate']) * 100)
        e['next_time'] = time.strftime(
            '%m-%d %H:%M:%S', time.localtime(int(e['next_time']) / 1000 + 28800))

    # 查询资金费率
    for e in res:
        premium = premium_history(e['symbol'])
        e['premium_history'] = premium['data']

    # 统计平均资金费率
    for e in res:
        e['avg_rate'] = '{:.4f}'.format(
            np.average(e['premium_history']['rate']) * 100)

    return {
        'msg': 'success',
        'data': res
    }


if __name__ == '__main__':
    # # 创建脚本目录
    # if not os.path.exists('scripts'):
    #     os.mkdir('scripts')

    # # 将脚本目录加入path
    # sys.path.append('scripts')

    # 运行脚本管理器
    script_server = tools.Server()

    # 在此主进程运行http服务器
    if config['use_ssl']:
        app.run(config['listen_ip'], config['listen_port'],
                ssl_context=(config['ssl_pem'], config['ssl_key']))
    else:
        app.run(config['listen_ip'], config['listen_port'])
