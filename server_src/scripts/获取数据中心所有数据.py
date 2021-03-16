import data_center


def main():
    client = data_center.Client()
    print('所有数据', client.get_all())
    print('不存在的数据', client.get(['FUCK', 'BULLSHIT']))
    print('模糊数据', client.get(['main', 'asset']))
    print('精确数据', client.get(['main', 'asset', 'BNB']))


if __name__ == '__main__':
    main()
