/**
 * 对元素为对象的数组进行简单排序
 */
export function sortByKey(list: any[] = [], key: string | number) {
  const results: any[] = [];
  let sortKeys = list.map((item: any) => {
    return item[key].toLowerCase();
  });
  sortKeys = [...new Set(sortKeys)];
  sortKeys.sort();
  sortKeys.forEach((sortItem: Record<string, string | number>) => {
    list.forEach((item: Record<string, any>) => {
      if (item[key]?.toLowerCase() === sortItem) {
        results.push(item);
      }
    });
  });
  return results;
}
