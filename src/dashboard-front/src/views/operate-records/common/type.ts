// 定义默认搜索参数接口
export interface DefaultSearchParamsInterface {
  op_type: string // 操作类型
  op_status: string // 操作状态
  op_object?: string // 操作对象（可选）
  op_object_type: string // 操作对象类型
  username?: string // 用户名（可选）
  time_start?: string // 开始时间（可选）
  time_end?: string // 结束时间（可选）
  keyword?: string // 关键词（可选）
  order_by?: string // 排序字段（可选）
}

// 定义表格空数据配置类型
export type TableEmptyConfType = {
  keyword: string // 关键词
  isAbnormal: boolean // 是否异常
};
