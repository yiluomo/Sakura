// electron/main.js
// Electron 主进程 —— 创建桌面窗口，加载 Vue 3 前端

const { app, BrowserWindow, shell, Menu } = require('electron')
const path = require('path')

// 是否为开发模式（npm run electron:dev 时设置）
const isDev = process.env.NODE_ENV === 'development'

let mainWindow

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1100,
        height: 780,
        minWidth: 800,
        minHeight: 600,
        title: '八重樱',
        // 使用系统原生窗口边框（可换成 false + 自定义标题栏）
        frame: true,
        resizable: true,
        center: true,
        // 窗口图标（打包后生效）
        // icon: path.join(__dirname, '../public/favicon.ico'),
        webPreferences: {
            nodeIntegration: false,   // 安全策略：禁用 Node 注入
            contextIsolation: true,
            sandbox: false,
        },
        backgroundColor: '#1a1a2e',  // 与应用背景色一致，避免白屏闪烁
    })

    // ── 加载页面 ─────────────────────────────────────────
    if (isDev) {
        // 开发模式：加载 Vite 开发服务器（需先启动 npm run dev）
        mainWindow.loadURL('http://localhost:722')
        // 调试时手动开启：Ctrl+Shift+I，或取消下方注释
        // mainWindow.webContents.openDevTools()
    } else {
        // 生产模式：加载构建后的静态文件
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
    }

    // ── 外部链接用默认浏览器打开 ─────────────────────────
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url)
        return { action: 'deny' }
    })

    mainWindow.on('closed', () => {
        mainWindow = null
    })
}

// ── 去掉默认顶部菜单栏 ───────────────────────────────────
Menu.setApplicationMenu(null)

// ── 生命周期 ─────────────────────────────────────────────
app.whenReady().then(() => {
    createWindow()

    // macOS：点击 Dock 图标时重新创建窗口
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})

app.on('window-all-closed', () => {
    // Windows/Linux：关闭所有窗口时退出应用
    if (process.platform !== 'darwin') app.quit()
})
