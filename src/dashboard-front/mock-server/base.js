function sleep(sec) {
  return new Promise((resolve) => {
    setTimeout(resolve, sec * 1000);
  });
};

const tableList = (app) => {
  app.get('/bk_apigateway/base.js', (req, res) => {
    // await sleep(10);
    const callback = req.query.callback;
    const data = {
      bkAppCode: 'bk_apigateway', // appcode
      name: 'API Gateway', // 站点的名称，通常显示在页面左上角，也会出现在网页title中
      nameEn: 'API Gateway', // 站点的名称-英文
      appLogo: '/static/images/APIgataway-c.png', // 站点logo
      appLogoEn: '/static/images/APIgataway-en.png', // 站点logo
      favicon: '/static/images/favicon.png', // 站点favicon
      helperText: '联系 BK 助手',
      helperTextEn: 'Contact BK Assistant',
      helperLink: 'wxwork://message/?username=BK%E5%8A%A9%E6%89%8B',
      brandImg: '/static/images/brand.png',
      brandImgEn: '/static/images/brand.png',
      brandName: '腾讯蓝鲸智云', // 品牌名，会用于拼接在站点名称后面显示在网页title中
      brandNameEn: 'BlueKing', // 品牌名-英文
      footerInfo: '[技术支持](https://wpa1.qq.com/KziXGWJs?_type=wpa&qidian=true) | [社区论坛](https://bk.tencent.com/s-mart/community/) | [产品官网](https://bk.tencent.com/index/)', // 页脚的内容，仅支持 a 的 markdown 内容格式
      footerInfoEn: '[Support](https://wpa1.qq.com/KziXGWJs?_type=wpa&qidian=true) | [Forum](https://bk.tencent.com/s-mart/community/) | [Official](https://bk.tencent.com/index/)', // 页脚的内容-英文
      footerCopyright: `Copyright © 2012-2024 Tencent BlueKing. All Rights Reserved. V1.0.0`, // 版本信息，包含变量，展示在页脚内容下方
    };
    if (callback){
      res.type('text/javascript');
      res.send(callback + '(' + JSON.stringify(data) + ')');
    } else {
      res.json(data);
    }
  });
};

module.exports = tableList;
