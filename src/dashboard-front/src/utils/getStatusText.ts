// 环境状态文本
export const getStatusText = (status: string) => {
  let text = '';
  switch (status) {
    case 'success':
      text = '已上线';
      break;
    case 'successful':
      text = '已上线';
      break;
    case 'failure':
      text = '发布失败';
      break;
    case 'fail':
      text = '发布失败';
      break;
    case 'failed':
      text = '发布失败';
      break;
    case 'unreleased':
      text = '未发布';
      break;
    case 'delist':
      text = '已下架';
      break;
  }
  return text;
};
