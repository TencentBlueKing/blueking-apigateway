/**
 * @description 获取表格最大显示行数
 * @param {Number} heightTaken 已被占用不能用来展示表格行的高度，单位 px
 * @param {Number} lineHeight 单行表格高度，单位 px
 * @returns {Number} 最大显示行数, 最小为 1
 */
import { useWindowSize } from '@vueuse/core';
import { toValue } from 'vue';

export default function useMaxTableLimit(heightTaken = 347, lineHeight = 42) {
  const viewportHeight = toValue(useWindowSize().height);
  const heightToUse = viewportHeight - heightTaken;
  const limit = Math.floor(heightToUse / lineHeight);
  return limit > 0 ? limit : 1;
}
