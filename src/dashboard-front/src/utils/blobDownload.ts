/**
 * 导出下载公共方法
 * @param {Object} res 接口返回值
 */
export const blobDownLoad = async (res: any) => {
  if (res.ok) {
    const blob: any = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const url = URL.createObjectURL(blob);
    const elment = document.createElement('a');

    elment.download = (disposition.match(/filename="(\S+?)"/) || [])[1];
    elment.href = url;
    elment.click();
    URL.revokeObjectURL(blob);
    return Promise.resolve({ success: true });
  }

  const errorInfo = await res.json();
  return Promise.reject(errorInfo);
};
