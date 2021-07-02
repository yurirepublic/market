import request from 'request'
import Vue from 'vue'
import { createAxisLabels } from 'echarts/lib/coord/axisTickLabelBuilder'

function apiRequest(func, args, url) {
  let useUrl = localConfig.serverUrl  // 默认使用设置的url
  if (url !== undefined) {
    useUrl = url
  }
  // 发送请求
  return new Promise((resolve, reject) => {
    request.post(
      {
        // url: localConfig.serverUrl
        url: useUrl,
        form: {
          function: func,
          args: JSON.stringify(args),
          password: localConfig.password
        },
        timeout: 30000
      },
      function(err, httpResponse, body) {
        if (err) {
          console.error('http请求错误', err)
          reject(err)
          return
        }
        if (httpResponse.statusCode !== 200) {
          console.error('http响应码错误', httpResponse)
          reject(httpResponse)
          return
        }
        let res = JSON.parse(body)
        if (res['msg'] !== 'success') {
          console.error('服务器响应非成功', res)
          reject(res)
          return
        }
        console.log('http请求返回', res)
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

function strip(num, precision = 12) {
  try {
    return +parseFloat(num.toPrecision(precision))
  } catch (e) {
    return NaN
  }
}

function toFixed(num, n) {
  if (n > 20 || n < 0) {
    throw new RangeError('toFixed() digits argument must be between 0 and 20')
  }
  const number = num
  if (num === undefined) {
    return undefined
  }
  if (isNaN(number) || number >= Math.pow(10, 21)) {
    return number.toString()
  }
  if (typeof (n) == 'undefined' || n === 0) {
    return (Math.round(number)).toString()
  }

  let result = number.toString()
  const arr = result.split('.')

  // 整数的情况
  if (arr.length < 2) {
    result += '.'
    for (let i = 0; i < n; i += 1) {
      result += '0'
    }
    return result
  }

  const integer = arr[0]
  const decimal = arr[1]
  if (decimal.length === n) {
    return result
  }
  if (decimal.length < n) {
    for (let i = 0; i < n - decimal.length; i += 1) {
      result += '0'
    }
    return result
  }
  result = integer + '.' + decimal.substr(0, n)
  const last = decimal.substr(n, 1)

  // 四舍五入，转换为整数再处理，避免浮点数精度的损失
  if (parseInt(last, 10) >= 5) {
    const x = Math.pow(10, n)
    result = (Math.round((parseFloat(result) * x)) + 1) / x
    result = result.toFixed(n)
  }

  return result
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
  }
}

// 全局公用的数据中心websocket对象
let globalDatacenterWebsocket = generateDataCenterWebsocket()   // 初始化时就直接开始连接服务器

async function generateDataCenterWebsocket() {
  let nickname = '全局数据'   // 原本设计是用于多个连接区分名字的，现在全部共用一个连接，似乎就没必要了
  let buf = {}    // 接收响应的缓冲区
  let order = 0   // 响应流水号，用于区分每个响应通道

  // 创建websocket
  let ws = new WebSocket(localConfig.dataUrl)

  // 定义接收和关闭行为
  ws.onmessage = msg => {
    // 将消息提取出来，根据buf内的回调函数传递数据
    msg = JSON.parse(msg.data)
    let comment = msg['comment']
    let item = buf[comment]

    let prepare_mode = item['prepare']
    let callback = item['callback']

    if (prepare_mode === 'PRECISE') {
      let res = msg['data']
      callback(res)
    } else if (prepare_mode === 'DICT') {
      let res = msg['data']
      callback(res)
    } else if (prepare_mode === 'FUZZY') {
      delete msg['comment']
      callback(msg)
    } else if (prepare_mode === 'ALL') {
      delete msg['comment']
      callback(msg)
    } else if (prepare_mode === 'NOT_SUBSCRIBE') {
      let res = msg['data']
      callback(res)
      // 非订阅需要释放掉buf占用
      delete buf[comment]
    }
  }
  ws.onclose = msg => {
    console.warn(nickname, '数据连接被关闭', msg)
  }

  // 等待websocket连接完毕
  await new Promise(resolve => {
    ws.onopen = async msg => {
      console.log(nickname, '数据连接成功打开', msg)
      await ws.send(localConfig.password)
      console.log(nickname, '数据连接密钥发送成功')
      resolve()
    }
  })

  // 用于生成不重复使用的编号
  let getOrder = function() {
    while (true) {
      // 超过10000000(一千万)就归零避免数字溢出
      if (order > 1000000) {
        order = 0
      }
      // 已经使用过的就跳过重新生成
      if (buf[order] !== undefined) {
        order++
        continue
      }
      // 返回生成的order
      return order++
    }
  }

  // 用于生成接收响应的promise，仅供get方式使用，不给订阅使用
  let createResponsePromise = function(order) {
    return new Promise(resolve => {
      buf[order] = {
        prepare: 'NOT_SUBSCRIBE',
        callback: function(res) {
          resolve(res)
        }
      }
    })
  }

  // 返回方法
  return {
    update: async function(tags, value) {
      ws.send(JSON.stringify({
        mode: 'SET',
        tags: tags,
        value: value
      }))
    },
    getPrecise: async function(tags) {
      let order = getOrder()
      let promise = createResponsePromise(order)
      ws.send(JSON.stringify({
        mode: 'GET',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getDict: async function(tags) {
      let order = getOrder()
      let promise = createResponsePromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_DICT',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getFuzzy: async function(tags) {
      let order = getOrder()
      let promise = createResponsePromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_FUZZY',
        tags: tags,
        comment: order
      }))
      return await promise
    },
    getAll: async function() {
      let order = getOrder()
      let promise = createResponsePromise(order)
      ws.send(JSON.stringify({
        mode: 'GET_ALL',
        comment: order
      }))
      return await promise
    },
    subscribePrecise: async function(tags, callback, init = false) {
      let order = getOrder()
      buf[order] = {
        prepare: 'PRECISE',
        callback: callback
      }
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_PRECISE',
        tags: tags,
        comment: order,
        init: init
      }))
    },
    subscribeDict: async function(tags, callback, init = false) {
      let order = getOrder()
      buf[order] = {
        prepare: 'DICT',
        callback: callback
      }
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_DICT',
        tags: tags,
        comment: order,
        init: init
      }))
    },
    subscribeFuzzy: async function(tags, callback, init = false) {
      let order = getOrder()
      buf[order] = {
        prepare: 'FUZZY',
        callback: callback
      }
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_FUZZY',
        tags: tags,
        comment: order,
        init: init
      }))
    },
    subscribeAll: async function(callback, init = false) {
      let order = getOrder()
      buf[order] = {
        prepare: 'ALL',
        callback: callback
      }
      await ws.send(JSON.stringify({
        mode: 'SUBSCRIBE_ALL',
        comment: order,
        init: init
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

const average = arr => arr.reduce((acc, val) => acc + val, 0) / arr.length

// 将时间戳格式化为字符串的工具，使用毫秒级时间戳
function timestamp2str(timestamp, showHour = false) {
  let date = new Date(timestamp)
  // let year = date.getFullYear()
  let month = date.getMonth() + 1
  let day = date.getDate()
  let hour = date.getHours()
  let minute = date.getMinutes()
  let timeStr = month + '-' + day
  if (showHour) {
    timeStr += ' ' + hour + '点'
  }
  return timeStr
}

export default {
  install(Vue, option) {
    Vue.prototype.apiRequest = apiRequest
    Vue.prototype.isNumber = isNumber
    Vue.prototype.showToast = showToast
    Vue.prototype.float2strFloor = float2strFloor
    Vue.prototype.float2strRound = float2strRound
    Vue.prototype.float2strCeil = float2strCeil
    Vue.prototype.strip = strip
    Vue.prototype.toFixed = toFixed
    Vue.prototype.average = average
    Vue.prototype.localConfig = localConfig
    Vue.prototype.connectDataCenter = connectDataCenter
    // Vue.prototype.connectSubscribe = connectSubscribe
    Vue.prototype.timestamp2str = timestamp2str
  }
}