export interface IStageData {
  id: number; // 阶段的唯一标识符
  name: string; // 阶段的名称
  description: string; // 阶段的描述（中文）
  description_en: string; // 阶段的描述（英文）
  status: number; // 阶段的状态码
  created_time: string; // 阶段创建的时间
  release: {
    status: string; // 发布的状态
    created_time: string | null; // 发布创建的时间，可能为空
    created_by: string; // 发布创建者的标识
  };
  resource_version: {
    version: string; // 资源版本号
    id: number; // 资源版本的唯一标识符
    schema_version: string; // 资源版本的架构版本号
  };
  publish_id: number; // 发布的唯一标识符
  new_resource_version: string; // 新的资源版本号
  publish_version: string; // 发布版本号
  publish_validate_msg: string; // 发布验证信息
}
