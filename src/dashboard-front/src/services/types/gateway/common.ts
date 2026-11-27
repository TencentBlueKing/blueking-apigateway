// DELETE /gateways/{gateway_id}/resources/batch/ 和 /resource-versions/batch/
export interface IBatchDeleteIdsInput {
  ids: number[]
}

/** 新建网关、资源文档或 MCP Server 后返回的记录 ID */
export interface ICreatedIdOutput {
  id: number
}
