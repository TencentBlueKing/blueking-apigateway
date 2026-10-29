export interface IGatewayName {
  name?: string | null
  display_name?: string | null
}

export const getGatewayDisplayName = (gateway?: IGatewayName | null) =>
  gateway?.display_name?.trim() || gateway?.name?.trim() || '--';

/**
 * 是否存在与网关 ID 不同的展示名
 * 后端 display_name 在为空时会回退到 name，此时两者相同，
 * 不应再重复渲染第二行 ID，也应避免出现 `foo (foo)` 这种展示
 */
export const hasDistinctDisplayName = (gateway?: IGatewayName | null) => {
  const displayName = gateway?.display_name?.trim();
  return Boolean(displayName);
};

export const getGatewayFullName = (gateway?: IGatewayName | null) => {
  const displayName = getGatewayDisplayName(gateway);
  const name = gateway?.name?.trim();

  if (!name) {
    return displayName;
  }

  return `${displayName} (${name})`;
};
