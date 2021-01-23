import request from 'request'
import { ipcRenderer } from 'electron'

// 读取服务器配置
let configReady = false;      // 配置文件是否已准备好
const local_config = {}
ipcRenderer.send('read-config')
ipcRenderer.on('read-config-reply', function (event, arg) {
  local_config = arg
  configReady = true
})

async function method_request(func, args) {
  // 等待配置文件准备好
  while (true) {
    if (!configReady) {
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          resolve()
        }, 100)
      })
    }
    else {
      break;
    }
  }

  request.post(
    {
      url: "https://" + local_config['server_ip'] + ':' + local_config['server_port'],
      form: {
        function: func,
        args: JSON.stringify(args),
        password: local_config['password']
      },
    },
    function (err, httpResponse, body) {
      if (err) {
        console.error(err)
        reject(err);
        return;
      }
      if (httpResponse.statusCode != 200) {
        console.error(httpResponse)
        reject(httpResponse);
        return;
      }
      let res = JSON.parse(body);
      if (res["msg"] != "success") {
        console.error(res)
        reject(res);
        return;
      }
      console.log(res);
      resolve(res);
    }
  );
}

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
  }
}