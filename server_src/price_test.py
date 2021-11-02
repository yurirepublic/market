import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import pickle
import time
import os
import gc
from rich.progress import track
import binance
import asyncio

binance.proxy_url = 'http://127.0.0.1:9910'


def str_2_timestamp(s) -> int:
    # 先转换为时间数组
    array = time.strptime(s, "%Y-%m-%d %H-%M-%S")

    # 转换为时间戳
    t = int(time.mktime(array))
    return t * 1000


def timestamp_2_str(timestamp) -> str:
    timestamp = int(timestamp)
    return time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(timestamp / 1000))


async def get_price(symbol, year=3, price_path='./'):
    """
    注：
    币安的K线获取API，获取数量同时受到limit和时间限制
    请求体的开始时间和结束时间，与任何一个K线的时间产生一丝交集，都会被返回，并非全包括才返回
    """
    end_timestamp = str_2_timestamp('2021-08-03 22-10-00')  # 开爬的时间戳，默认会从当前时间往历史爬，一个文件12h

    symbol = symbol.upper()

    price_path = price_path + '/' + symbol

    # 寻找已经爬到的最早的时间戳
    concat = False
    file_list = os.listdir(price_path)
    for name in file_list:
        if name.find('已合并') != -1:
            print('数据文件已全部下载并合并')
            concat = True
            break
    else:
        if len(file_list) != 0:
            file_list = [x.split(' ')[0] for x in file_list]
            file_list.sort()
            end_timestamp = int(file_list[0])  # 在最早的时间戳往前爬
            print('检查到断点，将从', timestamp_2_str(end_timestamp), end_timestamp, '开始爬')
        else:
            print('未检测到断点，将会从头开始爬')

    operator = binance.Operator()

    cycle_time = 2 * 365 * 3 - len(file_list)  # 爬取3年的数据
    if not concat:
        print('需要爬取的文件数', cycle_time)

    while cycle_time > 0:
        res = await operator.request('api', '/api/v3/klines', 'GET', {
            'symbol': symbol,
            'interval': '1m',
            'startTime': end_timestamp - 12 * 60 * 60 * 1000,
            'endTime': end_timestamp - 1,
            'limit': 1000
        }, send_signature=False, auto_timestamp=False)

        print('数据条目', len(res))
        format_start = res[0][0]
        format_end = res[-1][6]
        print('数据开始时间', format_start, timestamp_2_str(format_start))
        print('数据结束时间', format_end, timestamp_2_str(format_end))
        print('-' * 50, '剩余', cycle_time, '-' * 50)

        with open(price_path + '/{} {} {}.json'.format(format_start, format_end, timestamp_2_str(format_start)),
                  'w') as f:
            f.write(json.dumps(res))

        end_timestamp = res[0][0]

        cycle_time -= 1

        await asyncio.sleep(1)
    # 合并数据文件
    if not concat:
        print('正在合并数据文件')
        file_list = os.listdir(price_path)
        file_list.sort(key=lambda x: int(x.split(' ')[0]))
        all_start = int(file_list[0].split(' ')[0])
        all_end = int(file_list[-1].split(' ')[1])
        klines = []
        for name in track(file_list):
            with open(price_path + '/' + name, 'r') as f:
                klines += json.loads(f.read())
        with open(price_path + '/' + '{} {} 已合并 {} {}.json'.format(
                all_start, all_end, timestamp_2_str(all_start), timestamp_2_str(all_end)), 'w') as f:
            f.write(json.dumps(klines))

    # 连贯性检测
    print('开始检查数据连贯性')
    with open(price_path + '/' + '{} {} 已合并 {} {}.json'.format(
            all_start, all_end, timestamp_2_str(all_start), timestamp_2_str(all_end)), 'r') as f:
        klines = json.loads(f.read())
    last_end = 0
    for block in track(klines):
        block_start = block[0]
        block_end = block[6]
        if block_start != last_end + 1 and last_end != 0:
            print('检测到断点', last_end, block_start, timestamp_2_str(last_end), timestamp_2_str(block_start),
                  int((block_start - last_end) / (1000 * 3600)), '小时')
        last_end = block_end


async def main():
    """
    注：
    币安的K线获取API，获取数量同时受到limit和时间限制
    请求体的开始时间和结束时间，与任何一个K线的时间产生一丝交集，都会被返回，并非全包括才返回
    """
    end_timestamp = str_2_timestamp('2021-08-03 22-10-00')  # 开爬的时间戳，默认会从当前时间往历史爬，一个文件12h

    price_path = 'C:/Users/sraun/Documents/prices'

    # 寻找已经爬到的最早的时间戳
    concat = False
    file_list = os.listdir(price_path)
    for name in file_list:
        if name.find('已合并') != -1:
            print('数据文件已全部下载并合并')
            concat = True
            break
    else:
        if len(file_list) != 0:
            file_list = [x.split(' ')[0] for x in file_list]
            file_list.sort()
            end_timestamp = int(file_list[0])  # 在最早的时间戳往前爬
            print('检查到断点，将从', timestamp_2_str(end_timestamp), end_timestamp, '开始爬')
        else:
            print('未检测到断点，将会从头开始爬')

    operator = binance.Operator()

    cycle_time = 2 * 365 * 3 - len(file_list)  # 爬取3年的数据
    if not concat:
        print('需要爬取的文件数', cycle_time)

    while cycle_time > 0:
        res = await operator.request('api', '/api/v3/klines', 'GET', {
            'symbol': 'BTCUSDT',
            'interval': '1m',
            'startTime': end_timestamp - 12 * 60 * 60 * 1000,
            'endTime': end_timestamp - 1,
            'limit': 1000
        }, send_signature=False, auto_timestamp=False)

        print('数据条目', len(res))
        format_start = res[0][0]
        format_end = res[-1][6]
        print('数据开始时间', format_start, timestamp_2_str(format_start))
        print('数据结束时间', format_end, timestamp_2_str(format_end))
        print('-' * 50, '剩余', cycle_time, '-' * 50)

        with open(price_path + '/{} {} {}.json'.format(format_start, format_end, timestamp_2_str(format_start)),
                  'w') as f:
            f.write(json.dumps(res))

        end_timestamp = res[0][0]

        cycle_time -= 1

        await asyncio.sleep(1)
    # 合并数据文件
    if not concat:
        print('正在合并数据文件')
        file_list = os.listdir(price_path)
        file_list.sort(key=lambda x: int(x.split(' ')[0]))
        all_start = int(file_list[0].split(' ')[0])
        all_end = int(file_list[-1].split(' ')[1])
        klines = []
        for name in track(file_list):
            with open(price_path + '/' + name, 'r') as f:
                klines += json.loads(f.read())
        with open(price_path + '/' + '{} {} 已合并 {} {}.json'.format(
                all_start, all_end, timestamp_2_str(all_start), timestamp_2_str(all_end)), 'w') as f:
            f.write(json.dumps(klines))

    # 连贯性检测
    print('开始检查数据连贯性')
    with open(price_path + '/' + '{} {} 已合并 {} {}.json'.format(
            all_start, all_end, timestamp_2_str(all_start), timestamp_2_str(all_end)), 'r') as f:
        klines = json.loads(f.read())
    last_end = 0
    for block in track(klines):
        block_start = block[0]
        block_end = block[6]
        if block_start != last_end + 1 and last_end != 0:
            print('检测到断点', last_end, block_start, timestamp_2_str(last_end), timestamp_2_str(block_start),
                  int((block_start - last_end) / (1000 * 3600)), '小时')
        last_end = block_end


if __name__ == '__main__':
    asyncio.run(main())
