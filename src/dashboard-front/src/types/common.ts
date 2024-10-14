// 分页interface
import type { IPosition } from 'monaco-editor';

export interface IPagination {
  small?: boolean
  offset: number
  limit: number
  count: number
  abnormal?: boolean
  limitList?: number[]
  current: number
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
  enabled?: boolean
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

export enum StaffType {
  RTX = 'rtx',
}
export interface Staff {
  english_name: string;
  chinese_name: string;
  username: string;
  display_name: string;
}

// monaco editor 代码错误高亮要用的类型
export type CodeErrorMsgType = 'All' | 'Error' | 'Warning';

export type ErrorReasonType = {
  json_path?: string,
  paths?: string[],
  pathValue?: any[],
  quotedValue?: string,
  stringToFind?: string,
  message: string,
  isDecorated?: boolean,
  level: CodeErrorMsgType,
  offset?: number,
  position?: IPosition | null,
  regex?: RegExp | null,
};

