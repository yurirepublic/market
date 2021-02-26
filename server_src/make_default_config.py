"""
运行此脚本，在本地创建默认的配置文件，方便手写修改
已有配置文件也可运行，只会添加没有的条目，不会覆盖
"""
import os
import json

default_config = {
    "binance_public_key": "",  # 币安的apikey
    "binance_private_key": "",  # 币安的私钥
    "script_manager_listen_ip": "127.0.0.1",  # 脚本管理器服务端监听ip
    "script_manager_listen_port": 7721,  # 脚本管理器服务端监听端口
    "script_client_connect_ip": "127.0.0.1",  # 脚本管理器客户端监听ip
    "script_client_connect_port": 7721,  # 脚本管理器客户端监听端口
    "listen_ip": "0.0.0.0",  # 中央服务器http监听ip
    "listen_port": 11327,  # 中央服务器http监听端口
    "password": "abcdefg"  # 中央服务器认证口令
}

try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.loads(f.read())
except FileNotFoundError:
    config = {}

# 遍历对比没有的条目进行补充
for key in default_config.keys():
    if key not in config.keys():
        config[key] = default_config[key]

# 把配置写入文件
with open('config.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(config))
