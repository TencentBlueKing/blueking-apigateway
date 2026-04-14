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

import _isEqual from 'lodash-es/isEqual';
import { useTrace } from '@/stores';
import { useChildrenHiddenInject } from '@/components/trace-view/hooks';
import type { ISpan, TNil, Trace } from '@/components/trace-view/typings';
import ListView from '@/components/trace-view/trace-timeline-viewer/list-view';

import './virtualized-trace-view.scss';

type RowState = {
  bgColorIndex?: number
  isDetail: boolean
  span: ISpan
  spanIndex: number
};

const VirtualizedTraceViewProps = {
  registerAccessors: Function as PropType<(accesors: any) => void>,
  setSpanNameColumnWidth: Function as PropType<(width: number) => void>,
  setTrace: Function as PropType<(trace: TNil | Trace, uiFind: string | TNil) => void>,
  focusUiFindMatches: Function as PropType<(trace: Trace, uiFind: string | TNil, allowHide?: boolean) => void>,
  shouldScrollToFirstUiFindMatch: { type: Boolean },
  uiFind: { type: String },
  detailStates: { type: Object },
  hoverIndentGuideIds: { type: Array as PropType<string[]> },
  spanNameColumnWidth: { type: Number },
  trace_id: { type: String },
  handleShowSpanDetail: Function as PropType<(span: ISpan) => void>,
};

export function generateRowStates(
  spans: ISpan[] | TNil,
  childrenHiddenIDs: Set<unknown>,
  detailStates: Record<string, any> | undefined,
): RowState[] {
  if (!spans) {
    return [];
  }

  let collapseDepth = null;
  let rowStates: RowState[] = [];
  for (let i = 0; i < spans.length; i++) {
    const span = spans[i];
    const { span_id, depth } = span;
    let hidden = false;

    if (collapseDepth != null) {
      if (depth >= collapseDepth) {
        hidden = true;
      }
      else {
        collapseDepth = null;
      }
    }
    if (hidden) {
      continue;
    }
    if (childrenHiddenIDs.has(span_id)) {
      collapseDepth = depth + 1;
    }
    rowStates.push({
      span,
      isDetail: false,
      spanIndex: i,
    });
    if (detailStates?.has(span_id)) {
      rowStates.push({
        span,
        isDetail: true,
        spanIndex: i,
      });
    }
  }
  rowStates = handleSetBgColorIndex(rowStates);

  return rowStates;
}

/** 设置背景色层级 */
function handleSetBgColorIndex(list: RowState[]) {
  let bgColorIndex = 0;
  return list.map((item: RowState, index: number) => {
    if (index) {
      const curDepth = item.span.depth;
      const prevDepth = list[index - 1]?.span.depth;
      if (curDepth !== prevDepth) {
        // 与上一层层级不同则说明为间隔新区间
        bgColorIndex += 1;
      }
    }

    return {
      ...item,
      bgColorIndex,
    };
  });
}

export const DEFAULT_HEIGHTS = {
  bar: 28,
  detail: 161,
  detailWithLogs: 197,
};

export default defineComponent({
  name: 'VirtualizedTraceView',
  props: VirtualizedTraceViewProps,

  setup(props) {
    const traceStore = useTrace();

    const virtualizedTraceViewElm = ref<HTMLElement>();
    const listViewElmRef = ref<InstanceType<typeof ListView>>();
    const spanDetail = ref<ISpan | null>(null);
    const curShowDetailSpanId = ref('');
    const showSpanDetail = ref(false);
    const activeTab = ref('BasicInfo');
    const haveReadSpanIds = ref<string[]>([]);

    const childrenHiddenStore = useChildrenHiddenInject();
    const isFullscreen = inject('isFullscreen', false);

    const traceTree = computed(() => traceStore.traceTree);
    const spans = computed(() => traceStore.spanGroupTree);
    const getRowStates = computed<RowState[]>(() => {
      const { detailStates } = props;

      return traceTree.value
        ? generateRowStates(spans.value, childrenHiddenStore?.childrenHiddenIds.value, detailStates)
        : [];
    });

    const handleEscKeydown = (e: KeyboardEvent) => {
      if (e?.code === 'Escape') {
        showSpanDetail.value = false;
      }
    };

    /** 点击span事件 */
    const handleSpanClick = (span: ISpan, isEventTab = false) => {
      curShowDetailSpanId.value = span.span_id;
      if (!haveReadSpanIds.value.includes(span.span_id)) {
        haveReadSpanIds.value.push(span.span_id);
      }
      showSpanDetail.value = true;
      spanDetail.value = span;
      activeTab.value = isEventTab ? 'Event' : 'BasicInfo';
    };

    /** 展开分组折叠的节点 */
    const handleToggleCollapse = (groupID: string, status: string) => {
      nextTick(() => traceStore.updateSpanGroupCollapse(groupID, status));
    };

    /** 点击上一跳/下一跳 */
    const handlePrevNextClicked = (flag: string) => {
      // 获取当前spanId, spanIndex
      const curSpanId = spanDetail.value?.span_id;
      const curSpanIndex = spans.value.findIndex(
        span => span.span_id === curSpanId,
      );

      if (curSpanIndex === -1) {
        return; // 找不到当前 span，直接返回
      }

      if (flag === 'next') {
        // 展开节点
        const hasChildren = spanDetail.value?.hasChildren;
        const isHidden = childrenHiddenStore?.childrenHiddenIds.value.has(curSpanId);
        if (hasChildren && isHidden) {
          childrenHiddenStore?.onChange(curSpanId || '');
        }
        spanDetail.value = spans.value[curSpanIndex + 1];
      }
      else {
        // 上一跳
        spanDetail.value = spans.value
          .slice(0, curSpanIndex)
          .reverse()
          .find(({ depth }) => {
            if (!spanDetail.value) {
              return false;
            }
            return (
              depth === spanDetail.value?.depth
              || depth === spanDetail.value?.depth - 1
            );
          }) ?? null;
      }
    };

    onMounted(() => {
      document.addEventListener('keydown', handleEscKeydown);
    });

    onUnmounted(() => {
      document.removeEventListener('keydown', handleEscKeydown);
    });

    return {
      listViewElmRef,
      virtualizedTraceViewElm,
      activeTab,
      spans,
      isFullscreen,
      showSpanDetail,
      spanDetail,
      traceTree,
      getRowStates,
      haveReadSpanIds,
      handlePrevNextClicked,
      handleSpanClick,
      handleToggleCollapse,
    };
  },

  render() {
    const { spanNameColumnWidth } = this.$props;

    return (
      <div
        ref="virtualizedTraceViewElm"
        class="virtualized-trace-view-spans"
      >
        <ListView
          ref="listViewElmRef"
          activeSpanId={this.spanDetail?.span_id}
          dataLength={this.getRowStates.length}
          detailStates={this.detailStates}
          haveReadSpanIds={this.haveReadSpanIds}
          itemsWrapperClassName="virtualized-trace-view-rows-wrapper"
          spanNameColumnWidth={spanNameColumnWidth}
          viewBuffer={300}
          viewBufferMin={100}
          windowScroller
          onItemClick={this.handleSpanClick}
          onToggleCollapse={this.handleToggleCollapse}
        />
      </div>
    );
  },
});
