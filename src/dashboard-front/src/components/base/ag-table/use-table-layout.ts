/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

import type { ITableLimit, TableRowSize } from './types';

const DEFAULT_PAGE_SIZE = 10;
const DEFAULT_ALLOCATED_HEIGHT = 186;
const DEFAULT_BOTTOM_OFFSET = 24;
const MIN_AUTO_CONTENT_HEIGHT = 200;
const TDESIGN_PAGINATION_HEIGHT = 64;
const LEGACY_PAGINATION_HEIGHT = 60;

type TableHeights = Record<TableRowSize, [rowHeight: number, headerHeight: number]>;

// 同一行高设置在不同表格模式下对应的行高、表头高度（px）。
const TABLE_HEIGHTS = {
  bkui: {
    mini: [42, 42],
    small: [42, 42],
    medium: [60, 42],
    large: [78, 42],
  },
  tdesign: {
    mini: [32, 32],
    small: [36, 36],
    medium: [42, 42],
    large: [56, 56],
  },
  other: {
    mini: [32, 32],
    small: [42, 42],
    medium: [60, 42],
    large: [44, 47],
  },
} satisfies Record<string, TableHeights>;

interface ITableLayoutOptions {
  autoHeight: () => boolean
  maxHeight: () => string | number | undefined
  showPagination: () => boolean
  rowSize: TableRowSize
  config: () => Partial<ITableLimit> | null | undefined
  noticeHeight: () => number
  getTableElement: () => Element | undefined
  onMeasuredPageSize?: (pageSize: number) => void
}

const isMaxHeightNone = (value?: string | number) =>
  typeof value === 'string' && value.trim().toLowerCase() === 'none';

/**
 * 解析纯像素高度（如 378 或 '378px'）；百分比、vh、calc 等非固定像素返回 null。
 */
