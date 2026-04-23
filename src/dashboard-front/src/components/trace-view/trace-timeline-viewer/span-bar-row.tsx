/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 TencentBlueKing. All rights reserved.
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

import { Divider, PopConfirm, Popover } from 'bkui-vue';
import { bkTooltips } from 'bkui-vue/lib/directives';
import {
  type ViewedBoundsFunctionType,
  createViewedBoundsFunc,
  formatDuration,
} from '@/components/trace-view/trace-timeline-viewer/utils';
import {
  useChildrenHiddenInject,
  useSpanBarCurrentInject,
} from '@/components/trace-view/hooks';
import SpanBar from '@/components/trace-view/trace-timeline-viewer/span-bar';
import SpanTreeOffset from '@/components/trace-view/trace-timeline-viewer/span-tree-offset';
import TimelineRow from '@/components/trace-view/trace-timeline-viewer/timeline-row';
import TimelineRowCell from '@/components/trace-view/trace-timeline-viewer/timeline-row-cell';
import Ticks from '@/components/trace-view/trace-timeline-viewer/ticks';
import type { ISpan } from '@/components/trace-view/typings';
import { getSpanIcon } from '@/components/trace-view/model/trace-viewer';
import { t } from '@/locales';
import type { ITraceDetail } from '@/services/source/observability';
import { useTrace } from '@/stores/useTrace';

import './span-bar-row.scss';

type KindType = 1 | 2 | 3 | 4 | 5;

const SpanBarRowProps = {
  className: {
    type: String,
    required: false,
    default: '',
  },
  color: { type: String },
  columnDivision: {
    type: Number,
    default: 0,
  },
  isChildrenExpanded: { type: Boolean },
  isDetailExpanded: { type: Boolean },
  isMatchingFilter: { type: Boolean },
  isFocusMatching: { type: Boolean },
  isActiveMatching: { type: Boolean },
  isHaveRead: { type: Boolean },
  onDetailToggled: Function as PropType<(span_id: string) => void>,
  onLoadCrossAppInfo: Function as PropType<(span: ISpan) => void>,
  numTicks: {
    type: Number,
    default: 0,
  },
  rpc: {
    type: Object,
    required: false,
    default: null,
  },
  noInstrumentedServer: {
    type: Object,
    required: false,
    default: {
      color: '',
      serviceName: '',
    },
  },
  showErrorIcon: { type: Boolean },
  span: { type: Object as PropType<ISpan> },
  focusSpan: Function as PropType<(span_id: string) => void>,
  bgColorIndex: {
    // 层级背景色索引
    type: Number,
    required: true,
  },
};

