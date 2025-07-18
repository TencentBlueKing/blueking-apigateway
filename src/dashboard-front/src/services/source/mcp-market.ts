import http from '../http';

const path = '/gateways';

export const checkMcpServersDel = (apigwId: number, data: {
  stage_id: number
  resource_version_id: number
}) =>
  http.get<{
    has_related_changes: boolean
    deleted_resource_count: number
    details: any[]
  }>(`${path}/${apigwId}/mcp-servers/-/stage-release-check/`, data);
