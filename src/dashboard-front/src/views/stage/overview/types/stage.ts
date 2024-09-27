export interface IStageData {
  id: number;
  name: string;
  description: string;
  description_en: string;
  status: number;
  created_time: string;
  release: {
    status: string;
    created_time: string | null;
    created_by: string;
  };
  resource_version: {
    version: string;
    id: number;
    schema_version: string
  };
  publish_id: number;
  new_resource_version: string;
  publish_version: string;
  publish_validate_msg: string;
}
