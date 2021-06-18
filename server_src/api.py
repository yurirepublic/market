"""
此文件用于提供用于客户端的API
"""
# 导入http框架
import threading

from flask import Flask, request
from flask_cors import CORS
import logging

# 导入基本库
import json
import time
import traceback
import asyncio
import nest_asyncio
import functools

# 导入币安api、脚本管理器
import binance_api
import script_manager

nest_asyncio.apply()  # 开启async嵌套

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# 创建公用loop
loop = asyncio.get_event_loop()

# 创建公用币安api对象
operator: binance_api.Operator = loop.run_until_complete(binance_api.create_operator())

# 创建公用脚本管理器对象
sm: script_manager.Core = script_manager.Core(loop)

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.loads(f.read())


# 用于客户端进行HTTP交互的端口
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
    func_name = request.form['function']
    args = json.loads(request.form['args'])
    try:
        # 使用协程执行指令
        res = loop.run_until_complete(_exec_function(func_name, args))
        res = json.dumps(res)
        return res
    except Exception as e:
        return json.dumps({
            'msg': 'error',
            'traceback': traceback.format_exc(),
            'func': func_name,
            'args': args
        })


async def _exec_function(func_name, args):
    if func_name == 'running_script':
        return await running_script(*args)
    elif func_name == 'script_list':
        return await script_list(*args)
    elif func_name == 'script_log':
        return await script_log(*args)
    elif func_name == 'run_script':
        return await running_script(*args)
    elif func_name == 'stop_script':
        return await stop_script(*args)
    elif func_name == 'transfer':
        return await transfer(*args)
    elif func_name == 'trade_premium':
        return await trade_premium(*args)
    elif func_name == 'isolated_transfer':
        return await isolated_transfer(*args)
    elif func_name == 'query_interest':
        return await query_interest(*args)
    elif func_name == 'loan':
        return await loan(*args)
    elif func_name == 'repay':
        return await repay(*args)
    else:
        return json.dumps({
            'msg': 'function name invalid.'
        })


async def running_script():
    """
    获取运行中的脚本列表
    """
    # 开启调用脚本管理器的客户端进行操作
    return {
        'msg': 'success',
        'data': sm.status()
    }


async def script_list():
    """
    获取本地的脚本列表
    """
    return {
        'msg': 'success',
        'data': sm.ls()
    }


async def script_log(pid):
    """
    获取运行中脚本的log信息
    """
    pid = int(pid)
    return {
        'msg': 'success',
        'data': sm.get_log(pid)
    }


async def run_script(path, input_dict):
    """
    运行服务器上某个脚本
    """
    sm.exec(path, input_dict)
    return {
        'msg': 'success'
    }


async def stop_script(pid):
    """
    终止运行服务器上某个脚本
    """
    pid = int(pid)
    sm.kill(pid)
    return {
        'msg': 'success'
    }


async def transfer(trans_type, symbol, quantity):
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
    await operator.request('api', '/sapi/v1/asset/transfer', 'POST', {
        'type': trans_type,
        'asset': symbol,
        'amount': quantity,
        'timestamp': binance_api.get_timestamp()
    })

    return {
        'msg': 'success'
    }


async def trade_premium(symbol: str, amount: float, side: str, main_mode: str):
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
        await asyncio.gather(
            operator.trade_market(symbol, main_mode, amount, 'BUY'),
            operator.trade_market(symbol, 'FUTURE', amount, 'SELL')
        )

    elif side == 'CLOSE':
        await asyncio.gather(
            operator.trade_market(symbol, main_mode, amount, 'SELL'),
            operator.trade_market(symbol, 'FUTURE', amount, 'BUY')
        )

    return {
        'msg': 'success'
    }


