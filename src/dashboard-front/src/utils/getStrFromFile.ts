/**
 * 读取文件内容
 * @param {Object} file file文件对象
 */
export const getStrFromFile = (file: any) => {
  let resolveFn = (value: unknown) => {
  };
  const PromiseFunc = new Promise(resolve => resolveFn = resolve);
  // ▼ new 一个 FileReader
  // ▼ 然后监听 onload 事件，从中取得文本内容
  const oReader = Object.assign(new FileReader(), {
    onload(event: any) {
      resolveFn(event.target.result);
    },
  });
  oReader.readAsText(file);
  return PromiseFunc;
};

export const is24HoursAgo = (dateString: string) => {
  // 将日期字符串转换为 Date 对象
  const date: any = new Date(dateString);

  // 获取当前时间
  const now: any = new Date();

  // 计算时间差，单位为毫秒
  const diff = now - date;

  // 将时间差转换为小时
  const hours = diff / (1000 * 60 * 60);

  // 判断时间差是否大于等于24小时
  return hours >= 24;
};
