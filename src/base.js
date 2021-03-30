import request from 'request'
import Vue from 'vue'

async function method_request(func, args) {
  // 发送请求
  return await new Promise((resolve, reject) => {
    request.post(
      {
        url: this.localConfig.serverUrl,
        form: {
          function: func,
          args: JSON.stringify(args),
          password: this.localConfig.password,
        },
        timeout: 30000,
      },
      function (err, httpResponse, body) {
        if (err) {
          console.error(err)
          reject(err)
          return
        }
        if (httpResponse.statusCode !== 200) {
          console.error(httpResponse)
          reject(httpResponse)
          return
        }
        let res = JSON.parse(body);
        if (res["msg"] !== "success") {
          console.error(res)
          reject(res)
          return
        }
        console.log(res)
        resolve(res)
      }
    );
  })

}

// 用来方便判断是不是数字
function isNumber(value) {
  if (undefined === value || null === value) {
    return false;
  }
  if (typeof value == "number") {
    return true;
  }
  return !isNaN(value - 0);
}

// 用来快速显示toast
let showToast = {
  success: function (text) {
    Vue.$toast.open({
      message: text,
      type: 'success'
    })
  },
  error: function (text) {
    Vue.$toast.open({
      message: text,
      type: 'error'
    })
  },
  warning: function (text) {
    Vue.$toast.open({
      message: text,
      type: 'warning'
    })
  },
  info: function (text) {
    Vue.$toast.open({
      message: text,
      type: 'info'
    })
  }
}

// 用来将数字转换为指定精度的str格式
function float2strFloor(amount, precision) {
  amount *= Math.pow(10, precision);
  // 向下取整
  amount = Math.floor(amount);
  // 将数字除以精度
  amount /= Math.pow(10, precision);
  return amount.toString()
}

function float2strRound(amount, precision) {
  amount *= Math.pow(10, precision);
  // 向下取整
  amount = Math.round(amount);
  // 将数字除以精度
  amount /= Math.pow(10, precision);
  return amount.toString()
}

function float2strCeil(amount, precision) {
  amount *= Math.pow(10, precision);
  // 向下取整
  amount = Math.ceil(amount);
  // 将数字除以精度
  amount /= Math.pow(10, precision);
  return amount.toString()
}

function toPrecision(amount, precision) {
  amount *= Math.pow(10, precision)
  // 向下取整
  amount = Math.round(amount)
  // 除以精度
  amount /= Math.pow(10, precision)
  return amount
}

// 为了出代码提示来减少错误以及方便重构，本地设置需要在这里获取
let localConfig = {
  get serverUrl() {
    return localStorage.serverUrl
  },
  set serverUrl(val) {
    localStorage.serverUrl = val
  },
  get password() {
    return localStorage.password
  },
  set password(val) {
    localStorage.password = val
  },
  get dataUrl() {
    return localStorage.dataUrl
  },
  set dataUrl(val) {
    localStorage.dataUrl = val
  },
  get subscribeUrl() {
    return localStorage.subscribeUrl
  },
  set subscribeUrl(val) {
    localStorage.subscribeUrl = val
  }
}

// 默认的websocket连接
async function connectDataCenter(nickname) {
  let buf = {}
  let order = 0
  // 创建websocket
  let ws = new WebSocket(this.localConfig.dataUrl)
  // 等待websocket连接完毕
  await new Promise(resolve => {
    ws.onopen = async msg => {
      console.log(nickname, '数据连接成功打开', msg)
      await ws.send(this.localConfig.password)
      resolve()
    }
    ws.onmessage = msg => {
      // 将消息提取出来，根据buf
      msg = JSON.parse(msg.data)
      let comment = msg['comment']
      let data = msg['data']
      // 触发回调
      buf[comment](data)
      // 删除字典元素
      delete buf[comment]
    }
    ws.onclose = msg => {
      console.log(nickname, '数据连接被关闭', msg)
    }
  })
  let getOrder = function () {
    return order++
  }
  let generateGetPromise = function (order) {
    return new Promise(resolve => {
      buf[order] = function (data) {
        resolve(data)
      }
    })
  }
  return {
    getData: async function (tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getDict: async function (tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_DICT',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getFuzzy: async function (tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_FUZZY',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getAll: async function (tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_ALL',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    setData: async function (tags, val) {
      ws.send(JSON.stringify({
        mode: 'SET',
        tags: tags,
        value: val
      }))
    },
    close: async function (code = 1000) {
      await ws.close(code)
    }
  }
}

async function connectSubscribe(nickname) {
  let ws = new WebSocket(this.localConfig.subscribeUrl)
  await new Promise(resolve => {
    ws.onopen = async msg => {
      console.log(nickname, '订阅连接成功打开', msg)
      await ws.send(this.localConfig.password)
      resolve()
    }
    ws.onmessage = msg => {
      console.log(nickname, '收到消息', msg)
    }
    ws.onclose = msg => {
      console.log(nickname, '订阅连接被关闭', msg)
    }
  })
  return {
    precise: async function (tags) {
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_PRECISE',
        tags: tags
      }))
    },
    dict: async function (tags) {
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_DICT',
        tags: tags
      }))
    },
    fuzzy: async function (tags) {
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_FUZZY',
        tags: tags
      }))
    },
    all: async function () {
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_ALL'
      }))
    },
    set onmessage(func) {
      ws.onmessage = func
    },
    close: async function (code = 1000) {
      ws.close(code)
    }
  }
}

export default {
  install(Vue, option) {
    Vue.prototype.method_request = method_request
    Vue.prototype.isNumber = isNumber
    Vue.prototype.showToast = showToast
    Vue.prototype.float2strFloor = float2strFloor
    Vue.prototype.float2strRound = float2strRound
    Vue.prototype.float2strCeil = float2strCeil
    Vue.prototype.toPrecision = toPrecision
    Vue.prototype.localConfig = localConfig
    Vue.prototype.connectDataCenter = connectDataCenter
    Vue.prototype.connectSubscribe = connectSubscribe
  }
}