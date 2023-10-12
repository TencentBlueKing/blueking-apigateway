// 分页interface
export interface IPagination {
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
  children?: IMenu[]
}
