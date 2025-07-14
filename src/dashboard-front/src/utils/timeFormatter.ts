import dayjs from 'dayjs';

/**
 * 时间格式化
 * @param val 待格式化时间
 * @param format 格式
 * @returns 格式化后的时间
 */
export function timeFormatter(val: string, format = 'YYYY-MM-DD HH:mm:ss') {
  return val ? dayjs(val).format(format) : '--';
}
