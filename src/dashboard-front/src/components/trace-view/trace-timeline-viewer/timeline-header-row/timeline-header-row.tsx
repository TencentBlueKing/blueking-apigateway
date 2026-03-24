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

import { t } from '@/locales';
import { useViewRangeInject } from '../../hooks';
import Ticks from '../ticks';
import TimelineRow from '../timeline-row';
import TimelineRowCell from '../timeline-row-cell';
import VerticalResizer from '../vertical-resizer';
import TimelineCollapser from './timeline-collapser';
// import TimelineViewingLayer from './timeline-viewing-layer';
import './timeline-header-row.scss';

type TimelineHeaderRowProps = {
  columnResizeHandleHeight: number
  duration: number
  minSpanNameColumnWidth: number
  nameColumnWidth: number
  numTicks: number
  onCollapseAll: () => void
  onCollapseOne: () => void
  onColumnWidthChange: (width: number) => void
  onExpandAll: () => void
  onExpandOne: () => void
};

const TimelineHeaderRow = (props: TimelineHeaderRowProps) => {
  const {
    duration,
    nameColumnWidth,
    minSpanNameColumnWidth,
    onCollapseAll,
    onCollapseOne,
    onExpandOne,
    onExpandAll,
    numTicks,
    onColumnWidthChange,
    columnResizeHandleHeight,
  } = props;

  const viewRange = useViewRangeInject();
  const [viewStart, viewEnd] = viewRange?.viewRange.value.time.current as [number, number];

  return (
    <TimelineRow className="timeline-header-row">
      <TimelineRowCell
        width={nameColumnWidth}
        className="ub-flex ub-px2"
      >
        <h3 class="timeline-header-row-title">
          {t('服务')}
          &amp;
          {t('操作')}
        </h3>
        <TimelineCollapser
          onCollapseAll={onCollapseAll}
          onCollapseOne={onCollapseOne}
          onExpandAll={onExpandAll}
          onExpandOne={onExpandOne}
        />
      </TimelineRowCell>
      <TimelineRowCell width={1 - nameColumnWidth}>
        {/* 暂时先注释掉，后续如果需要支持动态拉伸每列宽度在开放 */}
        {/* <TimelineViewingLayer boundsInvalidator={nameColumnWidth} /> */}
        <Ticks
          endTime={viewEnd * duration}
          numTicks={numTicks}
          startTime={viewStart * duration}
          hideLine
          showLabels
        />
      </TimelineRowCell>
      <VerticalResizer
        columnResizeHandleHeight={columnResizeHandleHeight}
        max={0.85}
        min={Math.max(minSpanNameColumnWidth, 0.25)}
        position={nameColumnWidth}
        onChange={onColumnWidthChange}
      />
    </TimelineRow>
  );
};

export default TimelineHeaderRow;
