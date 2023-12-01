export interface DefaultSearchParamsInterface {
  op_object_type: string
  op_type: string
  username: string
  time_start: string
  time_end: string
  keyword: string
  op_object: string
}

export type PaginationType = {
  current: number
  count: number
  limit: number
  showTotalCount: boolean
};

export type TableEmptyConfType = {
  keyword: string
  isAbnormal: boolean
};
