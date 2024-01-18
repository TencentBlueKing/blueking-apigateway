export enum MethodsEnum {
  POST = 'info',
  GET = 'success',
  DELETE = 'danger',
  PUT = 'warning',
  PATCH = 'info',
  ANY = 'success',
}

export enum PublishSourceEnum {
  gateway_enable = '网关启用',
  gateway_disable = '网关停用',
  version_publish = '版本发布',
  plugin_bind = '插件绑定',
  plugin_update = '插件更新',
  plugin_unbind = '插件解绑',
  stage_disable = '环境下架',
  stage_delete = '环境删除',
  stage_update = '环境更新',
  backend_update = '服务更新',
}

export enum PublishStatusEnum {
  success = '执行成功',
  failure = '执行失败',
  doing = '执行中',
}
