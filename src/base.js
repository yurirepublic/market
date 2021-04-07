import request from 'request'
import Vue from 'vue'

function apiRequest(func, args) {
  // 发送请求
  return new Promise((resolve, reject) => {
    request.post(
      {
        url: localConfig.serverUrl,
        form: {
          function: func,
          args: JSON.stringify(args),
          password: localConfig.password
        },
        timeout: 30000
      },
      function(err, httpResponse, body) {
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
        let res = JSON.parse(body)
        if (res['msg'] !== 'success') {
          console.error(res)
          reject(res)
          return
        }
        console.log(res)
        resolve(res)
      }
    )
  })
}

// 用来方便判断是不是数字
function isNumber(value) {
  if (undefined === value || null === value) {
    return false
  }
  if (typeof value == 'number') {
    return true
  }
  return !isNaN(value - 0)
}

// 用来快速显示toast
let showToast = {
  success: function(text) {
    Vue.$toast.open({
      message: text,
      type: 'success'
    })
  },
  error: function(text) {
    Vue.$toast.open({
      message: text,
      type: 'error'
    })
  },
  warning: function(text) {
    Vue.$toast.open({
      message: text,
      type: 'warning'
    })
  },
  info: function(text) {
    Vue.$toast.open({
      message: text,
      type: 'info'
    })
  }
}

// 用来将数字转换为指定精度的str格式
function float2strFloor(amount, precision) {
  amount *= Math.pow(10, precision)
  // 向下取整
  amount = Math.floor(amount)
  // 将数字除以精度
  amount /= Math.pow(10, precision)
  return amount.toString()
}

function float2strRound(amount, precision) {
  amount *= Math.pow(10, precision)
  // 向下取整
  amount = Math.round(amount)
  // 将数字除以精度
  amount /= Math.pow(10, precision)
  return amount.toString()
}

function float2strCeil(amount, precision) {
  amount *= Math.pow(10, precision)
  // 向下取整
  amount = Math.ceil(amount)
  // 将数字除以精度
  amount /= Math.pow(10, precision)
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

// 全局公用的数据中心websocket对象
let globalDatacenterWebsocket = generateDataCenterWebsocket()

async function generateDataCenterWebsocket() {
  let nickname = '全局数据'
  let buf = {}
  let order = 0
  // 创建websocket
  let ws = new WebSocket(localConfig.dataUrl)
  // 等待websocket连接完毕
  await new Promise(resolve => {
    ws.onopen = async msg => {
      console.log(nickname, '数据连接成功打开', msg)
      await ws.send(localConfig.password)
      console.log(nickname, '数据连接密钥发送成功')
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
  let getOrder = function() {
    return order++
  }
  let generateGetPromise = function(order) {
    return new Promise(resolve => {
      buf[order] = function(data) {
        resolve(data)
      }
    })
  }
  return {
    getData: async function(tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getDict: async function(tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_DICT',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getFuzzy: async function(tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_FUZZY',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getAll: async function(tags) {
      let order = getOrder()
      let promise = generateGetPromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_ALL',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    setData: async function(tags, val) {
      ws.send(JSON.stringify({
        mode: 'SET',
        tags: tags,
        value: val
      }))
    },
    close: async function(code = 1000) {
      await ws.close(code)
    }
  }
}

// 单例模式创建数据中心连接
async function connectDataCenter() {
  return await globalDatacenterWebsocket
}

let globalSubscribeWebsocket = generateSubscribeWebsocket()   // 全局公用的订阅socket对象promise

async function generateSubscribeWebsocket() {
  let nickname = '全局订阅'
  let subscribe = {}    // 用来订阅的字典，key是分配的comment，value是回调函数
  let order = 0
  let getOrder = function() {
    return order++
  }
  // 创建websocket
  let ws = new WebSocket(localConfig.subscribeUrl)
  await new Promise(resolve => {
    ws.onopen = async msg => {
      console.log(nickname, '订阅连接成功打开', msg)
      await ws.send(localConfig.password)
      console.log(nickname, '订阅连接密钥发送成功')
      resolve()
    }
    ws.onmessage = msg => {
      msg = JSON.parse(msg.data)
      subscribe[msg['comment']](msg)
    }
    ws.onclose = msg => {
      console.log(nickname, '订阅连接被关闭', msg)
    }
  })


  return {
    precise: async function(tags, callback) {
      let order = getOrder()
      subscribe[order] = callback
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_PRECISE',
        tags: tags,
        comment: order
      }))
    },
    dict: async function(tags, callback) {
      let order = getOrder()
      subscribe[order] = callback
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_DICT',
        tags: tags,
        comment: order
      }))
    },
    fuzzy: async function(tags, callback) {
      let order = getOrder()
      subscribe[order] = callback
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_FUZZY',
        tags: tags,
        comment: order
      }))
    },
    all: async function(callback) {
      let order = getOrder()
      subscribe[order] = callback
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_ALL',
        comment: order
      }))
    },
    // 如果需要完整接管数据接收，可以修改此回调
    set onmessage(func) {
      ws.onmessage = func
    },
    close: async function(code = 1000) {
      ws.close(code)
    }
  }
}

async function connectSubscribe() {
  return await globalSubscribeWebsocket
}

const average = arr => arr.reduce((acc, val) => acc + val, 0) / arr.length

export default {
  install(Vue, option) {
    Vue.prototype.apiRequest = apiRequest
    Vue.prototype.isNumber = isNumber
    Vue.prototype.showToast = showToast
    Vue.prototype.float2strFloor = float2strFloor
    Vue.prototype.float2strRound = float2strRound
    Vue.prototype.float2strCeil = float2strCeil
    Vue.prototype.toPrecision = toPrecision
    Vue.prototype.average = average
    Vue.prototype.localConfig = localConfig
    Vue.prototype.connectDataCenter = connectDataCenter
    Vue.prototype.connectSubscribe = connectSubscribe
  }
}