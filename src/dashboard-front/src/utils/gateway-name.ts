export interface IGatewayName {
  name?: string | null
  display_name?: string | null
}

export const getGatewayDisplayName = (gateway?: IGatewayName | null) =>
  gateway?.display_name?.trim() || gateway?.name?.trim() || '--';

/**
 * 是否需要在展示名下方额外展示网关 ID
 * 只要 display_name 与 name 均非空就需要展示，即使两者内容相同
 */
export const hasDistinctDisplayName = (gateway?: IGatewayName | null) => {
  const displayName = gateway?.display_name?.trim();
  const name = gateway?.name?.trim();
  return Boolean(displayName && name);
};

export const getGatewayFullName = (gateway?: IGatewayName | null) => {
  const displayName = getGatewayDisplayName(gateway);
  const name = gateway?.name?.trim();

  if (!name || displayName === name) {
    return displayName;
  }

  return `${displayName} (${name})`;
};
