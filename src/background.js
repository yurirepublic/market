'use strict'

import { app, protocol, BrowserWindow } from 'electron'
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
import installExtension, { VUEJS_DEVTOOLS } from 'electron-devtools-installer'
const isDevelopment = process.env.NODE_ENV !== 'production'
import fs from 'fs'




// Scheme must be registered before the app is ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
])

async function createWindow() {
  // Create the browser window.
  const win = new BrowserWindow({
    // 这里针对开发环境弄大一点宽度
    width: isDevelopment ? 996 : 1366,
    height: isDevelopment ? 635 : 768,
    webPreferences: {
      // Use pluginOptions.nodeIntegration, leave this alone
      // See nklayman.github.io/vue-cli-plugin-electron-builder/guide/security.html#node-integration for more info
      nodeIntegration: process.env.ELECTRON_NODE_INTEGRATION,
    },
    frame: false,
  })


  // 使用fs读取配置文件
  let local_config = {}
  fs.readFile('config.json', 'utf-8', function (err, data) {
    // 没错误的的话，err是null
    if (err && err.code === 'ENOENT') {
      // 没有配置文件就写入默认设置
      local_config['server_url'] = ''
      local_config['password'] = ''
      return;
    }
    // 有配置文件就读成json
    local_config = JSON.parse(data)
  })

  // 定义一下IPC事件
  let ipcMain = require('electron').ipcMain
  ipcMain.on("window-minimize", function () {
    win.minimize()
  })
  ipcMain.on("window-maximize", function () {
    win.maximize()
  })
  ipcMain.on('window-restore', function () {
    win.restore()
  })
  ipcMain.on("window-close", function () {
    console.log('window-close')
    win.close()
  })
  ipcMain.on("read-config", function (event, arg) {
    console.log('收到读取配置文件请求')
    event.sender.send("read-config-reply", local_config)
  })
  ipcMain.on("save-config", function (event, arg) {
    // 将配置写入配置文件
    fs.writeFile('config.json', JSON.stringify(arg), 'utf-8', err => {
      if (err) {
        event.sender.send('save-config-reply', 'fail')
      }
      else {
        event.sender.send('save-config-reply', 'success')
      }
    })
  })


  win.setMenu(null)

  win.on('close', function (e) {
    e.preventDefault()
    win.destroy()
  })

  // 开发者模式把窗口弄宽一点方便开发
  if (!app.isPackaged) {
    win.setSize(1366, 768)
  }

  if (process.env.WEBPACK_DEV_SERVER_URL) {
    // Load the url of the dev server if in development mode
    await win.loadURL(process.env.WEBPACK_DEV_SERVER_URL)
    if (!process.env.IS_TEST) win.webContents.openDevTools()
  } else {
    createProtocol('app')
    // Load the index.html when not in development
    win.loadURL('app://./index.html')
  }


}

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', async () => {
  if (isDevelopment && !process.env.IS_TEST) {
    // Install Vue Devtools
    try {
      await installExtension(VUEJS_DEVTOOLS)
    } catch (e) {
      console.error('Vue Devtools failed to install:', e.toString())
    }
  }
  createWindow()
})

// Exit cleanly on request from parent process in development mode.
if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit()
      }
    })
  } else {
    process.on('SIGTERM', () => {
      app.quit()
    })
  }
}
