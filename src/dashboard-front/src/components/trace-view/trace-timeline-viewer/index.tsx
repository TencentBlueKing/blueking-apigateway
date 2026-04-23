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

import { useTrace } from '@/stores/useTrace';
import { useChildrenHiddenProvide } from '../hooks';
import TimelineHeaderRow from './timeline-header-row';
import VirtualizedTraceView from './virtualized-trace-view';

import type { ITraceTree } from '@/components/trace-view/typings/trace';
import type { ISpan, TUpdateViewRangeTimeFunction, ViewRangeTimeUpdate } from '../typings';

interface IState {
  height: number
  resizeObserver: any
}

const DEFAULT_MIN_VALUE = 240;

const TProps = {
  updateViewRangeTime: Function as PropType<TUpdateViewRangeTimeFunction>,
  updateNextViewRangeTime: Function as PropType<(update: ViewRangeTimeUpdate) => void>,
};

const NUM_TICKS = 5;

export default defineComponent({
  name: 'TraceTimelineViewer',
  props: TProps,

  setup() {
    const traceStore = useTrace();

    const wrapperRef = ref<HTMLDivElement>();
    const virtualizedTraceViewRef = ref<InstanceType<typeof VirtualizedTraceView>>();
    const spanNameColumnWidth = ref<number>(0.25);
    const minSpanNameColumnWidth = ref<number>(0.25);
    const childrenHiddenIds = ref(new Set());

    const state = reactive<IState>({
      height: 0,
      resizeObserver: null,
    });

    const trace = computed<ITraceTree>(() => traceStore.traceTree);
    const spans = computed<ISpan[]>(() => traceStore.spanGroupTree);

    useChildrenHiddenProvide({
      childrenHiddenIds,
      onChange: (spanId: string) => childrenToggle(spanId),
    });

    const isFullscreen = inject('isFullscreen', false);

    onMounted(() => {
      resizeObserver();
      setDefaultExpandSpan();
      getSpanNameColumnWidth();
    });

    /** 默认展开三层 其他的先收起 */
    const setDefaultExpandSpan = () => {
      const childrenHiddenIDs = spans.value.reduce((res: any, s: any) => {
        if (s.depth > 1) {
          res.add(s.span_id);
        }
        return res;
      }, new Set<string>());
      childrenHiddenIds.value = childrenHiddenIDs;
    };

    const resizeObserver = () => {
      state.resizeObserver = new ResizeObserver((entries) => {
        const rect = entries?.[0]?.contentRect;
        state.height = rect.height;
        getSpanNameColumnWidth();
      });
      state.resizeObserver.observe(wrapperRef.value);
    };

    const shouldDisableCollapse = (allSpans: ISpan[], hiddenSpansIds: any) => {
      const allParentSpans = allSpans.filter(s => s.hasChildren);
      return allParentSpans.length === hiddenSpansIds.size;
    };

    const collapseAll = () => {
      if (shouldDisableCollapse(spans.value, childrenHiddenIds.value)) {
        return;
      }
      const childrenHiddenIDs = spans.value.reduce((res: any, s: any) => {
        if (s.hasChildren) {
          res.add(s.span_id);
        }
        return res;
      }, new Set<string>());
      childrenHiddenIds.value = childrenHiddenIDs;
    };

    const collapseOne = () => {
      if (shouldDisableCollapse(spans.value, childrenHiddenIds.value)) {
        return;
      }
      let nearestCollapsedAncestor: ISpan | undefined;
      const childrenHiddenIDs = spans.value.reduce((res: any, curSpan: any) => {
        if (nearestCollapsedAncestor && curSpan.depth <= nearestCollapsedAncestor.depth) {
          res.add(nearestCollapsedAncestor.span_id);
          if (curSpan.hasChildren) {
            nearestCollapsedAncestor = curSpan;
          }
        }
        else if (curSpan.hasChildren && !res.has(curSpan.span_id)) {
          nearestCollapsedAncestor = curSpan;
        }
        return res;
      }, new Set(childrenHiddenIds.value));
      // The last one
      if (nearestCollapsedAncestor) {
        childrenHiddenIDs.add(nearestCollapsedAncestor.span_id);
      }
      childrenHiddenIds.value = childrenHiddenIDs;
    };

    const expandOne = () => {
      if (childrenHiddenIds.value.size === 0) {
        return;
      }
      let prevExpandedDepth = -1;
      let expandNextHiddenSpan = true;
      const childrenHiddenIDs = spans.value.reduce((res: any, s: any) => {
        if (s.depth <= prevExpandedDepth) {
          expandNextHiddenSpan = true;
        }
        if (expandNextHiddenSpan && res.has(s.span_id)) {
          res.delete(s.span_id);
          expandNextHiddenSpan = false;
          prevExpandedDepth = s.depth;
        }
        return res;
      }, new Set(childrenHiddenIds.value));
      childrenHiddenIds.value = childrenHiddenIDs;
    };

    const expandAll = () => {
      const childrenHiddenIDs = new Set<string>();
      childrenHiddenIds.value = childrenHiddenIDs;
    };

    const setSpanNameColumnWidth = (width: number) => {
      spanNameColumnWidth.value = width;
      nextTick(() => getSpanNameColumnWidth());
    };

    const childrenToggle = (span_id: string) => {
      const childrenHiddenIDs = new Set(childrenHiddenIds.value);
      if (childrenHiddenIDs.has(span_id)) {
        childrenHiddenIds.value.delete(span_id);
      }
      else {
        childrenHiddenIds.value.add(span_id);
      }
    };

    const getSpanNameColumnWidth = () => {
      const elemWidth = wrapperRef.value?.getBoundingClientRect()?.width || 0;
      const minReact = Number((DEFAULT_MIN_VALUE / elemWidth).toFixed(2));
      minSpanNameColumnWidth.value = minReact > 0.25 ? minReact : 0.25;
      if (minReact < spanNameColumnWidth.value) return;

      spanNameColumnWidth.value = Number(minReact);
    };

    return {
      ...toRefs(state),
      wrapperRef,
      virtualizedTraceViewRef,
      spanNameColumnWidth,
      minSpanNameColumnWidth,
      isFullscreen,
      collapseAll,
      collapseOne,
      expandOne,
      expandAll,
      setSpanNameColumnWidth,
      trace,
      childrenHiddenIds,
    };
  },

  render() {
    return (
      <div
        ref="wrapperRef"
        class="relative h-full rounded-2px trace-timeline-viewer"
      >
        <TimelineHeaderRow
          columnResizeHandleHeight={this.height}
          duration={this.trace?.duration as number}
          minSpanNameColumnWidth={this.minSpanNameColumnWidth}
          nameColumnWidth={this.spanNameColumnWidth}
          numTicks={NUM_TICKS}
          onCollapseAll={this.collapseAll}
          onCollapseOne={this.collapseOne}
          onColumnWidthChange={this.setSpanNameColumnWidth}
          onExpandAll={this.expandAll}
          onExpandOne={this.expandOne}
        />
        <VirtualizedTraceView
          ref="virtualizedTraceViewRef"
          detailStates={new Map()}
          spanNameColumnWidth={this.spanNameColumnWidth}
        />
      </div>
    );
  },
});
