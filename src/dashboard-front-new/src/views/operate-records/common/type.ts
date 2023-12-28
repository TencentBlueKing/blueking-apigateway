export interface DefaultSearchParamsInterface {
  op_type: string
  op_status: string
  op_object?: string
  op_object_type: string
  username?: string
  time_start?: string
  time_end?: string
  keyword?: string
}

export type TableEmptyConfType = {
  keyword: string
  isAbnormal: boolean
};
