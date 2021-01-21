
import request from 'request'

async function method_request(func, args) {
  return await new Promise(function (resolve, reject) {
    request.post(
      {
        url: "http://us.pwp.today:11327",
        form: {
          function: func,
          args: JSON.stringify(args),
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
  });
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