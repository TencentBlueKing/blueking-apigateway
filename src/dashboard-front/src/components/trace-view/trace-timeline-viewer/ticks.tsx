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

import { formatDuration } from '@/components/trace-view/utils/date';

import type { TNil } from '@/components/trace-view/typings';

import './ticks.scss';

type TicksProps = {
  endTime?: number | TNil
  hideLine?: boolean
  numTicks: number
  showLabels?: boolean | TNil
  startTime?: number | TNil
};

const Ticks = (props: TicksProps) => {
  const { endTime, numTicks, showLabels, startTime, hideLine } = props;

  let labels: string[] | undefined;
  if (showLabels) {
    labels = [];
    const viewingDuration = (endTime || 0) - (startTime || 0);
    for (let i = 0; i < numTicks; i++) {
      const durationAtTick = (startTime || 0) + (i / (numTicks - 1)) * viewingDuration;
      labels.push(formatDuration(durationAtTick, ' ', 3));
    }
  }
  const ticks = [];
  for (let i = 0; i < numTicks; i++) {
    const portion = i / (numTicks - 1);
    ticks.push(
      <div
        key={portion}
        style={{
          'left': `${portion * 100}%`,
          'background-color': hideLine ? '' : '#dcdee5',
        }}
        class="ticks-tick"
      >
        {labels && (
          <span class={`ticks-tickLabel ${portion >= 1 ? 'isEndAnchor' : ''} ${hideLine ? 'hide-line-label' : ''}`}>
            {labels[i]}
          </span>
        )}
      </div>,
    );
  }
  return <div class="ticks">{ticks}</div>;
};

Ticks.defaultProps = {
  endTime: null,
  showLabels: null,
  startTime: null,
};

export default Ticks;
