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

import type { PropType } from 'vue';
import { useTrace } from '@/stores/useTrace';
import {
  useFocusMatchesProvide,
  useSpanBarCurrentProvide,
  useViewRangeProvide,
} from '@/components/trace-view/hooks';
import TraceTimelineViewer from '@/components/trace-view/trace-timeline-viewer';
import filterSpans from '@/components/trace-view/utils/filter-spans';

import type { ITraceTree } from '@/components/trace-view/typings/trace';
import type {
  ISpan,
  IViewRange,
  TUpdateViewRangeTimeFunction,
  ViewRangeTimeUpdate,
} from '@/components/trace-view/typings';
import type { ITraceDetail } from '@/services/source/observability';

const TraceProps = { traceChainDetail: Object as PropType<ITraceDetail> };

export default defineComponent({
  name: 'TracePlugin',
  props: TraceProps,

  setup(_, { expose }) {
    const traceStore = useTrace();

    const traceTimelineViewer = ref<InstanceType<typeof TraceTimelineViewer>>();
    const focusMatchesId = ref('');
    const curFocusIndex = ref(-1);
    const focusMatchesIdIndex = ref(-1);
    const findMatchesIDs = ref(new Set());
    const viewRange = ref<IViewRange>({ time: { current: [0, 1] } });
    const current = ref<[number, number]>([0, 1]);

    /** trace 瀑布图完整数据 */
    const traceTree = computed<ITraceTree>(() => traceStore.traceTree);
    /** trace span 瀑布树 */
    const spanTree = computed<ISpan[]>(() => traceStore.spanGroupTree);

    useViewRangeProvide({
      viewRange,
      onViewRangeChange: (range: IViewRange) => {
        viewRange.value = range;
      },
    });

    useSpanBarCurrentProvide({
      current,
      onCurrentChange: (val: [number, number]) => {
        current.value = val;
      },
    });

    useFocusMatchesProvide({
      focusMatchesId,
      focusMatchesIdIndex,
      findMatchesIDs,
    });

    const nextResult = () => {
      curFocusIndex.value = curFocusIndex.value + 1;
      focusMatchSpan();
    };

    const prevResult = () => {
      curFocusIndex.value = curFocusIndex.value - 1;
      focusMatchSpan();
    };

    const isInContainer = (el: HTMLDivElement, container: HTMLDivElement) => {
      if (!el || !container) return false;

      const elRect = el.getBoundingClientRect();
      let containerRect;

      if (
        [window, document, document.documentElement, null, undefined].includes(
          container,
        )
      ) {
        containerRect = {
          top: 0,
          right: window.innerWidth,
          bottom: window.innerHeight,
          left: 0,
        };
      }
      else {
        containerRect = container.getBoundingClientRect();
      }
      return (
        elRect.top < containerRect.bottom
        && elRect.top > containerRect.top
        && elRect.bottom > containerRect.top
        && elRect.bottom < containerRect.bottom
      );
    };

    const focusMatchSpan = () => {
      nextTick(() => {
        const timelineViewer = traceTimelineViewer.value;
        if (!timelineViewer) return;

        const { expandAll, virtualizedTraceViewRef } = timelineViewer;
        expandAll?.();

        const sortResultMatches: string[] = [];
        const matchedSpanIds = Array.from(findMatchesIDs.value) || [];

        (virtualizedTraceViewRef?.getRowStates || []).forEach(
          (row: { span: ISpan }) => {
            const { span } = row;
            if (matchedSpanIds.includes(span.span_id)) {
              sortResultMatches.push(span.span_id);
            }
          },
        );

        focusMatchesId.value = sortResultMatches[curFocusIndex.value];

        const targetElem = document.querySelector(
          `[id="${focusMatchesId.value}"]`,
        ) as HTMLDivElement;
        const containerElem = document.querySelector(
          '.ag-trace-chain-chart',
        ) as HTMLDivElement;

        if (targetElem && containerElem && isInContainer(targetElem, containerElem)) {
          return;
        }

        focusMatchesIdIndex.value = (spanTree.value || []).findIndex(
          item => item.span_id === focusMatchesId.value,
        );
      });
    };

    const updateNextViewRangeTime = (update: ViewRangeTimeUpdate) => {
      const time = {
        ...viewRange.value.time,
        ...update,
      };
      viewRange.value = {
        ...viewRange.value,
        time,
      };
    };

    const updateViewRangeTime: TUpdateViewRangeTimeFunction = (
      start: number,
      end: number,
    ) => {
      const current: [number, number] = [start, end];
      const time = { current };
      viewRange.value = {
        ...viewRange.value,
        time,
      };
    };

    const trackFilter = (value: string[]) => {
      let matchedSpanIds = new Set();
      for (let index = 0; index < value.length; index++) {
        const curMatched = filterSpans(value[index], spanTree.value);
        if (!curMatched?.size) {
          matchedSpanIds = new Set();
          break;
        }
        else if (!matchedSpanIds.size) {
          matchedSpanIds = curMatched;
        }
        else {
          matchedSpanIds = new Set(
            new Set([...curMatched].filter(x => matchedSpanIds.has(x))),
          );
        }
      }
      findMatchesIDs.value = matchedSpanIds;

      if (findMatchesIDs.value.size) {
        curFocusIndex.value = 0;
        focusMatchSpan();
      }
      else {
        clearSearch();
      }
    };

    const handleClassifyFilter = (matchedSpanIds: Set<string>) => {
      findMatchesIDs.value = matchedSpanIds;

      if (findMatchesIDs.value.size) {
        curFocusIndex.value = 0;
        focusMatchSpan();
      }
      else {
        clearSearch();
      }
    };

    const clearSearch = () => {
      curFocusIndex.value = -1;
      focusMatchesId.value = '';
      focusMatchesIdIndex.value = -1;
      findMatchesIDs.value = new Set();
    };

    onMounted(() => {
      updateViewRangeTime(0, 1);
    });

    expose({
      handleClassifyFilter,
      trackFilter,
      nextResult,
      prevResult,
      clearSearch,
      findMatchesIDs,
    });

    return {
      focusMatchesId,
      curFocusIndex,
      focusMatchesIdIndex,
      viewRange,
      traceTree,
      traceTimelineViewer,
      updateViewRangeTime,
      updateNextViewRangeTime,
      trackFilter,
      nextResult,
      prevResult,
      clearSearch,
    };
  },

  render() {
    return (
      <div
        key={this.traceTree?.request_id}
        class="p-16px box-border trace-chain-view"
      >
        <div class="min-h-52px trace-page-content">
          <TraceTimelineViewer ref="traceTimelineViewer" />
        </div>
      </div>
    );
  },
});
