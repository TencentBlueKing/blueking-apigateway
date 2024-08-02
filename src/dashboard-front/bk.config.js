const mockServer = require('./mock-server');
const MonacoWebpackPlugin = require('monaco-editor-webpack-plugin')
// const { DefinePlugin } = require('webpack');

module.exports = {
  host: process.env.BK_APP_HOST,
  port: process.env.BK_APP_PORT,
  publicPath: '/',
  cache: true,
  open: true,
  replaceStatic: true,

  // webpack config 配置
  configureWebpack() {
    return {
      devServer: {
        setupMiddlewares: mockServer,
        host: 'dev-t.paas3-dev.bktencent.com',
        client: {
          overlay: false,
        },
        https: !process.env.BK_HTTPS,
      },
    };
  },

  chainWebpack: config => {
    config
    .plugin('monaco')
    .use(new MonacoWebpackPlugin());
    return config
  }
};
