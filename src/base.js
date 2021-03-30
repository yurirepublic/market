import request from 'request'
import Vue from 'vue'


async function method_request(func, args) {
  // 发送请求
  return await new Promise((resolve, reject) => {
    request.post(
      {
        url: localStorage.serverUrl,
        form: {
          function: func,
          args: JSON.stringify(args),
          password: localStorage.password,
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

export default {
  install(Vue, option) {
    Vue.prototype.method_request = method_request
    Vue.prototype.isNumber = isNumber
    Vue.prototype.showToast = showToast
    Vue.prototype.float2strFloor = float2strFloor
    Vue.prototype.float2strRound = float2strRound
    Vue.prototype.float2strCeil = float2strCeil
  }
}