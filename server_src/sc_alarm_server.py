import script_manager
import asyncio
import datacenter
import time


class Script(script_manager.Script):
    @staticmethod
    def info():
        info = script_manager.ScriptInfo()
        info.title = '警报器服务端'
        info.description = """
                此脚本会监控服务器上的各个数据，一旦达到危险值就会将数据中心的[alarm, common]设置为0
                如果安全，则会每5s设置为当前的timestamp
                客户端会侦听数据中心这个值，并在以下任意一个条件满足时启动警报流程：
                1. WebSocket连接断开且重连失败
                2. [alarm, common]的timestamp距今超过20秒
                3. [alarm, common]的值为0
                """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.async_main())
        loop.run_forever()

    @staticmethod
    async def async_main():
        client = await datacenter.create_client()
        while True:
            await asyncio.sleep(1)
            # 获取期货资金使用率
            risk = await client.get_precise(['risk', 'future', 'usage'])
            if risk > 5 or risk is None:
                await client.update(['alarm', 'common', 'code'], 0)
                await client.update(['alarm', 'common', 'reason'], '期货资金使用率触发警报' + str(risk))
                continue

            # 获取全仓借贷占比
            risk = await client.get_precise(['risk', 'margin', 'usage'])
            if risk > 0.8 or risk is None:
                await client.update(['alarm', 'common', 'code'], 0)
                await client.update(['alarm', 'common', 'reason'], '全仓借贷占比触发警报' + str(risk))
                continue

            # 获取当前聚合仓位信息
            position = await client.get_precise(['json', 'position'])
            if position is None:
                await client.update(['alarm', 'common', 'code'], 0)
                await client.update(['alarm', 'common', 'reason'], '聚合仓位为空触发警报' + str(position))
                continue
            # 逐个检查逐仓借贷占比
            continue_flag = False
            for e in position:
                if e['isolatedRisk'] > 0.8:
                    await client.update(['alarm', 'common', 'code'], 0)
                    await client.update(['alarm', 'common', 'reason'], '逐仓借贷占比触发警报' + str(e['isolatedRisk']))
                    continue_flag = True
                    break
            if continue_flag:
                continue

            # 获取当前脚本运行状况
            res = await client.get_dict({'json', 'scriptManager', 'status'})
            continue_flag = False
            for key in res.keys():
                for e in res[key]:
                    if e['status'] == '异常结束':
                        await client.update(['alarm', 'common', 'code'], 0)
                        await client.update(['alarm', 'common', 'reason'], '有脚本运行异常')
                        continue_flag = True
            if continue_flag:
                continue



            # 获取磁盘空间大小



            # 向数据中心传输当前timestamp表示安全
            await client.update(['alarm', 'common', 'code'], time.time() * 1000)
