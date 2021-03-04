# 导入http框架
from typing import Union

from flask import Flask, request
from flask_cors import CORS

# 导入基本库
import json
import time
import multiprocessing
from multiprocessing import Process, Manager
import traceback
import numpy as np

# 导入币安api和脚本管理器
from scripts import binance_api
from scripts import tools

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域

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
    # 接收格式为表单内 { function: '函数名', args: [...参数字符串列表]， password: '口令' }
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


def run_script(path, input_dict):
    """
    运行服务器上某个脚本
    """
    client = tools.Client()
    client.exec(path, input_dict)
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
    main_bnb = operator.get_asset_amount('BNB', 'MAIN')

    # 获取期货资产
    future_bnb = operator.get_asset_amount('BNB', 'FUTURE')

    # 获取全仓资产
    margin_bnb = operator.get_asset_amount('BNB', 'MARGIN')

    # 获取BNB最新现货价格（用于估算USDT市值）
    bnb_price = operator.get_latest_price('BNBUSDT', 'MAIN')

    return {
        'msg': 'success',
        'data': {
            'main_bnb': main_bnb,
            'future_bnb': future_bnb,
            'margin_bnb': margin_bnb,
            'bnb_price': float(bnb_price)
        }
    }


def wallet_money():
    """
    获取账户内余额信息
    """
    print('正在获取账户余额')

    main_free = operator.get_asset_amount('USDT', 'MAIN')
    future_free = operator.get_asset_amount('USDT', 'FUTURE')
    margin_free = operator.get_asset_amount('USDT', 'MARGIN')

    return {
        'msg': 'success',
        'data': {
            'main_free': binance_api.float_to_str_round(main_free),
            'future_free': binance_api.float_to_str_round(future_free),
            'margin_free': binance_api.float_to_str_round(margin_free)
        }
    }


def trade_market(symbol: str, mode: str, amount: Union[str, float, int], side: str):
    """
    单向下单\n
    """
    operator.trade_market(symbol, mode, amount, side)

    return {
        'msg': 'success'
    }


def trade_premium(symbol: str, amount: float, side: str, main_mode: str):
    """
    创建套利交易\n
    :param symbol: 创建套利交易的符号
    :param amount: 创建套利交易的货币数
    :param side: 创建套利交易的方向，只能为OPEN或者CLOSE
    :param main_mode: 现货下单的位置，只能为MAIN、MARGIN、ISOLATED
    """
    if side != 'OPEN' and side != 'CLOSE':
        raise Exception('side只能为OPEN或者CLOSE')
    if main_mode != 'MAIN' and main_mode != 'MARGIN' and main_mode != 'ISOLATED':
        raise Exception('main_mode只能为MAIN、MARGIN、ISOLATED')
    if side == 'OPEN':
        def a():
            operator.trade_market(symbol, main_mode, amount, 'BUY')

        def b():
            operator.trade_market(symbol, 'FUTURE', amount, 'SELL')

        handle_a = multiprocessing.Process(target=a, args=())
        handle_b = multiprocessing.Process(target=b, args=())
        handle_a.start()
        handle_b.start()
        handle_a.join()
        handle_b.join()

    elif side == 'CLOSE':
        def a():
            operator.trade_market(symbol, main_mode, amount, 'SELL')

        def b():
            operator.trade_market(symbol, 'FUTURE', amount, 'BUY')

        handle_a = multiprocessing.Process(target=a, args=())
        handle_b = multiprocessing.Process(target=b, args=())
        handle_a.start()
        handle_b.start()
        handle_a.join()
        handle_b.join()

    return {
        'msg': 'success'
    }


def get_bnb_burn():
    """
    获取BNB燃烧状态
    """
    return {
        'msg': 'success',
        'data': operator.get_bnb_burn()
    }


def set_bnb_burn(spot_bnb_burn: bool, interest_bnb_burn: bool):
    """
    设置BNB燃烧状态\n
    会顺带返回设置后的新状态
    """
    operator.set_bnb_burn(spot_bnb_burn, interest_bnb_burn)
    return {
        'msg': 'success',
        'data': operator.get_bnb_burn()
    }


