
import request from 'request'

async function method_request (func, args) {
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
          reject(err);
          return;
        }
        if (httpResponse.statusCode != 200) {
          reject(httpResponse);
          return;
        }
        let res = JSON.parse(body);
        if (res["msg"] != "success") {
          reject(res);
          return;
        }
        console.log(res);
        resolve(res);
      }
    );
  });
}

export default {
    install(Vue, option) {
        Vue.prototype.method_request = method_request
    }
}