export function parsePixelHeight(value?: string | number): number | null {
  if (typeof value === 'number') {
    return Number.isFinite(value) && value > 0 ? value : null;
  }
  if (typeof value !== 'string') return null;
  const match = /^(\d+(?:\.\d+)?)(px)?$/i.exec(value.trim());
  if (!match) return null;
  const parsed = Number(match[1]);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

const getHeightMetrics = (
  rowSize: TableRowSize,
  showPagination: boolean,
  config?: Partial<ITableLimit> | null,
) => {
  const mode = config?.mode ?? 'tdesign';
  const heights = mode === 'bkui' || mode === 'tdesign' ? TABLE_HEIGHTS[mode] : TABLE_HEIGHTS.other;
  const [defaultRowHeight, headerHeight] = heights[rowSize];
  const customLineHeight = config?.customLineHeight;
  const rowHeight = typeof customLineHeight === 'number' && Number.isFinite(customLineHeight) && customLineHeight > 0
    ? customLineHeight
    : defaultRowHeight;
  const hasPagination = config?.hasPagination ?? showPagination;
  // TDesign 的现有布局固定为底部分页区域预留 64px。
  const paginationHeight = hasPagination
    ? (mode === 'tdesign' ? TDESIGN_PAGINATION_HEIGHT : LEGACY_PAGINATION_HEIGHT)
    : 0;
  return {
    rowHeight,
    headerHeight,
    hasPagination,
    paginationHeight,
  };
};

const calculatePageSizeFromContentHeight = (
  contentHeight: number,
  rowSize: TableRowSize,
  showPagination: boolean,
  config?: Partial<ITableLimit> | null,
) => {
  const { rowHeight, headerHeight, hasPagination } = getHeightMetrics(rowSize, showPagination, config);
  if (!hasPagination) return DEFAULT_PAGE_SIZE;
  return Math.max(1, Math.floor((contentHeight - headerHeight) / rowHeight));
};

const isElementVisible = (element: Element | undefined): element is HTMLElement => {
  if (!(element instanceof HTMLElement) || !element.isConnected) return false;
  const rect = element.getBoundingClientRect();
  return rect.width > 0 && (rect.height > 0 || element.getClientRects().length > 0);
};

// 向上累加可滚动祖先的 scrollTop，还原未滚动时的视口顶部偏移；遇到 fixed 容器（如抽屉/弹窗）立即停止。
const getAncestorScrollTop = (element: HTMLElement) => {
  let scrollTop = 0;
  let current: HTMLElement | null = element;
  while (current && current !== document.documentElement) {
    if (getComputedStyle(current).position === 'fixed') return scrollTop;
    const parent: HTMLElement | null = current.parentElement;
    if (!parent || parent === document.documentElement) break;
    scrollTop += parent.scrollTop;
    current = parent;
  }
  return scrollTop + window.scrollY;
};

// 收集表格自身、至多两层父容器以及它们之前的同级节点，捕获上方提示条显隐/筛选栏折行引起的顶部偏移变化。
const collectLayoutWatchTargets = (element: HTMLElement) => {
  const targets = new Set<Element>([element]);
  let current: HTMLElement | null = element;
  for (let depth = 0; depth < 2 && current; depth++) {
    let prev = current.previousElementSibling;
    while (prev) {
      targets.add(prev);
      prev = prev.previousElementSibling;
    }
    const parent: HTMLElement | null = current.parentElement;
    if (!parent || parent === document.body || parent === document.documentElement) break;
    targets.add(parent);
    current = parent;
  }
  return targets;
};

/**
 * 统一管理表格自适应最大高度与首屏每页条数：
 * - 显式关闭 autoHeight 或传入 maxHeight="none" 时不做自适应，回退默认 10 条；
 * - 外部传入固定像素 maxHeight（如 378px）时沿用该高度，并按其内容区高度反推首屏条数；
 * - 外部传入 allocatedHeight 时沿用显式扣减公式；
 * - 默认基于真实 DOM 位置（getBoundingClientRect().top）动态测算剩余高度，并在窗口或上方内容变化时更新高度。
 */
export const useTableLayout = (options: ITableLayoutOptions) => {
  const viewportHeight = ref(window.innerHeight);
  const measuredContentHeight = ref<number | undefined>(undefined);
  let hasAppliedDomPageSize = false;
  let rafId = 0;

  const isAutoEnabled = computed(() => options.autoHeight() && !isMaxHeightNone(options.maxHeight()));
  const explicitMaxHeightPx = computed(() => parsePixelHeight(options.maxHeight()));
  const hasExplicitAllocatedHeight = computed(() => {
    const allocatedHeight = options.config()?.allocatedHeight;
    return typeof allocatedHeight === 'number' && Number.isFinite(allocatedHeight);
  });
  const usesDomMeasurement = computed(() =>
    isAutoEnabled.value
    && (options.maxHeight() === undefined || options.maxHeight() === '')
    && !hasExplicitAllocatedHeight.value);

  const calculateAllocatedMetrics = () => {
    const config = options.config();
    const { paginationHeight } = getHeightMetrics(options.rowSize, options.showPagination(), config);
    const allocatedHeight = hasExplicitAllocatedHeight.value
      ? config!.allocatedHeight!
      : DEFAULT_ALLOCATED_HEIGHT;
    const availableTotalHeight = viewportHeight.value - allocatedHeight - options.noticeHeight();
    const rawContentHeight = availableTotalHeight - paginationHeight;
    return {
      rawContentHeight,
      contentMaxHeight: Math.max(MIN_AUTO_CONTENT_HEIGHT, Math.floor(rawContentHeight)),
    };
  };

  const computeInitialPageSize = () => {
    if (!isAutoEnabled.value) return DEFAULT_PAGE_SIZE;
    const config = options.config();
    // 外部传入固定像素 maxHeight 时，TDesign 的 max-height 直接作用于表头+表体内容区（不含分页器）。
    if (explicitMaxHeightPx.value !== null) {
      return calculatePageSizeFromContentHeight(
        explicitMaxHeightPx.value,
        options.rowSize,
        options.showPagination(),
        config,
      );
    }
    if (hasExplicitAllocatedHeight.value) {
      const { rawContentHeight } = calculateAllocatedMetrics();
      return calculatePageSizeFromContentHeight(
        rawContentHeight,
        options.rowSize,
        options.showPagination(),
        config,
      );
    }
    if (measuredContentHeight.value !== undefined) {
      return calculatePageSizeFromContentHeight(
        measuredContentHeight.value,
        options.rowSize,
        options.showPagination(),
        config,
      );
    }
    // 挂载前 DOM 尚未就绪，先按默认占位高度估算兜底值，待挂载测得真实位置后再修正。
    const { contentMaxHeight } = calculateAllocatedMetrics();
    return calculatePageSizeFromContentHeight(
      contentMaxHeight,
      options.rowSize,
      options.showPagination(),
      config,
    );
  };

  const initialPageSize = computeInitialPageSize();

  const measureDomLayout = (allowPageSizeUpdate: boolean): number | undefined => {
    if (!usesDomMeasurement.value) return undefined;
    const element = options.getTableElement();
    if (!isElementVisible(element)) return undefined;

    const config = options.config();
    const { paginationHeight } = getHeightMetrics(options.rowSize, options.showPagination(), config);
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    const borderHeight = (parseFloat(style.borderTopWidth) || 0) + (parseFloat(style.borderBottomWidth) || 0);
    const topOffset = Math.max(0, rect.top + getAncestorScrollTop(element));
    const bottomOffset = typeof config?.bottomOffset === 'number' && Number.isFinite(config.bottomOffset)
      ? config.bottomOffset
      : DEFAULT_BOTTOM_OFFSET;
    const rawContentHeight = window.innerHeight - topOffset - bottomOffset - paginationHeight - borderHeight;
    const nextContentHeight = Math.max(MIN_AUTO_CONTENT_HEIGHT, Math.floor(rawContentHeight));

    if (measuredContentHeight.value !== nextContentHeight) {
      measuredContentHeight.value = nextContentHeight;
    }

    const nextPageSize = calculatePageSizeFromContentHeight(
      nextContentHeight,
      options.rowSize,
      options.showPagination(),
      config,
    );
    if (allowPageSizeUpdate && !hasAppliedDomPageSize) {
      hasAppliedDomPageSize = true;
      options.onMeasuredPageSize?.(nextPageSize);
    }
    return nextPageSize;
  };

  // 供首屏请求前同步补测：确保 immediate=false 且父组件提前 fetchData 时仍拿到真实自适应条数。
  const measureInitialPageSize = (): number | undefined => {
    if (!isAutoEnabled.value) return undefined;
    if (explicitMaxHeightPx.value !== null || hasExplicitAllocatedHeight.value) {
      return computeInitialPageSize();
    }
    return measureDomLayout(true);
  };

  const updateViewportAndMeasure = () => {
    viewportHeight.value = window.innerHeight;
    if (usesDomMeasurement.value) {
      // 若挂载时元素隐藏（如抽屉未展开），首次变为可见时允许同步一次首屏条数。
      measureDomLayout(!hasAppliedDomPageSize);
    }
  };

  const scheduleMeasure = () => {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(() => {
      rafId = 0;
      updateViewportAndMeasure();
    });
  };

  const resolvedMaxHeight = computed<string | number | undefined>(() => {
    const externalMaxHeight = options.maxHeight();
    if (!isAutoEnabled.value) return externalMaxHeight;
    if (externalMaxHeight !== undefined && externalMaxHeight !== '') return externalMaxHeight;
    if (hasExplicitAllocatedHeight.value) {
      return calculateAllocatedMetrics().contentMaxHeight;
    }
    return measuredContentHeight.value ?? calculateAllocatedMetrics().contentMaxHeight;
  });

  onMounted(() => {
    updateViewportAndMeasure();
    window.addEventListener('resize', scheduleMeasure);
  });

  watch(
    [options.getTableElement, usesDomMeasurement],
    ([element, enabled], _, onCleanup) => {
      if (!enabled || !(element instanceof HTMLElement)) {
        if (!enabled) measuredContentHeight.value = undefined;
        return;
      }
      measureDomLayout(!hasAppliedDomPageSize);
      if (typeof ResizeObserver === 'undefined') return;
      const observer = new ResizeObserver(scheduleMeasure);
      collectLayoutWatchTargets(element).forEach(target => observer.observe(target));
      onCleanup(() => observer.disconnect());
    },
    { flush: 'post' },
  );

  // 顶部全局公告栏异步展示或分页开关切换时，表格内容区可用高度随之更新。
  watch([options.noticeHeight, options.showPagination, options.autoHeight], scheduleMeasure, { flush: 'post' });

  onScopeDispose(() => {
    if (rafId) cancelAnimationFrame(rafId);
    window.removeEventListener('resize', scheduleMeasure);
  });

  return {
    initialPageSize,
    resolvedMaxHeight,
    measureInitialPageSize,
  };
};
