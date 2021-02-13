import request from 'request'
import { ipcRenderer } from 'electron'

// 读取服务器配置
let configReady = false;      // 配置文件是否已准备好
let local_config = {}
async function reload_config() {
  await new Promise(resolve => {
    ipcRenderer.on('read-config-reply', function (event, arg) {
      local_config = arg
      configReady = true
      console.log('配置文件读取完毕')
      console.log(local_config)
      resolve()
    })
    ipcRenderer.send('read-config')
  })
  return
}

async function method_request(func, args) {
  // 等待配置文件准备好
  while (true) {
    if (!configReady) {
      await new Promise(resolve => {
        setTimeout(() => {
          resolve()
        }, 1000)
      })
      if (configReady) {
        console.log('配置文件已读取完毕')
      }

    }
    else {
      break;
    }
  }
  // 发送请求
  return await new Promise((resolve, reject) => {
    request.post(
      {
        url: local_config['server_url'],
        proxy: local_config['proxy_url'] == '' ? null : local_config['proxy_url'],
        form: {
          function: func,
          args: JSON.stringify(args),
          password: local_config['password'],
        },
      },
      function (err, httpResponse, body) {
        if (err) {
          console.error(err)
          reject(err)
          return
        }
        if (httpResponse.statusCode != 200) {
          console.error(httpResponse)
          reject(httpResponse)
          return
        }
        let res = JSON.parse(body);
        if (res["msg"] != "success") {
          console.error(res)
          reject(res)
          return
        }
        console.log(res)
        resolve(res)
        return
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

import Vue from 'vue'

// 用来快速显示toast
function showToast() {
  return {
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
}

export default {
  install(Vue, option) {
    Vue.prototype.method_request = method_request
    Vue.prototype.isNumber = isNumber
    Vue.prototype.showToast = showToast
    Vue.prototype.reload_config = reload_config
  }
}