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

import { type CSSProperties, getCurrentInstance } from 'vue';
import { useTrace } from '@/stores/useTrace';
import type { ISpan, TNil } from '@/components/trace-view/typings';
import { PEER_SERVICE } from '@/components/trace-view/constants/tag-keys';
import { useChildrenHiddenInject, useFocusMatchesInject, useSpanBarCurrentInject } from '@/components/trace-view/hooks';
import {
  type ViewedBoundsFunctionType,
  createViewedBoundsFunc,
  findServerChildSpan,
  isErrorSpan,
  spanContainsErredSpan,
} from '@/components/trace-view/trace-timeline-viewer/utils';
import { DEFAULT_HEIGHTS, generateRowStates } from '@/components/trace-view/trace-timeline-viewer/virtualized-trace-view';
import SpanBarRow from '@/components/trace-view/trace-timeline-viewer/span-bar-row';
import Positions from '@/components/trace-view/trace-timeline-viewer/list-view/positions';

type RowState = {
  bgColorIndex?: number
  isDetail: boolean
  span: ISpan
  spanIndex: number
};

type TWrapperProps = {
  onScroll?: () => void
  style: CSSProperties
};

const NUM_TICKS = 5;

const DEFAULT_INITIAL_DRAW = 100;

const TListViewProps = {
  activeSpanId: { type: String },
  dataLength: {
    type: Number,
    default: 0,
  },
  detailStates: { type: Object },
  haveReadSpanIds: {
    type: Array,
    default: [],
  },
  itemsWrapperClassName: {
    type: String,
    required: false,
  },
  spanNameColumnWidth: { type: Number },
  viewBuffer: {
    type: Number,
    default: 0,
  },
  viewBufferMin: {
    type: Number,
    default: 0,
  },
  windowScroller: {
    type: Boolean,
    required: false,
  },
};

