// POST /gateways/{gateway_id}/ai/batch-translate/ - 批量翻译文档
export interface IBatchTranslateInputSLZ {
  doc_ids?: number[]
  target_language?: 'zh' | 'en' | null
}

// POST /gateways/{gateway_id}/ai/completion/ - AI Completion
export interface IAICompletionInputSLZ {
  inputs: {
    type: string
    input: string
    enable_streaming?: false
    language?: string
  }
}

/**
 * POST /gateways/{gateway_id}/ai/batch-translate/
 */
export interface IBatchTranslateOutput {
  message: string
  doc_count: number
}

/** 普通（非流式）AI Completion 响应 */
export interface IAICompletionOutput {
  content: string | null
  usage: {
    prompt_tokens: number
    completion_tokens: number
  }
}
