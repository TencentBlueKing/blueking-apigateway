export interface IUser {
  username: string;
  avatar_url: string;
}

export interface IFeatureFlags {
  [key: string]: boolean;
}
