// 分页interface
import type { IPosition } from 'monaco-editor';

// 分页接口
export interface IPagination {
  small?: boolean // 是否使用小型分页样式
  offset: number // 数据偏移量
  limit: number // 每页显示的数据条数
  count: number // 数据总条数
  abnormal?: boolean // 是否存在异常
  limitList?: number[] // 可选的每页显示条数列表
  current: number // 当前页码
}

// 对话框接口
export interface IDialog {
  isShow: boolean // 是否显示对话框
  title: string // 对话框标题
  loading?: boolean // 是否显示加载状态
}

export interface IMenu {
  name: string
  title: string
  icon?: string
  enabled?: boolean
  children?: IMenu[]
  // 是否在可编程网关中隐藏，默认 false
  hideInProgrammable?: boolean
}

// drop下拉菜单interface
export interface IDropList {
  value: string
  label: string
  disabled?: boolean
}

// 员工类型枚举
export enum StaffType {
  RTX = 'rtx', // RTX员工类型
}

// 员工接口
export interface Staff {
  english_name: string; // 英文名
  chinese_name: string; // 中文名
  username: string; // 用户名
  display_name: string; // 显示名
}

// monaco editor 代码错误高亮要用的类型
export type CodeErrorMsgType = 'All' | 'Error' | 'Warning';

// 错误原因类型
export type ErrorReasonType = {
  json_path?: string, // JSON路径，可能为空
  paths?: string[], // 路径数组，可能为空
  pathValue?: any[], // 路径值数组，可能为空
  quotedValue?: string, // 引用值，可能为空
  stringToFind?: string, // 要查找的字符串，可能为空
  message: string, // 错误信息
  isDecorated?: boolean, // 是否装饰，可能为空
  level: CodeErrorMsgType, // 错误级别
  offset?: number, // 偏移量，可能为空
  position?: IPosition | null, // 位置，可能为空
  regex?: RegExp | null, // 正则表达式，可能为空
};
