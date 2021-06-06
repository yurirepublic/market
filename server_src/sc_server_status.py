"""
获取配对的现货与期货价格，并计算溢价
"""
import time

import binance_api
import data_center
import script_manager
import asyncio
import json
import psutil


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '服务器运行状况监控'
        info.description = """
        此脚本会每5s获取CPU、内存、硬盘使用情况
        并将运作状况上传到数据中心
        """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._main())
        loop.run_forever()

    async def _main(self):
        # 连接数据中心
        self.client = await data_center.create_client()
        # 读取自己的服务器昵称
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
        self.nickname = config['nickname']
        # 上传自己的地址和端口信息
        await self.client.update({'server', 'info', 'ip', self.nickname}, config['self_ip'])
        await self.client.update({'server', 'info', 'port', 'api', self.nickname}, config['self_api_port'])
        await self.client.update({'server', 'info', 'port', 'datacenter', self.nickname},
                                 config['self_datacenter_port'])
        await self.client.update({'server', 'info', 'port', 'subscribe', self.nickname}, config['self_subscribe_port'])
        # 启动监测上报
        asyncio.create_task(self.cpu())
        asyncio.create_task(self.ram())
        asyncio.create_task(self.disk())

    async def cpu(self):
        percent_history = [0] * 100
        history_timestamp = [0] * 100
        while True:
            cpu_usage = await asyncio.get_running_loop().run_in_executor(None, psutil.cpu_percent)

            timestamp = round(time.time() * 1000)
            percent_history.pop(0)  # 移除第一个元素
            percent_history.append(cpu_usage)  # 记录最新的元素
            history_timestamp.pop(0)
            history_timestamp.append(timestamp)

            await self.client.update({'server', 'status', 'cpu', 'usage', 'percent', self.nickname}, cpu_usage)
            await self.client.update({'server', 'status', 'cpu', 'usage', 'percentHistory', self.nickname},
                                     percent_history)
            await asyncio.sleep(5)

    async def ram(self):
        percent_history = [0] * 100
        history_timestamp = [0] * 100
        while True:
            ram = await asyncio.get_running_loop().run_in_executor(None, psutil.virtual_memory)
            total = ram[0]
            available = ram[1]
            percent = ram[2]
            used = ram[3]
            free = ram[4]

            timestamp = round(time.time() * 1000)
            percent_history.pop(0)  # 移除第一个元素
            percent_history.append(percent)  # 记录最新的元素
            history_timestamp.pop(0)
            history_timestamp.append(timestamp)

            await self.client.update({'server', 'status', 'ram', 'usage', 'total', self.nickname}, total)
            await self.client.update({'server', 'status', 'ram', 'usage', 'available', self.nickname}, available)
            await self.client.update({'server', 'status', 'ram', 'usage', 'percent', self.nickname}, percent)
            await self.client.update({'server', 'status', 'ram', 'usage', 'used', self.nickname}, used)
            await self.client.update({'server', 'status', 'ram', 'usage', 'free', self.nickname}, free)
            await self.client.update({'server', 'status', 'ram', 'usage', 'percentHistory', self.nickname},
                                     percent_history)
            await asyncio.sleep(5)

    async def disk(self):
        percent_history = [0] * 100
        history_timestamp = [0] * 100
        while True:
            hdd = psutil.disk_usage('/')
            total = hdd.total
            free = hdd.free
            used = hdd.used
            percent = (used / total) * 100

            timestamp = round(time.time() * 1000)
            percent_history.pop(0)  # 移除第一个元素
            percent_history.append(percent)  # 记录最新的元素
            history_timestamp.pop(0)
            history_timestamp.append(timestamp)

            await self.client.update({'server', 'status', 'disk', 'usage', 'total', self.nickname}, total)
            await self.client.update({'server', 'status', 'disk', 'usage', 'free', self.nickname}, free)
            await self.client.update({'server', 'status', 'disk', 'usage', 'used', self.nickname}, used)
            await self.client.update({'server', 'status', 'disk', 'usage', 'percent', self.nickname}, percent)
            await self.client.update({'server', 'status', 'disk', 'usage', 'percentHistory', self.nickname},
                                     percent_history)
            await asyncio.sleep(5)
