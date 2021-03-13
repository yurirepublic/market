import websocket
import time
import _thread
import json
import binance_api


def on_open(ws):
    print('websocket成功连接')


def on_message(ws, message):
    print(ws)
    print(message)


def on_error(ws, error):
    print(ws)
    print(error)


def on_close(ws):
    print(ws)
    print("### closed ###")


def main():
    operator = binance_api.SmartOperator()
    listen_key = operator.create_listen_key('MAIN')

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp('wss://stream.binance.com:9443/ws/{}'.format(listen_key), on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close, )
    ws.run_forever()


if __name__ == '__main__':
    main()
