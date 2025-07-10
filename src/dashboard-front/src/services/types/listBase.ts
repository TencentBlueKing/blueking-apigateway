/**
 * 列表基础类型
 */
export interface ListBase<T extends any[]> {
  count: number
  next: string
  previous: string
  results: T
  permission: T[number]['permission']
}
