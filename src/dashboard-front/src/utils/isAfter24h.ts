export const isAfter24h = (dateString: string) => {
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