async def isolated_transfer(asset: str, symbol: str, to: str, amount):
    """
    用于逐仓账户的划转，逐仓账户没法用万向划转，只能用这个
    :param asset: 被划转的资产，例如BTC
    :param symbol: 操作的逐仓symbol，例如BTCUSDT
    :param to: 转账的目标，只有SPOT和ISOLATED_MARGIN，代表现货和逐仓
    :param amount: 划转的数量
    """
    asset = asset.upper()
    symbol = symbol.upper()
    to = to.upper()
    if to == 'SPOT':
        _from = 'ISOLATED_MARGIN'
    elif to == 'ISOLATED_MARGIN':
        _from = 'SPOT'
    else:
        return {
            'msg': 'transfer to invalid.',
        }

    await operator.request('api', '/sapi/v1/margin/isolated/transfer', 'POST', {
        'asset': asset,
        'symbol': symbol,
        'transFrom': _from,
        'transTo': to,
        'amount': amount,
        'timestamp': binance_api.get_timestamp()
    })

    return {
        'msg': 'success'
    }


async def query_interest(asset):
    """
    查询某个资产的借贷利息
    """
    asset = asset.upper()
    info = await operator.request('api', '/sapi/v1/margin/interestRateHistory', 'GET', {
        'asset': asset,
        'timestamp': binance_api.get_timestamp()
    })

    return {
        'msg': 'success',
        'data': info[0]['dailyInterestRate']
    }


async def loan(asset, is_isolated, symbol, amount):
    """
    归还某个资产
    """
    asset = asset.upper()
    if isinstance(is_isolated, bool):
        if is_isolated:
            is_isolated = 'TRUE'
        else:
            is_isolated = 'FALSE'
    if is_isolated == 'TRUE':
        symbol = symbol.upper()
        await operator.request('api', '/sapi/v1/margin/loan', 'POST', {
            'asset': asset,
            'isIsolated': is_isolated,
            'symbol': symbol,
            'amount': amount,
            'timestamp': binance_api.get_timestamp()
        })
    elif is_isolated == 'FALSE':
        await operator.request('api', '/sapi/v1/margin/loan', 'POST', {
            'asset': asset,
            'isIsolated': is_isolated,
            'amount': amount,
            'timestamp': binance_api.get_timestamp()
        })
    else:
        return {
            'msg': 'isolated param invalid.'
        }

    return {
        'msg': 'success'
    }


async def repay(asset, is_isolated, symbol, amount):
    asset = asset.upper()
    if isinstance(is_isolated, bool):
        if is_isolated:
            is_isolated = 'TRUE'
        else:
            is_isolated = 'FALSE'
    if is_isolated == 'TRUE':
        symbol = symbol.upper()
        await operator.request('api', '/sapi/v1/margin/repay', 'POST', {
            'asset': asset,
            'isIsolated': is_isolated,
            'symbol': symbol,
            'amount': amount,
            'timestamp': binance_api.get_timestamp()
        })
    elif is_isolated == 'FALSE':
        await operator.request('api', '/sapi/v1/margin/repay', 'POST', {
            'asset': asset,
            'isIsolated': is_isolated,
            'amount': amount,
            'timestamp': binance_api.get_timestamp()
        })
    else:
        return {
            'msg': 'isolated param invalid.'
        }

    return {
        'msg': 'success'
    }


