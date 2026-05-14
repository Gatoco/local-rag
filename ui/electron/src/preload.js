const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  query: (params) => ipcRenderer.invoke('query', params),
  getProviders: () => ipcRenderer.invoke('get-providers'),
  getModels: (provider) => ipcRenderer.invoke('get-models', provider),
  health: () => ipcRenderer.invoke('health'),
});