export default defineComponent({
  name: 'SpanBarRow',
  directives: { bkTooltips },
  props: SpanBarRowProps,
  emits: ['toggleCollapse'],

  setup(props: any, { emit }: any) {
    const traceStore = useTrace();
    const spanBarCurrentStore = useSpanBarCurrentInject();
    const childrenHiddenStore = useChildrenHiddenInject();

    // 激活态Row
    const activeSpan = computed(() => traceStore?.activeSpan);
    // 是否跨应用调用 span
    const crossRelationInfo = computed(() =>
      Object.keys(props.span?.cross_relation || {}).length
        ? props.span?.cross_relation
        : false,
    );
    const ellipsisDirection = computed(() => traceStore?.ellipsisDirection);
    // 是否显示耗时
    const showDuration = computed(() => traceStore?.traceViewFilters.includes('duration'));
    // 总耗时
    const totalTraceDuration = computed(() => traceStore?.traceTree?.total_latency_ms ?? 0);

    const setActiveSpan = (value: string) => {
      traceStore.setActiveSpan(value || '');
    };

    /**
     * @description 获取正确的耗时(ms)
     */
    const getSpanDuration = (span: ISpan): number => {
      if (!span) return 0;
      const duration = span.latency_ms ?? span.duration;
      return typeof duration === 'number' && !isNaN(duration) ? duration : 0;
    };

    /**
     * @description 获取正确的开始时间(ms)
     */
    const getSpanStartTime = (span: ISpan): number => {
      if (!span) return traceStore?.traceTree?.startTime || 0;
      if (span.startTime) return span.startTime;
      const offset
        = typeof span.start_offset_ms === 'number' && !isNaN(span.start_offset_ms)
          ? span.start_offset_ms
          : 0;
      return (traceStore?.traceTree?.startTime || 0) + offset;
    };

    const getViewedBounds = (): ViewedBoundsFunctionType => {
      const [zoomStart, zoomEnd] = (spanBarCurrentStore?.current.value ?? [0, 0]) as [number, number];

      return createViewedBoundsFunc({
        min: traceStore?.traceTree?.startTime || 0,
        max: traceStore?.traceTree?.endTime || 0,
        viewStart: zoomStart,
        viewEnd: zoomEnd,
      }) as ViewedBoundsFunctionType;
    };

    const detailToggle = () => {
      props.onDetailToggled?.(props.span?.span_id as string);
    };

    const childrenToggle = () => {
      childrenHiddenStore?.onChange(props.span?.span_id || '');
    };

    const handleClick = (e: MouseEvent, hasChildren: boolean) => {
      e.stopPropagation();
      if (hasChildren) {
        childrenToggle();
      }
      else {
        props.onLoadCrossAppInfo?.(props.span as ISpan);
      }
    };

    const handleToggleCollapse = (
      e: { stopPropagation: () => void },
      groupID: number,
      status: string,
    ) => {
      e?.stopPropagation();
      emit('toggleCollapse', groupID, status);
    };

    return {
      activeSpan,
      showDuration,
      crossRelationInfo,
      ellipsisDirection,
      totalTraceDuration,
      detailToggle,
      childrenToggle,
      handleClick,
      getViewedBounds,
      handleToggleCollapse,
      getSpanDuration,
      getSpanStartTime,
      setActiveSpan,
    };
  },

  render() {
    const {
      className,
      color,
      columnDivision,
      isChildrenExpanded,
      isDetailExpanded,
      isMatchingFilter,
      isFocusMatching,
      isActiveMatching,
      isHaveRead,
      numTicks,
      rpc,
      noInstrumentedServer,
      showErrorIcon,
      bgColorIndex,
      span,
    } = this.$props;

    const {
      span_id,
      hasChildren: isParent,
      operation,
      service: serviceName,
      kind,
      is_virtual: isVirtual,
      source,
      ebpf_kind: ebpfKind,
      ebpf_thread_name: ebpfThreadName = '',
      ebpf_tap_side: ebpfTapSide = '',
      ebpf_tap_port_name: ebpfTapPortName = '',
      group_info: groupInfo,
      is_expand: isExpand,
      attributes,
      depth = 0,
    } = span as Record<string, any>;

    const spanDuration = this.getSpanDuration(span as ISpan);

    const realDuration
      = groupInfo && groupInfo.id === span_id && !isExpand
        ? this.getSpanDuration(groupInfo)
        : spanDuration;
    const label = this.showDuration ? formatDuration(realDuration) : '';

    const isOddRow = (bgColorIndex as number) % 2 !== 0;

    const displayServiceName
      = source === 'ebpf'
        ? ebpfKind === 'ebpf_system'
          ? ebpfThreadName
          : ebpfTapSide
        : serviceName;

    const displayOperationName
      = source === 'ebpf'
        ? ebpfKind === 'ebpf_system'
          ? operation
          : ebpfTapPortName
        : operation;
    const labelDetail = `${displayServiceName}::${displayOperationName}`;
    let errorDescription = '';
    if (showErrorIcon) {
      const item = attributes?.find?.(
        (attr: { key: string }) => attr.key === 'span.status_message',
      );
      errorDescription = item?.value || '';
    }

    const longLabel = `${label ? `${label} | ` : ''}${labelDetail}`;

    const kindIcons: Record<KindType, string> = {
      1: 'icon-nei',
      2: 'icon-bei',
      3: 'icon-zhu',
      4: 'icon-zhu',
      5: 'icon-bei',
    };
    const isShowKindIcon = !isVirtual && source !== 'ebpf' && !!kindIcons?.[kind as KindType];
    const curClickSpan = `${span?.span_id}&${span?.service}&${span?.parent_span_id ?? ''}&${span?.layer}`;

    return (
      <TimelineRow
        className={`
          span-row
          ${className || ''}
          ${isOddRow ? 'is-odd-row' : ''}
          ${isDetailExpanded ? 'is-expanded' : ''}
          ${isFocusMatching ? 'is-focus-matching' : ''}
          ${isActiveMatching ? 'is-active-matching' : ''}
          ${isHaveRead ? 'is-have-read' : ''}
          ${isMatchingFilter ? 'is-matching-filter' : ''}
          ${curClickSpan === this.activeSpan ? 'is-active-span' : ''}
          depth-${depth}
        `}
      >
        {this.crossRelationInfo
          ? (
            <TimelineRowCell
              width={1}
              className="cursor-pointer span-view cross-app-span"
            >
              <div
                class={[
                  'span-name-wrapper',
                  {
                    'is-matching-filter': this.isMatchingFilter,
                    'is-disabled': !this.crossRelationInfo.permission,
                  },
                ]}
              >
                <SpanTreeOffset
                  childrenVisible={isChildrenExpanded}
                  showChildrenIcon={true}
                  span={span}
                  onClick={(e: MouseEvent) => this.handleClick(e, isParent)}
                />
              </div>
            </TimelineRowCell>
          )
          : (
            <>
              <TimelineRowCell
                width={columnDivision}
                className="span-name-column"
              >
                <div
                  class={`
                  span-name-wrapper
                  ${isMatchingFilter ? 'is-matching-filter' : ''}
                `}
                >
                  <SpanTreeOffset
                    childrenVisible={isChildrenExpanded}
                    span={span}
                    onClick={(e: MouseEvent) => this.handleClick(e, isParent)}
                  />
                  <div
                    style={{ borderColor: span?.color }}
                    class={`span-name ${isDetailExpanded ? 'is-detail-expanded' : ''} ${isShowKindIcon ? 'show-kind-icon' : ''}`}
                    aria-checked={isDetailExpanded}
                    role="switch"
                    tabindex={0}
                  >
                    {span?.layer && (
                      <ag-icon
                        name={getSpanIcon(span)}
                        class="service-icon"
                        color="#4d4f56"
                      />
                    )}
                    <span
                      class={[
                        'span-svc-name',
                        { 'is-children-collapsed': isParent && !isChildrenExpanded },
                        { 'is-rtl': this.ellipsisDirection === 'rtl' },
                      ]}
                    >
                      <PopConfirm
                        trigger="click"
                        v-slots={{
                          default: () => (
                            <span
                              class={isHaveRead ? 'read-service' : ''}
                              onClick={() => {
                                this.setActiveSpan(
                                  `${span?.span_id}&${span?.service}&${span?.parent_span_id ?? ''}&${span?.layer}`,
                                );
                              }}
                              v-clickOutSide={(e: MouseEvent) => {
                                e.stopPropagation();
                                if ((e?.target as HTMLElement)?.className !== 'read-service') {
                                  this.setActiveSpan('');
                                }
                              }}
                            >
                              {displayServiceName}
                            </span>
                          ),
                          content: () => {
                            const {
                              upstream = '--',
                              latency_ms,
                              service,
                              operation,
                              detail = {},
                            } = span ?? {};

                            const {
                              path,
                              status: status_code,
                              request_id,
                              method,
                              mcp_method,
                              request_body_size,
                              response_body_size,
                            } = detail as ITraceDetail;

                            return (
                              <div class="trace-detail-popover box-border min-w-700px max-w-1152px">
                                <div class="flex justify-between items-center lh-32px text-12px">
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">service:</span>
                                    <span class="color-#313238 ml-8px">{service ?? '--'}</span>
                                  </div>
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">path:</span>
                                    <span class="color-#313238 ml-8px">{path ?? '--'}</span>
                                  </div>
                                </div>

                                <div class="flex justify-between items-center lh-32px text-12px">
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">operation:</span>
                                    <span class="color-#313238 ml-8px">{operation ?? '--'}</span>
                                  </div>
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">status_code:</span>
                                    <span class="color-#313238 ml-8px">{status_code ?? '--'}</span>
                                  </div>
                                </div>

                                <div class="flex justify-between items-center lh-32px text-12px">
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">request_id:</span>
                                    <span class="color-#313238 ml-8px">{request_id ?? '--'}</span>
                                  </div>
                                  <div class="flex items-center x">
                                    <span class="color-#4d4f56">latency_ms:</span>
                                    <span class="color-#313238 ml-8px">{latency_ms ?? '--'}</span>
                                  </div>
                                </div>

                                <div class="flex justify-between items-center lh-32px text-12px">
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">upstream:</span>
                                    <span class="color-#313238 ml-8px">{upstream ?? '--'}</span>
                                  </div>
                                  <div class="flex items-center x">
                                    <span class="color-#4d4f56">request_body_size:</span>
                                    <span class="color-#313238 ml-8px">
                                      {request_body_size ? `${request_body_size} bytes` : '--'}
                                    </span>
                                  </div>
                                </div>

                                <div class="flex justify-between items-center lh-32px text-12px">
                                  <div class="flex items-center">
                                    <span class="color-#4d4f56">method:</span>
                                    <span class="color-#313238 ml-8px">{ mcp_method || method || '--'}</span>
                                  </div>
                                  <div class="flex items-center x">
                                    <span class="color-#4d4f56">response_body_size:</span>
                                    <span class="color-#313238 ml-8px">
                                      {response_body_size ? `${response_body_size} bytes` : '--'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            );
                          },
                        }}
                        placement="auto-start"
                        cancelText=""
                        popoverOptions={{
                          extCls: 'trace-viewer-popover-confirm',
                          popoverDelay: 0,
                          arrow: false,
                        }}
                      />
                      {rpc && (
                        <span>
                          {rpc.serviceName}
                        </span>
                      )}
                      {noInstrumentedServer && (
                        <span>
                          <ag-icon
                            name="arrows--right--line"
                            class="span-bar-row-arrow-icon"
                          />
                          <i
                            style={{ background: noInstrumentedServer.color }}
                            class="span-bar-row-rpc-color-marker"
                          />
                          {noInstrumentedServer.serviceName}
                        </span>
                      )}
                      <span class="endpoint-name">{displayOperationName}</span>
                      {label && (
                        <span class="endpoint-name label">
                          <Divider
                            direction="vertical"
                            type="solid"
                            color="#979ba5"
                            class="m-4px!"
                          />
                          {label}
                        </span>
                      )}
                    </span>
                    {groupInfo
                      ? (
                        <Popover
                          key={isExpand}
                          v-slots={{
                            content: () =>
                              isExpand
                                ? (
                                  <span>
                                    {t('点击折叠')}
                                    <br />
                                    {t('相同"Service + ISpan name + status"的 ISpan')}
                                  </span>
                                )
                                : (
                                  <span>
                                    {t('已折叠 {count} 个相同"Service + ISpan name + status"的 ISpan', { count: groupInfo.members.length })}
                                    <br />
                                    {t('点击展开')}
                                  </span>
                                ),
                          }}
                          placement="top"
                          popoverDelay={[500, 0]}
                        >
                          {isExpand
                            ? (
                              <i
                                class="icon-monitor icon-mc-fold-menu icon-collapsed"
                                onClick={(e: any) => this.handleToggleCollapse(e, groupInfo.id, 'collpase')}
                              />
                            )
                            : (
                              <span
                                class="collapsed-mark"
                                onClick={(e: any) => this.handleToggleCollapse(e, groupInfo.id, 'expand')}
                              >
                                {groupInfo.members.length}
                              </span>
                            )}
                        </Popover>
                      )
                      : (
                        ''
                      )}
                  </div>
                </div>
              </TimelineRowCell>
              <TimelineRowCell
                width={1 - columnDivision}
                className="cursor-pointer span-view"
              >
                <Ticks numTicks={numTicks} />
                <SpanBar
                  color={color}
                  longLabel={longLabel}
                  rpc={rpc}
                  shortLabel={label}
                  span={span}
                  numTicks={numTicks}
                  totalTraceDuration={this.totalTraceDuration}
                />
              </TimelineRowCell>
            </>
          )}
      </TimelineRow>
    );
  },
});
