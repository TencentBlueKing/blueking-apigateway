/**
 * 导出下载公共方法
 * @param {Object} res 接口返回值
 */
import type { AxiosResponse } from 'axios';

export function downloadFile(response: AxiosResponse) {
  const contentDisposition = response.headers['content-disposition'] ?? '';
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.download = (contentDisposition.match(/filename="(\S+?)"/) || [])[1];
  link.href = url;
  link.click();
  URL.revokeObjectURL(url);
};