export default defineComponent({
  name: 'ListView',
  props: TListViewProps,
  emits: ['itemClick', 'getCrossAppInfo', 'toggleCollapse'],

  setup(props: any, { emit }: any) {
    const route = useRoute();
    const { traceTree: trace, spanGroupTree } = useTrace();
    const spanBarCurrentStore = useSpanBarCurrentInject();
    const focusMatchesStore = useFocusMatchesInject();
    const childrenHiddenStore = useChildrenHiddenInject();

    const span_id = ref('');
    const wrapperElm = ref<HTMLElement | TNil>(null);
    const itemHolderElm = ref<HTMLElement | TNil>(null);
    const knownHeights = ref(new Map());
    const startIndexDrawn = ref(2 ** 20);
    const endIndexDrawn = ref(-(2 ** 20));
    const startIndex = ref(0);
    const endIndex = ref(0);
    const viewHeight = ref(-1);
    const scrollTop = ref(-1);
    const htmlTopOffset = ref(-1);
    const isScrolledOrResized = ref(false);
    const windowScrollListenerAdded = ref(false);
    const htmlElm = ref(document.documentElement as any);

    const yPositions = new Positions(200);
    const internalInstance = getCurrentInstance() as any;
    const forceUpdate = internalInstance?.proxy?.$forceUpdate;

    const spans = computed(() => spanGroupTree);
    const getRowStates = computed<RowState[]>(() => {
      const { detailStates } = props;
      return trace ? generateRowStates(spans.value, childrenHiddenStore?.childrenHiddenIds.value, detailStates) : [];
    });

    onMounted(() => {
      if (props.windowScroller) {
        if (wrapperElm.value) {
          const { top } = wrapperElm.value.getBoundingClientRect();
          htmlTopOffset.value = top + htmlElm.value.scrollTop;
        }
        const elem = document.querySelector('.ag-trace-chain-chart');
        elem?.addEventListener('scroll', onScroll);
        windowScrollListenerAdded.value = true;
      }

      if (itemHolderElm.value) {
        scanItemHeights();
      }
    });

    onUnmounted(() => {
      if (windowScrollListenerAdded.value) {
        window.removeEventListener('scroll', onScroll);
      }
    });

    watch(
      () => focusMatchesStore?.focusMatchesIdIndex.value,
      (val: any) => {
        if (val > -1) {
          const elem = document.querySelector('.ag-trace-chain-chart');
          elem?.scrollTo({
            top: val * 28,
            behavior: 'smooth',
          });
        }
      },
    );

    const getRowHeight = (index: number) => {
      const { span, isDetail } = getRowStates.value[index];
      if (!isDetail) {
        return DEFAULT_HEIGHTS.bar;
      }
      if (Array.isArray(span.logs) && span.logs.length) {
        return DEFAULT_HEIGHTS.detailWithLogs;
      }
      return DEFAULT_HEIGHTS.detail;
    };

    const getKeyFromIndex = (index: number) => {
      const { isDetail, span } = getRowStates.value[index];
      return `${span.span_id}--${isDetail ? 'detail' : 'bar'}`;
    };

    const getIndexFromKey = (key: string) => {
      const parts = key.split('--');
      const _spanID = parts[0];
      const _isDetail = parts[1] === 'detail';
      const max = getRowStates.value.length;
      for (let i = 0; i < max; i++) {
        const { span, isDetail } = getRowStates.value[i];
        if (span.span_id === _spanID && isDetail === _isDetail) {
          return i;
        }
      }
      return -1;
    };

    const getRowPosition = (index: number): {
      height: number
      y: number
    } =>
      yPositions.getRowPosition(index, getHeight);

    /**
     * Recalculate _startIndex and _endIndex, e.g. which items are in view.
     */
    const calcViewIndexes = () => {
      const useRoot = props.windowScroller;
      // funky if statement is to satisfy flow
      if (!useRoot) {
        /* istanbul ignore next */
        if (!wrapperElm.value) {
          viewHeight.value = -1;
          startIndex.value = 0;
          endIndex.value = 0;
          return;
        }
        viewHeight.value = wrapperElm.value.clientHeight;
        scrollTop.value = wrapperElm.value.scrollTop;
      }
      else {
        // viewHeight.value = window.innerHeight - state.htmlTopOffset;
        // scrollTop.value = window.scrollY;
        const elem = document.querySelector('.ag-trace-chain-chart');
        if (!elem) {
          return;
        }
        const rect = elem?.getBoundingClientRect();
        scrollTop.value = elem?.scrollTop as number;
        viewHeight.value = rect?.height as number;
      }
      const yStart = scrollTop.value;
      const yEnd = scrollTop.value + viewHeight.value;
      startIndex.value = yPositions.findFloorIndex(yStart, getHeight) as number;
      endIndex.value = yPositions.findFloorIndex(yEnd, getHeight) as number;
    };

    /**
     * Checked to see if the currently rendered items are sufficient, if not,
     * force an update to trigger more items to be rendered.
     */
    const positionList = () => {
      isScrolledOrResized.value = false;
      if (!wrapperElm.value) {
        return;
      }
      calcViewIndexes();
      // indexes drawn should be padded by at least props.viewBufferMin
      const maxStart = props.viewBufferMin > startIndex.value ? 0 : startIndex.value - props.viewBufferMin;
      const minEnd
        = props.viewBufferMin < props.dataLength - endIndex.value
          ? endIndex.value + props.viewBufferMin
          : props.dataLength - 1;
      if (maxStart < startIndexDrawn.value || minEnd > endIndexDrawn.value) {
        forceUpdate?.();
      }
    };

    const onScroll = () => {
      if (!isScrolledOrResized.value) {
        isScrolledOrResized.value = true;
        window.requestAnimationFrame(positionList);
      }
    };

    /**
     * Get the height of the element at index `i`; first check the known heigths,
     * fallbck to `.props.itemHeightGetter(...)`.
     */
    const getHeight = (i: number) => {
      // const key = props.getKeyFromIndex?.(i);
      const key = getKeyFromIndex?.(i);
      const known = knownHeights.value.get(key);
      // known !== known iff known is NaN

      if (known != null) {
        return known;
      }
      // return props.itemHeightGetter?.(i, key as string);
      return getRowHeight(i);
    };

    /**
     * Returns true is the view height (scroll window) or scroll position have
     * changed.
     */
    const isViewChanged = () => {
      if (!wrapperElm.value) {
        return false;
      }
      const useRoot = props.windowScroller;
      const clientHeight = useRoot ? htmlElm.value.clientHeight : wrapperElm.value.clientHeight;
      const scrollTopVal = useRoot ? htmlElm.value.scrollTop : wrapperElm.value.scrollTop;
      return clientHeight !== viewHeight.value || scrollTopVal !== scrollTop.value;
    };

    /**
     * Go through all items that are rendered and save their height based on their
     * item-key (which is on a data-* attribute). If any new or adjusted heights
     * are found, re-measure the current known y-positions (via .yPositions).
     */
    const scanItemHeights = () => {
      // const { getIndexFromKey } = props;
      if (!itemHolderElm.value) {
        return;
      }
      // note the keys for the first and last altered heights, the `yPositions`
      // needs to be updated
      let lowDirtyKey = null;
      let highDirtyKey = null;
      let isDirty = false;
      // iterating childNodes is faster than children
      // https://jsperf.com/large-htmlcollection-vs-large-nodelist
      const nodes = itemHolderElm.value.childNodes;
      const max = nodes.length;
      for (let i = 0; i < max; i++) {
        const node: HTMLElement = nodes[i] as any;
        // use `.getAttribute(...)` instead of `.dataset` for jest / JSDOM
        // const itemKey = node?.getAttribute('data-item-key');
        const itemKey = node.nextElementSibling?.getAttribute('data-item-key');
        if (!itemKey) {
          // console.warn('itemKey not found');
          continue;
        }
        // measure the first child, if it's available, otherwise the node itself
        // (likely not transferable to other contexts, and instead is specific to
        // how we have the items rendered)
        const measureSrc: Element = node.firstElementChild || node;
        const observed = measureSrc.clientHeight;
        const known = knownHeights.value.get(itemKey);
        if (observed !== known) {
          knownHeights.value.set(itemKey, observed);
          if (!isDirty) {
            isDirty = true;

            lowDirtyKey = highDirtyKey = itemKey;
          }
          else {
            highDirtyKey = itemKey;
          }
        }
      }

      if (lowDirtyKey != null && highDirtyKey != null) {
        // update yPositions, then redraw
        const imin = getIndexFromKey?.(lowDirtyKey);
        const imax = highDirtyKey === lowDirtyKey ? imin : getIndexFromKey?.(highDirtyKey);
        yPositions.calcHeights(imax as number, getHeight, imin);
        forceUpdate?.();
      }
    };

    const getClippingCssClasses = () => {
      const [zoomStart = 0, zoomEnd = 0] = (spanBarCurrentStore?.current.value ?? [0, 0]) as [number, number];

      return {
        'clipping-left': zoomStart > 0,
        'clipping-right': zoomEnd < 1,
      };
    };

    const getViewedBounds = (): ViewedBoundsFunctionType => {
      const [zoomStart, zoomEnd] = (spanBarCurrentStore?.current.value ?? [0, 0]) as [number, number];

      const viewedBoundsFunc = createViewedBoundsFunc({
        min: trace?.startTime || 0,
        max: trace?.endTime || 0,
        viewStart: zoomStart,
        viewEnd: zoomEnd,
      });

      return (start: number, end: number) => {
        const result = viewedBoundsFunc(start, end) as {
          start?: number
          end?: number
        };
        return {
          start: typeof result.start === 'number' ? result.start : 0,
          end: typeof result.end === 'number' ? result.end : 0,
        };
      };
    };

    const renderRow = (key: string, style: CSSProperties, index: number, attrs: object) => {
      const { span, spanIndex, bgColorIndex } = getRowStates.value[index];
      return renderSpanBarRow(span, spanIndex, key, style, attrs, bgColorIndex as number);
    };

    const renderSpanBarRow = (
      span: ISpan,
      spanIndex: number,
      key: string,
      style: CSSProperties,
      attrs: object,
      bgColorIndex: number,
    ) => {
      const { span_id } = span;
      const { detailStates, spanNameColumnWidth, haveReadSpanIds } = props;

      if (!trace) {
        return null;
      }

      const highlightSpanId = span_id;
      const isCollapsed = childrenHiddenStore?.childrenHiddenIds.value.has(span_id);
      const isDetailExpanded = detailStates?.has(span_id);
      const isMatchingFilter = focusMatchesStore?.findMatchesIDs.value?.has(span_id) ?? false;
      const isFocusMatching = span_id === focusMatchesStore?.focusMatchesId.value;
      const isActiveMatching = span_id === props.activeSpanId || span_id === highlightSpanId;
      const isHaveRead = haveReadSpanIds.includes(span_id);
      const showErrorIcon = isErrorSpan(span) || (isCollapsed && spanContainsErredSpan(spans.value, spanIndex));
      const attributes = {
        ...attrs,
        id: span_id,
      };

      // Check for direct child "server" span if the span is a "client" span.
      let rpc: any = null;

      const rpcSpan = findServerChildSpan(spans.value.slice(spanIndex));
      if (rpcSpan) {
        const rpcViewBounds = getViewedBounds()(
          rpcSpan.startTime ?? 0,
          (rpcSpan.startTime ?? 0) + (rpcSpan.duration ?? 0),
        );
        rpc = {
          color: rpcSpan.color,
          operation: rpcSpan.operation,
          serviceName: rpcSpan.serviceName,
          viewEnd: rpcViewBounds.end,
          viewStart: rpcViewBounds.start,
        };
      }
      const peerServiceKV = (span?.tags ?? []).find((kv: { key: string }) => kv.key === PEER_SERVICE);
      // Leaf, kind == client and has peer.service tag, is likely a client span that does a request
      // to an uninstrumented/external service
      let noInstrumentedServer: any = null;

      if (!span.hasChildren && peerServiceKV) {
        noInstrumentedServer = {
          serviceName: peerServiceKV.value,
          color: span.color,
        };
      }

      return (
        <div
          key={key}
          style={style}
          class="virtualized-trace-view-row"
          onClick={() => handleClick(span)}
          {...attributes}
        >
          <SpanBarRow
            class={getClippingCssClasses()}
            bgColorIndex={bgColorIndex}
            color={span.color}
            columnDivision={spanNameColumnWidth}
            isActiveMatching={isActiveMatching}
            isChildrenExpanded={!isCollapsed}
            isDetailExpanded={isDetailExpanded}
            isFocusMatching={isFocusMatching}
            isHaveRead={isHaveRead}
            isMatchingFilter={isMatchingFilter}
            noInstrumentedServer={noInstrumentedServer}
            numTicks={NUM_TICKS}
            rpc={rpc}
            showErrorIcon={showErrorIcon}
            span={span}
            onLoadCrossAppInfo={getCrossAppInfo}
            onToggleCollapse={(groupID: any, status: any) => emit('toggleCollapse', groupID, status)}
          />
        </div>
      );
    };

    function getCrossAppInfo(span: ISpan) {
      emit('getCrossAppInfo', span);
    }

    function handleClick(itemKey: ISpan) {
      emit('itemClick', itemKey);
    }

    return {
      yPositions,
      wrapperElm,
      itemHolderElm,
      onScroll,
      isViewChanged,
      calcViewIndexes,
      getHeight,
      getRowPosition,
      renderRow,
      startIndexDrawn,
      endIndexDrawn,
      startIndex,
      endIndex,
      getKeyFromIndex,
    };
  },

  render() {
    const { dataLength, viewBuffer, viewBufferMin } = this.$props;
    const heightGetter = this.getHeight;
    const items = [];
    let start: number;
    let end: number;

    this.yPositions.profileData(dataLength);

    if (!this.wrapperElm) {
      start = 0;
      end = (DEFAULT_INITIAL_DRAW < dataLength ? DEFAULT_INITIAL_DRAW : dataLength) - 1;
    }
    else {
      if (this.isViewChanged()) {
        this.calcViewIndexes();
      }
      const maxStart = viewBufferMin > this.startIndex ? 0 : this.startIndex - viewBufferMin;
      const minEnd = viewBufferMin < dataLength - this.endIndex ? this.endIndex + viewBufferMin : dataLength - 1;
      if (maxStart < this.startIndexDrawn || minEnd > this.endIndexDrawn) {
        start = viewBuffer > this.startIndex ? 0 : this.startIndex - viewBuffer;
        end = this.endIndex + viewBuffer;
        if (end >= dataLength) {
          end = dataLength - 1;
        }
      }
      else {
        start = this.startIndexDrawn;
        end = this.endIndexDrawn > dataLength - 1 ? dataLength - 1 : this.endIndexDrawn;
      }
    }

    this.yPositions.calcHeights(end, heightGetter, start || -1);
    this.startIndexDrawn = start;
    this.endIndexDrawn = end;

    items.length = end - start + 1;
    for (let i = start; i <= end; i++) {
      const { y: top, height } = this.yPositions.getRowPosition(i, heightGetter);
      const style = {
        height: `${height}px`,
        top: `${top}px`,
        position: 'absolute',
      };
      const itemKey = this.getKeyFromIndex?.(i);
      const attrs = { 'data-item-key': itemKey };
      items.push(this.renderRow?.(itemKey as string, style as CSSProperties, i, attrs as Record<string, string>));
    }

    const wrapperProps: TWrapperProps = { style: { position: 'relative' } };
    if (!this.$props.windowScroller) {
      wrapperProps.onScroll = this.onScroll;
      wrapperProps.style.height = '100%';
      wrapperProps.style.overflowY = 'auto';
    }
    const scrollerStyle = {
      position: 'relative' as const,
      height: `${this.yPositions.getEstimatedHeight()}px`,
    };

    return (
      <div
        ref="wrapperElm"
        {...wrapperProps}
      >
        <div style={scrollerStyle}>
          <div
            ref="itemHolderElm"
            style={{
              position: 'absolute',
              top: 0,
              margin: 0,
              padding: 0,
            }}
            class={this.itemsWrapperClassName}
          >
            {items}
          </div>
        </div>
      </div>
    );
  },
});
