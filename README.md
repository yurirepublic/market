# electron-market
币安非官方套利助手

## 安全起见，如何自己编译客户端？
### 先安装node.js、以及yarn
### 使用包管理安装依赖
```
yarn
```
### 启动编译
```
yarn electron:build
```

## 如何部署服务端程序？
因为币安被墙，同时为了提升下单的连接稳定性，请将服务器部署到海外，最好是美国
### 部署服务器的前置条件（强烈建议）
- 一个域名
- 对应域名的https证书

域名可以在godaddy一年十块钱买到，证书可以在阿里云、腾讯云免费签发
### 将```api.py```、```binance_api.py```复制到服务器
### 安装python的依赖库
```
pip3 install flask flask-cors numpy requests websocket-client
```
### 在代码目录下创建设置文件```config.json```，输入以下内容
```
{
  "binance_public_key": "币安的api密钥",
  "binance_private_key": "币安的私有密钥",
  "listen_ip": "监听ip，一般是0.0.0.0代表监听所有ip",
  "listen_port": "监听端口，不和其他冲突就行，例如11327",
  "password": "验证口令，客户端发来的请求必须口令一致才会执行",
  "use_ssl": true 是否使用https加密，不使用可以免去域名和https证书申请，但你要确保网络环境绝对安全，因为http不加密，被人截获数据包的话连口令都是公开的,
  "ssl_pem": "证书的pem文件目录，例如xxxxx.pem",
  "ssl_key": "证书的key文件目录，例如xxxxx.key"
}

```

### 在后台运行程序
```
nohup python3 -u api.py &
```
### 程序会在后台运行，想看log输入
```
tail nohup.out
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
