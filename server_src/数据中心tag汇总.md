### 数据中心TAG汇总速查

```
[]符号里面表示通配符
通配符内符号意义
asset 资产名，例如BNB
symbol 交易对符号，例如BNBUSDT
nickname 服务器识别昵称，例如us1

特别注意：TAG不分前后，没有顺序

下单精度
precision quote main [symbol]
precision quote future [symbol]

资产余额
asset main [asset]
asset future [asset]
asset margin [asset]
asset isolated base [symbol]
asset isolated quote [symbol]

负债余额
borrowed margin base [symbol]
borrowed isolated quote [symbol]

仓位
position future [symbol]

价格
price main [symbol]
price future [symbol]

溢价
premium rate [symbol]
premium dif [symbol]
premium fundingRate [symbol]
premium fundingRateHistory [symbol]

资金费率流水
json fundingFee

服务器运行状况
server status cpu usage percent [nickname]
server status ram usage percent [nickname]
server status disk usage percent [nickname]
```

