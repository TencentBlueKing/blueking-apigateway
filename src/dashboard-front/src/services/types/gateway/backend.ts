import type { IHealthCheck } from '@/types/backend';

/** /gateways/{gateway_id}/backends/ [GET] */
export interface IGatewaysBackendsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  name?: string
  type?: string
  kind?: string
}

export interface IStandardBackendConfigInput {
  type?: string
  timeout: number
  loadbalance: string
  hash_on?: string
  key?: string
  hosts: {
    scheme: string
    host: string
    weight?: number
  }[]
  checks?: Partial<IHealthCheck>
  stage_id: number
}

export interface IAIBackendAuthHeaderInput {
  name: string
  value: string
}

export type AIBackendProviderInput = 'openai' | 'deepseek' | 'openai-compatible';

export type AIBackendFallbackItemInput = 'http_429' | 'http_5xx';

// 模型服务实例；后端严格拒绝未知字段，也不接受 null，可选字段为空时直接省略
export interface IAIBackendInstanceInput {
  // 实例名称：同环境、同模型服务内唯一，也是凭据掩码恢复的身份标识
  name: string
  // 主实例 10，备用实例 0
  priority: number
  provider: AIBackendProviderInput
  // 仅自定义 Provider；内置 Provider 地址固定，不提交
  endpoint?: string
  model_endpoint?: string
  // 仅内置 Provider，不带 Bearer 前缀；未修改的已有凭据回传原掩码
  api_key?: string
  // 仅自定义 Provider
  auth_header?: IAIBackendAuthHeaderInput
  model?: string
  model_options?: Record<string, unknown>
}

export interface IAIBackendBalancerInput {
  // chash 固定按 $bk_app_code 分流，不提交 hash_on/key
  algorithm: 'roundrobin' | 'chash'
}

export interface IAIBackendConfigInput {
  stage_id: number
  // 单位秒，整个环境的实例共用
  timeout: number
  instances: IAIBackendInstanceInput[]
  // 仅多个主实例时提交；省略时后端默认 roundrobin
  balancer?: IAIBackendBalancerInput
  // 仅多实例时提交；省略时后端默认两项都启用，关闭重试必须显式提交 []
  fallback_strategy?: AIBackendFallbackItemInput[]
}

// POST /gateways/{gateway_id}/backends/test-connection/ - 单实例连通性测试
export interface IBackendTestConnectionInputSLZ {
  // 仅测试已保存的实例时携带，用于按 Backend + 环境 + 实例名称恢复已脱敏的凭据
  backend_id?: number
  config: {
    // 新建环境时还没有环境 id，不传
    stage_id?: number
    instance: IAIBackendInstanceInput
  }
}

// POST /gateways/{gateway_id}/backends/ - 创建后端服务
export interface IBackendInputSLZ {
  name: string
  description?: string
  type?: string
  kind?: string
  configs: (IStandardBackendConfigInput | IAIBackendConfigInput)[]
}

/**
 * GET /gateways/{gateway_id}/backends/
 */
export interface IBackendListOutput {
  id: number
  name: string
  description: string
  resource_count: number
  deletable: boolean
  updated_time: string | null
  kind: string
  type: string
}

export interface IStandardBackendConfigOutput {
  checks?: Partial<IHealthCheck>
  hosts: {
    scheme: string
    host: string
    weight: number
  }[]
  loadbalance: string
  stage: {
    id: number
    name: string
  }
  timeout: number
  type: string
  hash_on?: string
  key?: string
}

export interface IAIBackendInstanceOutput {
  name: string
  // 历史未配置 priority 的实例按主实例 10 返回
  priority: number
  provider: 'openai' | 'deepseek' | 'openai-compatible'
  endpoint: string
  model_endpoint: string | null
  // 已脱敏的掩码
  api_key: string | null
  auth_header: {
    name: string
    value: string
  } | null
  model: string | null
  model_options: Record<string, unknown>
}

export interface IAIBackendConfigOutput {
  // 仅模型服务详情返回；环境后端接口的 config 不带环境信息
  stage?: {
    id: number
    name: string
  }
  // 单位秒
  timeout: number
  instances: IAIBackendInstanceOutput[]
  // 历史数据可能缺省
  balancer?: {
    algorithm: 'roundrobin' | 'chash'
  } | null
  fallback_strategy?: ('http_429' | 'http_5xx')[] | null
}

/**
 * PUT /gateways/{gateway_id}/backends/{id}/
 */
export interface IBackendUpdateOutput {
  bound_stages: {
    id: number
    name: string
  }[]
  // 配置发生变化的环境，不代表发布完成
  updated_stages: {
    id: number
    name: string
  }[]
}

export interface IBackendTestConnectionOutput {
  models: string[]
}

/**
 * GET /gateways/{gateway_id}/backends/{id}/
 */
export interface IBackendRetrieveOutput {
  id: number
  name: string
  description: string | null
  kind: string
  type: string
  configs: (IStandardBackendConfigOutput | IAIBackendConfigOutput)[]
}
