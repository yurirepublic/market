"""
获取配对的现货与期货价格，并计算溢价
"""
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
        self.client = await data_center.create_client_adapter()
        # 读取自己的服务器昵称
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
        self.nickname = config['nickname']
        # 启动监测上报
        asyncio.create_task(self.cpu())
        asyncio.create_task(self.ram())
        asyncio.create_task(self.disk())

    async def cpu(self):
        while True:
            cpu_usage = await asyncio.get_running_loop().run_in_executor(None, psutil.cpu_percent)
            await self.client.update({'server', 'status', 'cpu', 'usage', 'percent', self.nickname}, cpu_usage)
            await asyncio.sleep(5)

    async def ram(self):
        while True:
            ram = await asyncio.get_running_loop().run_in_executor(None, psutil.virtual_memory)
            total = ram[0]
            available = ram[1]
            percent = ram[2]
            used = ram[3]
            free = ram[4]
            await self.client.update({'server', 'status', 'ram', 'usage', 'total', self.nickname}, total)
            await self.client.update({'server', 'status', 'ram', 'usage', 'available', self.nickname}, available)
            await self.client.update({'server', 'status', 'ram', 'usage', 'percent', self.nickname}, percent)
            await self.client.update({'server', 'status', 'ram', 'usage', 'used', self.nickname}, used)
            await self.client.update({'server', 'status', 'ram', 'usage', 'free', self.nickname}, free)
            await asyncio.sleep(5)

    async def disk(self):
        while True:
            hdd = psutil.disk_usage('/')
            total = hdd.total
            free = hdd.free
            used = hdd.used
            percent = (used / total) * 100
            await self.client.update({'server', 'status', 'disk', 'usage', 'total', self.nickname}, total)
            await self.client.update({'server', 'status', 'disk', 'usage', 'free', self.nickname}, free)
            await self.client.update({'server', 'status', 'disk', 'usage', 'used', self.nickname}, used)
            await self.client.update({'server', 'status', 'disk', 'usage', 'percent', self.nickname}, percent)
            await asyncio.sleep(5)
