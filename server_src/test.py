import asyncio
import binance
import datacenter
import json


async def main():
    client = await datacenter.create_client()
    res = await client.get_dict({'json', 'scriptManager', 'status'})
    for key in res.keys():
        e = res[key]
        print(json.loads(e))
    await client.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
