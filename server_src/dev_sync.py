"""
注意，此代码用于快速同步服务端的代码，避免打开sftp上传的繁琐
会与服务端通用api交互
并不会传输文件夹，只会传输此代码文件目录下的所有文件
如果有不想要传输的文件，请将文件名写到dev_dont_sync.txt
"""

import base64
import os
import requests
import json


def main():
    # 读取需要排除的文件
    try:
        with open('dev_dont_sync.txt', 'r', encoding='utf-8') as f:
            exclude = f.readlines()
            for i in range(len(exclude)):
                exclude[i] = exclude[i].strip()
            print('排除列表', exclude)
    except FileNotFoundError:
        exclude = []

    print('本地文件列表')
    want_upload = []
    for name in os.listdir():
        if os.path.isfile(name):
            print(name)
            with open(name, 'rb') as f:
                data = base64.b64encode(f.read())
                want_upload.append({
                    'name': name,
                    'data': data.decode('utf-8')
                })

    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.loads(f.read())
    ip = config['api']['client_ip']
    port = config['api']['client_port']
    url = 'https://' + str(ip) + ':' + str(port)
    r = requests.post(url, data={
        'password': config['password'],
        'function': 'dev_sync',
        'args': json.dumps([want_upload])
    })
    print(json.loads(r.text))
    if json.loads(r.text)['msg'] == 'success' and r.status_code == 200:
        print('同步成功')
    else:
        print('同步失败')


if __name__ == '__main__':
    main()