#
# async def analyze_premium():
#     """
#     分析并返回当前所有的套利交易对，还顺带返回孤立仓位
#     """
#     # 连接数据中心准备获取数据
#
#     # 获取当前所有现货资产
#     main_asset = await operator.get_all_asset_amount('MAIN')
#     # 去除掉现货资产的USDT
#     if 'USDT' in main_asset.keys():
#         del main_asset['USDT']
#
#     # 获取当前所有全仓资产
#     margin_asset = await operator.get_all_asset_amount('MARGIN')
#     margin_asset_usdt = 0
#     # 去除掉全仓资产的USDT
#     if 'USDT' in margin_asset:
#         margin_asset_usdt = margin_asset['USDT']
#         del margin_asset['USDT']
#
#     # 获取所有全仓借贷资产
#     margin_borrowed = await operator.get_borrowed_asset_amount('MARGIN')
#     margin_borrowed_usdt = 0
#     # 去除掉全仓资产的USDT
#     if 'USDT' in margin_borrowed:
#         margin_borrowed_usdt = margin_borrowed['USDT']
#         del margin_borrowed['USDT']
#
#     # 计算全仓风险率（借币市值 + 借U / 持币市值 + 持U）* 100
#     margin_asset_value = 0  # 全仓资产市值
#     margin_asset_borrowed = 0  # 全仓借贷资产市值
#     for e in margin_asset.keys():
#         price = await operator.get_latest_price(e + 'USDT', 'MAIN')
#         margin_asset_value += price * margin_asset[e]
#     for e in margin_borrowed.keys():
#         price = await operator.get_latest_price(e + 'USDT', 'MAIN')
#         margin_asset_borrowed += price * margin_borrowed[e]
#     if margin_asset_value == 0:
#         margin_risk = 0
#     else:
#         margin_risk = ((margin_asset_borrowed + margin_borrowed_usdt) / (margin_asset_value + margin_asset_usdt)) * 100
#
#     # 计算全仓触发风险警告所需的波动率
#     if margin_asset_borrowed - 0.8 * margin_asset_value == 0:
#         margin_warning = 99999
#     else:
#         margin_warning = ((0.8 * margin_asset_usdt - margin_borrowed_usdt
#                            ) / (margin_asset_borrowed - 0.8 * margin_asset_value)) * 100
#
#     # 获取当前所有逐仓资产
#     isolated_asset = await operator.get_all_asset_amount('ISOLATED')
#     # 仅保留计价单位是USDT的逐仓，且将逐仓名字仅保留币名
#     new_dict = {}
#     for e in isolated_asset.keys():
#         if isolated_asset[e]['quote_name'] == 'USDT':
#             new_dict[isolated_asset[e]['base_name']] = isolated_asset[e]
#     isolated_asset = new_dict
#
#     # 获取当前所有逐仓借贷资产
#     isolated_borrowed = await operator.get_borrowed_asset_amount('ISOLATED')
#     # 仅保留计价单位是USDT的逐仓，且仅将逐仓名字仅保留币名
#     new_dict = {}
#     for e in isolated_borrowed.keys():
#         if isolated_borrowed[e]['quote_name'] == 'USDT':
#             new_dict[isolated_borrowed[e]['base_name']] = isolated_borrowed[e]
#     isolated_borrowed = new_dict
#
#     # 获取当前所有的期货仓位（不是资产）
#     future_position = await operator.get_future_position()
#     # 将期货符号的USDT去掉，而且仅保留USDT计价的期货
#     new_dict = {}
#     for e in future_position.keys():
#         clear_symbol = e.replace('USDT', '')
#         if clear_symbol != e:
#             new_dict[clear_symbol] = float(future_position[e])
#     future_position = new_dict
#
#     # 计算期货风险率 (期货总市值 / 期货余额) * 100
#     future_position_value = 0
#     future_free = await operator.get_asset_amount('USDT', 'FUTURE')
#     for e in future_position.keys():
#         price = await operator.get_latest_price(e + 'USDT', 'FUTURE')
#         future_position_value += price * abs(future_position[e])
#     if future_free == 0:
#         future_free = 0.00000001  # 给期货一丁点数字避免除0错误
#     future_risk = (future_position_value / future_free) * 100
#
#     # 计算期货风险警报所需市值波动率（500%风险率）
#     if future_position_value != 0:
#         future_warning = (future_position_value + (5 * future_free - future_position_value) / 6) / future_position_value
#         future_warning *= 100
#         future_warning -= 100
#     else:
#         future_warning = 99999
#
#     # 将所有拥有的资产名取个并集
#     all_asset_key = set(main_asset.keys()) | set(margin_asset.keys()) | set(isolated_asset.keys()) | set(
#         future_position.keys()) | set(margin_borrowed.keys()) | set(isolated_borrowed.keys())
#
#     # 以资产名为key，将资产信息写入字典
#     usdt_asset = {}  # 先写USDT资产
#     for key in all_asset_key:
#         info = {
#             'main': main_asset[key] if key in main_asset.keys() else 0,  # 现货持仓
#             'margin': margin_asset[key] if key in margin_asset.keys() else 0,  # 全仓持仓
#             'margin_borrowed': margin_borrowed[key] if key in margin_borrowed.keys() else 0,  # 全仓借入
#             'isolated': isolated_asset[key]['base_asset'] if key in isolated_asset.keys() else 0,  # 逐仓持仓
#             'isolated_borrowed': isolated_borrowed[key]['base_asset'] if key in isolated_borrowed.keys() else 0,
#             'isolated_quote': isolated_asset[key]['quote_asset'] if key in isolated_asset.keys() else 0,
#             'isolated_quote_borrowed': isolated_borrowed[key]['quote_asset'] if key in isolated_borrowed.keys() else 0,
#             'future': future_position[key] if key in future_position.keys() else 0,  # 期货持仓
#             'net': 0,  # 净持仓
#             'hedging': 0,  # 双向持仓
#         }
#         # 计算净持仓
#         info['net'] = info['main'] + info['margin'] + info['isolated'] + info['future'] - info['margin_borrowed'] - \
#                       info['isolated_borrowed']
#         # 计算双向持仓
#         positive = info['main'] + info['margin'] + info['isolated']  # 正向持仓部分
#         if info['future'] > 0:
#             positive += info['future']
#         negative = -info['margin_borrowed'] - info['isolated_borrowed']  # 反向持仓部分
#         if info['future'] < 0:
#             negative += info['future']
#         # 因为反向持仓算出来是负数，所以变为正数
#         negative = -negative
#         # 取最小值为双向持仓量
#         info['hedging'] = min(positive, negative)
#
#         # 计算逐仓风险率
#         if info['isolated'] + info['isolated_quote'] == 0:
#             info['isolated_risk'] = 0
#         else:
#             price = await operator.get_latest_price(key + 'USDT', 'MAIN')
#
#             risk = (info['isolated_borrowed'] * price + info['isolated_quote_borrowed'])
#             risk /= info['isolated'] * price + info['isolated_quote']
#             risk *= 100
#             info['isolated_risk'] = binance_api.float_to_str_ceil(risk, 2)
#
#         usdt_asset[key] = info
#
#     # float转str
#     for e in usdt_asset.keys():
#         for x in usdt_asset[e].keys():
#             usdt_asset[e][x] = binance_api.float_to_str_round(usdt_asset[e][x])
#     margin_risk = binance_api.float_to_str_round(margin_risk, 2)
#     future_risk = binance_api.float_to_str_round(future_risk, 2)
#     future_warning = binance_api.float_to_str_round(future_warning, 2)
#     margin_warning = binance_api.float_to_str_round(margin_warning)
#
#     return {
#         'msg': 'success',
#         'data': {
#             'USDT': usdt_asset,
#             'margin_risk': margin_risk,
#             'future_risk': future_risk,
#             'future_warning': future_warning,
#             'margin_warning': margin_warning
#         }
#     }


def memory_summary():
    # 只在需要的时候引入pympler！ 不然引入后就会影响程序运行
    while True:
        from pympler import summary, muppy
        mem_summary = summary.summarize(muppy.get_objects())
        rows = summary.format_(mem_summary)
        print('\n'.join(rows))
        time.sleep(300)


async def main():
    # # 运行内存泄露检测
    # threading.Thread(target=memory_summary).start()

    # 读取要自动启动的脚本
    print('正在执行自启动脚本:')
    for name in config['exec']:
        print(name)
        sm.exec(name, {})

    ip = config['api']['server_ip']
    port = config['api']['server_port']

    print('即将运行http服务器{}:{}'.format(ip, port))
    loop.run_in_executor(None, functools.partial(app.run, config['api']['server_ip'],
                                                 config['api']['server_port'],
                                                 ssl_context=(config['api']['ssl_pem'],
                                                              config['api']['ssl_key'])))


if __name__ == '__main__':
    loop.run_until_complete(main())
    loop.run_forever()
