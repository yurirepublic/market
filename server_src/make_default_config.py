"""
运行此脚本，在本地创建默认的配置文件，方便手写修改
已有配置文件也可运行，只会添加没有的条目，不会覆盖
对于多余的条目，会发出警告
"""
import os
import json

default_config = {
    "binance_public_key": "",  # 币安的apikey
    "binance_private_key": "",  # 币安的私钥

    "script_manager_listen_ip": "127.0.0.1",  # 脚本管理器服务端监听ip和端口
    "script_manager_listen_port": 7721,

    "script_client_connect_ip": "127.0.0.1",  # 脚本管理器客户端连接ip和端口
    "script_client_connect_port": 7721,

    "listen_ip": "0.0.0.0",  # 中央服务器http监听ip和端口
    "listen_port": 11327,

    "data_center_http_server_listen_ip": "0.0.0.0",     # 数据中心服务端监听ip和端口
    "data_center_http_server_listen_port": 11327,

    "data_center_http_client_connect_ip": "us.pwp.today",   # 数据中心服务端监听ip和端口
    "data_center_http_client_connect_port": 11327,

    "password": "defaultPassword"  # 中央服务器认证口令
}

try:
    with open('scripts/config.json', 'r', encoding='utf-8') as f:
        config = json.loads(f.read())
except FileNotFoundError:
    config = {}

# 遍历对比没有的条目进行补充
for key in default_config.keys():
    if key not in config.keys():
        config[key] = default_config[key]

# 遍历多余的条目进行警告
for key in config.keys():
    if key not in default_config:
        print('警告：发现多余的key', key)

# 把配置写入文件
with open('scripts/config.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(config))
