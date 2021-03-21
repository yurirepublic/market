import data_center


def main():
    print('使用websocket接口')
    ws = data_center.WebsocketClientAdapter()
    print('所有数据', ws.get_all())
    print('不存在的数据', ws.get(['FUCK', 'BULLSHIT']))
    print('模糊数据', ws.get(['main', 'asset']))
    print('精确数据', ws.get(['main', 'asset', 'BNB']))
    ws.close()


if __name__ == '__main__':
    main()
