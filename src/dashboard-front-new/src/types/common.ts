// 分页interface
export interface IPagination {
  small?: boolean
  offset: number
  limit: number
  count: number
}

export interface IDialog {
  isShow: boolean
  title: string
  loading?: boolean
}

export interface IMenu {
  name: string
  title: string
  icon?: string
  children?: IMenu[]
}

export interface IMethodList {
  id: string
  name: string
}
// drop下拉菜单interface
export interface IDropList {
  value: string
  label: string
  disabled?: boolean
}
