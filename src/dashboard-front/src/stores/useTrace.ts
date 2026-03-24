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

import { defineStore } from 'pinia';

import { transformTraceTree } from '@/components/trace-view/model/transform-trace-data';
import { formatDuration } from '@/components/trace-view/utils/date';
import { handleToggleCollapse, handleTraceTreeGroup } from '@/components/trace-view/utils/group';
import { DEFAULT_TRACE_DATA } from '@/components/trace-view/constants/trace';
import type { ISpan } from '@/components/trace-view/typings';
import type {
  DirectionType,
  ISpanListItem,
  ITraceListItem,
  ITraceTree,
} from '@/components/trace-view/typings/trace';
import type { ITraceLog } from '@/services/source/observability';

export type IInterfaceStatisticsType = {
  selectedInterfaceStatisticsType?: []
  selectedInterfaceTypeInInterfaceStatistics?: []
  selectedSourceTypeInInterfaceStatistics?: []
};

export type IServiceStatisticsType = {
  contain: any[]
  interfaceType: any[]
};

export type ListType = 'interfaceStatistics' | 'serviceStatistics' | 'span' | 'trace' | string;

export type TraceListMode = 'origin' | 'pre_calculation';

export const useTrace = defineStore('useTrace', () => {
  const loading = ref(false);
  const traceLoading = ref(false); // trace 详情loading
  const traceData = shallowRef<ITraceLog>(DEFAULT_TRACE_DATA);
  const traceList = shallowRef<ITraceListItem[]>([]);
  const spanList = shallowRef<ISpanListItem[]>([]);
  const interfaceStatisticsList = shallowRef([]);
  const serviceStatisticsList = shallowRef([]);
  const interfaceStatisticsType = ref<any[]>([]);
  const serviceStatisticsType = ref<IServiceStatisticsType>({
    contain: [],
    interfaceType: [],
  });
  const filterTraceList = shallowRef<ITraceListItem[]>([]); // 通过左侧查询结果统计过滤的列表 为空则表示未过滤
  const filterSpanList = shallowRef<ISpanListItem[]>([]); // 作用如上
  const totalCount = ref(0);
  const traceTree = shallowRef<ITraceTree>({ spans: [] }); // 当前展示的 trace 数据
  const spanGroupTree = shallowRef<ISpan[]>([]); // 基于 traceTree 折叠展示的 span tree
  const ellipsisDirection = ref<DirectionType>('ltr'); // 省略号头部/尾部显示
  const traceViewFilters = ref<string[]>(['duration']); // 工具栏过滤 span 条件
  // Trace / ISpan list 切换标志
  const listType = ref<ListType>('trace');
  const traceType = ref([]);
  const isTraceLoading = ref(false);
  const spanType = ref([]);
  const selectedTraceViewFilterTab = ref('');
  const traceListMode = ref<TraceListMode>('pre_calculation');
  const compareTraceOriginalData = ref([]); // 对比 baseline 原始数据 用于查看 span详情原始数据
  const serviceSpanList = shallowRef<ISpan[]>([]);
  const activeSpan = ref(''); // 全局唯一的 activeSpan

  /** 更新页面 loading */
  function setPageLoading(v: boolean) {
    loading.value = v;
  }

  /** 更新 trace detail loading */
  function setTraceLoading(v: boolean) {
    traceLoading.value = v;
  }

  /** 更新当前拉取 trace 的总数 */
  function setTraceTotalCount(count: number) {
    totalCount.value = count;
  }

  /** 更新 trace 列表 */
  function setTraceList(data: ITraceListItem[]) {
    traceList.value = data?.map(item => ({
      ...item,
      trace_id: item.trace_id || '',
      duration: formatDuration(item.trace_duration, ' '),
      time: item?.time,
      entryService: item.root_service,
      entryEndpoint: item.root_span_name,
      statusCode: item.root_status_code?.value,
      status: item.root_status_code?.type,
      type: item.root_category,
    })) || [];
  }

  function setTraceType(v: never[]) {
    traceType.value = v;
  }

  function setServiceSpanList(spanList: ISpan[]) {
    serviceSpanList.value = spanList;
  }

  /** 更新 trace 过滤列表 */
  function setFilterTraceList(data: ITraceListItem[]) {
    filterTraceList.value = data;
  }

  function setFilterSpanList(data: ISpanListItem[]) {
    filterSpanList.value = data;
  }

  function setSpanList(data: ISpanListItem[]) {
    spanList.value = data;
  }

  /** 跨应用信息设置 */
  function setMcpTraceInfo(data: ITraceLog) {
    /** 合并 trace_tree */
    traceTree.value = transformTraceTree(data) as unknown as ITraceTree;
    spanGroupTree.value = handleTraceTreeGroup(traceTree.value?.spans ?? []);
  }

  function updateEllipsisDirection(val: DirectionType) {
    ellipsisDirection.value = val;
  }

  // 切换 Trace 或 ISpan 列表时，需要重置为默认状态。
  function resetTable() {
    loading.value = false;
    traceLoading.value = false;
    totalCount.value = 0;
    traceList.value = [];
    spanList.value = [];
    interfaceStatisticsList.value = [];
    serviceStatisticsList.value = [];
    traceType.value.length = 0;
    spanType.value.length = 0;
    interfaceStatisticsType.value.length = 0;
    serviceStatisticsType.value.contain.length = 0;
    serviceStatisticsType.value.interfaceType.length = 0;
  }

  const setActiveSpan = (spanKey: string) => {
    activeSpan.value = spanKey;
  };

  function setListType(v: ListType) {
    listType.value = v;
  }

  function updateTraceViewFilterTab(v: string) {
    selectedTraceViewFilterTab.value = v;
  }

  function setTraceListMode(v: TraceListMode) {
    traceListMode.value = v;
  }

  /** 切换瀑布图节点折叠状态 */
  function updateSpanGroupCollapse(groupID: any, status: any) {
    traceTree.value.spans = handleToggleCollapse(traceTree.value.spans, groupID, status);
    spanGroupTree.value = handleTraceTreeGroup(traceTree.value?.spans);
  }

  function updateCompareTraceOriginalData(list: never[]) {
    compareTraceOriginalData.value = list;
  }

  return {
    loading,
    traceLoading,
    traceData,
    traceList,
    filterTraceList,
    totalCount,
    traceTree,
    serviceSpanList,
    setServiceSpanList,
    setPageLoading,
    setTraceLoading,
    setTraceTotalCount,
    setTraceList,
    setFilterTraceList,
    setMcpTraceInfo,
    ellipsisDirection,
    updateEllipsisDirection,
    resetTable,
    traceViewFilters,
    listType,
    setListType,
    spanList,
    setSpanList,
    spanType,
    filterSpanList,
    setFilterSpanList,
    selectedTraceViewFilterTab,
    updateTraceViewFilterTab,
    interfaceStatisticsList,
    serviceStatisticsList,
    interfaceStatisticsType,
    serviceStatisticsType,
    traceListMode,
    setTraceListMode,
    spanGroupTree,
    updateSpanGroupCollapse,
    traceType,
    setTraceType,
    compareTraceOriginalData,
    updateCompareTraceOriginalData,
    isTraceLoading,
    activeSpan,
    setActiveSpan,
  };
});