def analyze_premium():
    """
    分析并返回当前所有的套利交易对，还顺带返回孤立仓位
    """
    # 获取当前所有现货资产
    main_asset = operator.get_all_asset_amount('MAIN')
    # 去除掉现货资产的USDT
    if 'USDT' in main_asset.keys():
        del main_asset['USDT']

    # 获取当前所有全仓资产
    margin_asset = operator.get_all_asset_amount('MARGIN')
    # 去除掉全仓资产的USDT
    if 'USDT' in margin_asset:
        del margin_asset['USDT']

    # 获取所有全仓借贷资产
    margin_borrowed = operator.get_borrowed_asset_amount('MARGIN')
    # 去除掉全仓资产的USDT
    if 'USDT' in margin_borrowed:
        del margin_borrowed['USDT']

    # 计算全仓风险率（借贷 / 资产总价值）* 100
    margin_asset_value = 0
    margin_asset_borrowed = 0
    for e in margin_asset.keys():
        price = operator.get_latest_price(e + 'USDT', 'MAIN')
        margin_asset_value += price * margin_asset[e]
    for e in margin_borrowed.keys():
        price = operator.get_latest_price(e + 'USDT', 'MAIN')
        margin_asset_borrowed += price * margin_borrowed[e]
    if margin_asset_value == 0:
        margin_risk = 0
    else:
        margin_risk = (margin_asset_borrowed / margin_asset_value) * 100

    # 获取当前所有逐仓资产
    isolated_asset = operator.get_all_asset_amount('ISOLATED')
    # 仅保留计价单位是USDT的逐仓，且将逐仓名字仅保留币名
    new_dict = {}
    for e in isolated_asset.keys():
        if isolated_asset[e]['quote_name'] == 'USDT':
            new_dict[isolated_asset[e]['base_name']] = isolated_asset[e]
    isolated_asset = new_dict

    # 获取当前所有逐仓借贷资产
    isolated_borrowed = operator.get_borrowed_asset_amount('ISOLATED')
    # 仅保留计价单位是USDT的逐仓，且仅将逐仓名字仅保留币名
    new_dict = {}
    for e in isolated_borrowed.keys():
        if isolated_borrowed[e]['quote_name'] == 'USDT':
            new_dict[isolated_borrowed[e]['base_name']] = isolated_borrowed[e]
    isolated_borrowed = new_dict

    # 获取当前所有的期货仓位（不是资产）
    future_position = operator.get_future_position()
    # 将期货符号的USDT去掉，而且仅保留USDT计价的期货
    new_dict = {}
    for e in future_position.keys():
        clear_symbol = e.replace('USDT', '')
        if clear_symbol != e:
            new_dict[clear_symbol] = float(future_position[e])
    future_position = new_dict

    # 计算期货风险率 (期货总市值 / 期货余额) * 100
    future_position_value = 0
    future_free = operator.get_asset_amount('USDT', 'FUTURE')
    for e in future_position.keys():
        price = operator.get_latest_price(e + 'USDT', 'FUTURE')
        future_position_value += price * abs(future_position[e])
    if future_free == 0:
        future_free = 0.00000001        # 给期货一丁点数字避免除0错误
    future_risk = (future_position_value / future_free) * 100

    # 计算期货风险警报所需市值波动率（500%风险率）
    future_warning = (future_position_value + (5 * future_free - future_position_value) / 6) / future_position_value
    future_warning *= 100
    future_warning -= 100

    # 将所有拥有的资产名取个并集
    all_asset_key = set(main_asset.keys()) | set(margin_asset.keys()) | set(isolated_asset.keys()) | set(
        future_position.keys()) | set(margin_borrowed.keys()) | set(isolated_borrowed.keys())

    # 以资产名为key，将资产信息写入字典
    usdt_asset = {}  # 先写USDT资产
    for key in all_asset_key:
        info = {
            'main': main_asset[key] if key in main_asset.keys() else 0,  # 现货持仓
            'margin': margin_asset[key] if key in margin_asset.keys() else 0,  # 全仓持仓
            'margin_borrowed': margin_borrowed[key] if key in margin_borrowed.keys() else 0,  # 全仓借入
            'isolated': isolated_asset[key]['base_asset'] if key in isolated_asset.keys() else 0,  # 逐仓持仓
            'isolated_borrowed': isolated_borrowed[key]['base_asset'] if key in isolated_borrowed.keys() else 0,
            'isolated_quote': isolated_asset[key]['quote_asset'] if key in isolated_asset.keys() else 0,
            'isolated_quote_borrowed': isolated_borrowed[key]['quote_asset'] if key in isolated_borrowed.keys() else 0,
            'future': future_position[key] if key in future_position.keys() else 0,  # 期货持仓
            'net': 0,  # 净持仓
            'hedging': 0,  # 双向持仓
        }
        # 计算净持仓
        info['net'] = info['main'] + info['margin'] + info['isolated'] + info['future'] - info['margin_borrowed'] - \
                      info['isolated_borrowed']
        # 计算双向持仓
        positive = info['main'] + info['margin'] + info['isolated']  # 正向持仓部分
        if info['future'] > 0:
            positive += info['future']
        negative = -info['margin_borrowed'] - info['isolated_borrowed']  # 反向持仓部分
        if info['future'] < 0:
            negative += info['future']
        # 因为反向持仓算出来是负数，所以变为正数
        negative = -negative
        # 取最小值为双向持仓量
        info['hedging'] = min(positive, negative)

        # 计算逐仓风险率
        if info['isolated'] + info['isolated_quote'] == 0:
            info['isolated_risk'] = 0
        else:
            price = operator.get_latest_price(key + 'USDT', 'MAIN')

            risk = (info['isolated_borrowed'] * price + info['isolated_quote_borrowed'])
            risk /= info['isolated'] * price + info['isolated_quote']
            risk *= 100
            info['isolated_risk'] = binance_api.float_to_str_ceil(risk, 2)

        usdt_asset[key] = info

    # float转str
    for e in usdt_asset.keys():
        for x in usdt_asset[e].keys():
            usdt_asset[e][x] = binance_api.float_to_str_round(usdt_asset[e][x])
    margin_risk = binance_api.float_to_str_round(margin_risk, 2)
    future_risk = binance_api.float_to_str_round(future_risk, 2)
    future_warning = binance_api.float_to_str_round(future_warning, 2)

    return {
        'msg': 'success',
        'data': {
            'USDT': usdt_asset,
            'margin_risk': margin_risk,
            'future_risk': future_risk,
            'future_warning': future_warning
        }
    }

    #
    #
    # # 取两边资产最小的一方作为套利仓位并返回
    # pair = []  # 配对的双向仓位（期货必须是做空期货，暂不支持做空现货）
    # single = []  # 不配对的孤立仓位
    # for e in same:
    #     if future_position[e] <= 0:
    #         pair.append({
    #             'symbol': e + 'USDT',
    #             'quantity': str(min(main_asset[e], abs(future_position[e])))
    #         })
    #         # 两边有不对等的则算入孤立仓位
    #         single.append({
    #             'symbol': e + 'USDT',
    #             # 仅保留10位小数消除浮点精度误差
    #             'quantity': str(round((main_asset[e] + future_position[e]) * 10000000000) / 10000000000),
    #             'type': 'MAIN' if main_asset[e] + future_position[e] > 0 else 'FUTURE'
    #         })
    #
    # # 将全仓交易对也加入孤立仓位（暂时无法分析杠杆仓位）
    # for key in margin_asset.keys():
    #     single.append({
    #         'symbol': key + 'USDT',
    #         'quantity': binance_api.float_to_str_round(margin_asset[key]),
    #         'type': 'MARGIN'
    #     })
    #
    # # 将逐仓交易对也加入孤立仓位（暂时无法分析杠杆仓位）
    # for key in isolated_asset.keys():
    #     single.append({
    #         'symbol': key + 'USDT',
    #         'quantity': binance_api.float_to_str_round(isolated_asset[key]['quote_asset']),
    #         'type': 'ISOLATED'
    #     })
    #
    # # 筛选掉仓位为0的资产
    # pair = list(filter(lambda x: float(x['quantity']) != 0, pair))
    # single = list(filter(lambda x: float(x['quantity']) != 0 and x['symbol'] != 'USDTUSDT', single))


