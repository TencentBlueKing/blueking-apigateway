interface IPlugin<T> {
  code?: string
  type?: string
  name: string
  config: T
  config_id: number
}

interface IColumn<T = IBaseTableRow> {
  label: string
  field?: string
  prop?: string
  width?: string
  align?: string
  rowspan?: ({ row }: { row: T }) => number
  index?: number
  render?: ValueRenderType
}

interface IBaseTableRow {
  key?: string
  value?: unknown
  rowSpan?: number
}

type ValueRenderType<T = IBaseTableRow> = () => (props: { row: T }) => unknown;

export {
  IPlugin,
  IColumn,
  IBaseTableRow,
  ValueRenderType,
};
