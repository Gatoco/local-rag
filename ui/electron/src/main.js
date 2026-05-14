const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'public', 'index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.handle('query', async (event, { question, provider, api_key, model }) => {
  const response = await fetch('http://localhost:8000/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, provider, api_key, model }),
  });
  return response.json();
});

ipcMain.handle('get-providers', async () => {
  const response = await fetch('http://localhost:8000/api/v1/llm/providers');
  return response.json();
});

ipcMain.handle('get-models', async (event, provider) => {
  const response = await fetch(`http://localhost:8000/api/v1/llm/models/${provider}`);
  return response.json();
});

ipcMain.handle('health', async () => {
  const response = await fetch('http://localhost:8000/api/v1/health');
  return response.json();
});