def request_premium():
    """
    获取资金费率交易所需要的表格数据
    """
    res = []  # 里面放的是字典

    # 获取每个 现货 交易对的规则（下单精度）
    info = json.loads(operator.request(
        'api', '/api/v3/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
    precision = {}
    for e in info:
        # 只需要报价单位是USDT的(排除掉BUSD之类的)
        if e['quoteAsset'] == 'USDT':
            precision[e['symbol']] = e['baseAssetPrecision']

    # 获取每个 期货 交易对的规则（下单精度）
    info = json.loads(operator.request(
        'fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False))['symbols']
    precision_future = {}
    for e in info:
        precision_future[e['symbol']] = e['quantityPrecision']

    # 统计两边交易对的交集
    same_info = set(precision.keys()) & set(precision_future.keys())

    # 将有效的交易对symbol以及精度放入列表
    for name in same_info:
        res.append({
            "symbol": name,
            "precision": min(precision[name], precision_future[name])
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

    manager_dict = Manager().dict()

    def _x():
        # 查询现货价格
        manager_dict['prices'] = json.loads(operator.request(
            'api', '/api/v3/ticker/price', 'GET', {}, send_signature=False))

    def _y():
        # 查询期货价格
        manager_dict['prices_future'] = json.loads(operator.request(
            'fapi', '/fapi/v1/ticker/price', 'GET', {}, send_signature=False))

    handle1 = Process(target=_x)
    handle2 = Process(target=_y)
    handle1.start()
    handle2.start()
    handle1.join()
    handle2.join()

    price_dict = {}
    prices = manager_dict['prices']
    for e in prices:
        price_dict[e['symbol']] = e['price']
    for e in res:
        if e['symbol'] in price_dict.keys():
            e['price'] = float(price_dict[e['symbol']])
        else:
            e['price'] = None
    res = list(filter(lambda x: x['price'] is not None, res))

    price_dict = {}
    prices = manager_dict['prices_future']
    for e in prices:
        price_dict[e['symbol']] = e['price']
    for e in res:
        if e['symbol'] in price_dict.keys():
            e['price_future'] = float(price_dict[e['symbol']])
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
        e['premium_history'] = premium_history(e['symbol'])['data']

        # 计算平均资金费率
        if len(e['premium_history']['rate']) == 0:
            e['avg_rate'] = 0
        else:
            e['avg_rate'] = '{:.4f}'.format(
                np.average(e['premium_history']['rate']) * 100)

        # 如果长度不够100，则填充到100
        if len(e['premium_history']['rate']) < 100:
            e['premium_history']['rate'] = list(
                np.zeros(100 - len(e['premium_history']['rate']))) + e['premium_history']['rate']
            e['premium_history']['time'] = list(
                np.zeros(100 - len(e['premium_history']['rate']))) + e['premium_history']['time']

    # # 统计平均资金费率
    # for e in res:

    return {
        'msg': 'success',
        'data': res
    }


if __name__ == '__main__':
    # 运行脚本管理器
    script_server = tools.Server()

    # 在此主进程运行http服务器
    if config['use_ssl']:
        app.run(config['listen_ip'], config['listen_port'],
                ssl_context=(config['ssl_pem'], config['ssl_key']))
    else:
        app.run(config['listen_ip'], config['listen_port'])
