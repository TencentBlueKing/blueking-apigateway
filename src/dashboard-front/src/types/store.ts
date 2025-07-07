export interface IUser {
  username: string;
  display_name?: string;
  avatar_url: string;
  tenant_id: string;
}

export interface IFeatureFlags {
  [key: string]: boolean;
}
