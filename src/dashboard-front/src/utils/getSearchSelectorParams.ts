import type { ISearchValue } from 'bkui-vue/lib/search-select/utils';

/**
 * 获取 search selector 参数结果
 * @param data search select 组件选择结果
 * @returns 由每项 id 和 values id 字符串组成的对象
 */
export function getSearchSelectorParams<T extends Record<string, any>>(data: ISearchValue[]): T {
  const params = {};
  data.forEach((value: ISearchValue) => {
    Object.assign(params, { [value.id]: (value.values || []).map(item => `${item.id}`.trim()).join(',') });
  });
  return params as T;
}
