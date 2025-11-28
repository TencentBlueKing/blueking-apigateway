/**
 * 找出数组中指定字段的重复值（排除空值）
 * @param arr 要校验的数组
 * @param key 要校验的字段名（必填）
 * @returns 重复的字段值数组（无重复返回空数组）
 */
export function getDuplicateKeys(arr: any[], key: string) {
  // 边界处理：数组为空或未传递 key，直接返回空数组
  if (!Array.isArray(arr) || arr.length <= 1 || !key || typeof key !== 'string') {
    return [];
  }

  const keyMap = new Map(); // 存储字段值 -> 出现次数
  const duplicates = new Set(); // 存储重复的字段值
  const emptyValues = new Set([undefined, null, '']); // 不视为重复的空值

  for (const item of arr) {
    // 跳过非对象/数组的项（避免 item[key] 报错）
    if (typeof item !== 'object' || item === null) {
      continue;
    }

    const field = item[key]; // 获取当前项的字段值
    // 空值不参与重复判定
    if (emptyValues.has(field)) {
      continue;
    }

    const count = (keyMap.get(field) || 0) + 1;
    keyMap.set(field, count);

    // 当出现次数 >= 2 时，添加到重复集合（Set 自动去重，无需担心多次添加）
    if (count >= 2) {
      duplicates.add(field);
    }
  }

  // 转为数组返回（确保返回类型统一）
  return Array.from(duplicates);
}
