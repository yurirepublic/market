# electron-market
币安非官方套利助手

## 如何编译/调试客户端？
### 环境安装
1. 安装```node.js```
1. 将目录切换到代码根目录
1. 敲入命令```npm install```来安装所有依赖

注：如果网络不好，可以先敲```npm install -g cnpm```，然后敲```cnpm install```来使用国内镜像安装依赖

### 启动调试
```
npm run serve
```

### 启动编译
```
npm run build
```

## 如何部署服务端程序？
因为币安被墙，同时为了提升下单的连接稳定性，请将服务器部署到海外，最好是美国
### 部署服务器的前置条件（强烈建议）
- 一个域名
- 对应域名的https证书

域名可以在godaddy一年十块钱买到，证书可以在阿里云、腾讯云或者Let's Encrype免费签发
### 部署过程
1. 将```server_src```所有内容复制到服务器
1. 将ssl证书的两个文件复制到代码目录
1. 运行```make_default_config.py```创建默认的```config.json```配置文件
1. 修改```config.json```里的内容，主要是域名和证书文件名
1. 输入```screen```新建一个screen窗口
1. 输入```python3 data_center.py```运行数据中心
1. 按下Ctrl+A，弹起后再按下C，以此新建另一个screen子窗口   
1. 输入```python3 api.py```运行主控服务端

注：可以按下Ctrl+A，弹起后按下n，来切换数据中心和主控服务器的控制台，更多操作请搜索screen使用方法
注2：服务端目前相当不稳定，运作时如有问题，请重启api.py，数据中心一般不用重启。