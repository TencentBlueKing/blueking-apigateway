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

import _groupBy from 'lodash-es/groupBy';
import type { ISpan, ITimeTick } from '@/components/trace-view/typings';
import AgIcon from '@/components/ag-icon/Index.vue';

import './span-bar.scss';

const SpanBarProps = {
  color: { type: String },
  rpc: { type: Object },
  span: { type: Object as PropType<ISpan> },
  label: {
    type: String,
    default: '',
  },
  longLabel: {
    type: String,
    default: '',
  },
  shortLabel: {
    type: String,
    default: '',
  },
  duration: {
    type: Number,
    default: 0,
  },
  percent: {
    type: Number,
    default: 0,
  },
  totalTraceDuration: {
    type: Number,
    default: 0,
  },
  numTicks: {
    type: Number,
    default: 4,
  },
};

export default defineComponent({
  name: 'SpanBar',
  props: SpanBarProps,

  setup(props) {
    const label = ref(props.shortLabel);

    // 百分比格式化
    function toPercent(value: number): string {
      const percent = value * 100;

      if (percent >= 99 && !['inside'].includes(labelPosition.value)) return '99%';

      const decimalLen = (String(percent).split('.')[1] || '').length;
      const formatted = decimalLen > 2 ? percent.toFixed(3) : percent;

      return `${formatted}%`;
    }

    // 生成时间刻度
    function generateTimeTicks(totalDuration: number): ITimeTick[] {
      if (!totalDuration || totalDuration <= 0) return [];
      const ticks: ITimeTick[] = [];
      const step = Math.ceil(totalDuration / props.numTicks / 100) * 100;
      let current = 0;

      while (current <= totalDuration) {
        ticks.push({
          time: current,
          percent: current / totalDuration,
          label: `${current}ms`,
        });
        current += step;
      }

      if (ticks[ticks.length - 1].time !== totalDuration) {
        ticks.push({
          time: totalDuration,
          percent: 1,
          label: `${totalDuration}ms`,
        });
      }

      // 给最后一个刻度加 is-last 标记
      if (ticks.length > 0) {
        ticks[ticks.length - 1].isLast = true;
      }

      return ticks;
    }

    const setShortLabel = () => {
      label.value = props.shortLabel;
    };
    const setLongLabel = () => {
      label.value = props.longLabel;
    };

    // 计算位置
    const viewStart = computed(() => props.span?.start_offset_ms ?? 0);
    const viewEnd = computed(() => (props.span?.start_offset_ms ?? 0) + (props.span?.latency_ms ?? 0));
    const isFullWidth = computed(() => {
      const total = props.totalTraceDuration;
      return total && (props.span?.latency_ms ?? 0) >= total * 0.99;
    });

    // 文字放左边还是右边
    const labelPosition = computed(() => {
      if (isFullWidth.value) return 'inside';
      const total = props.totalTraceDuration || 1;
      const endPos = viewEnd.value / total;
      return endPos > 0.8 ? 'left' : 'right';
    });

    // 进度条样式
    const barStyle = computed(() => {
      const total = props.totalTraceDuration || 1;
      const left = isFullWidth.value ? 0 : viewStart.value / total;
      let width = isFullWidth.value ? 1 : (viewEnd.value - viewStart.value) / total;

      // 极短跨度（0.002ms）强制设置最小宽度
      const minWidthPercent = 0.002;
      if (width > 0 && width < minWidthPercent) {
        width = minWidthPercent;
      }

      return {
        backgroundColor: props.color,
        left: toPercent(left),
        width: toPercent(width),
        top: '50%',
        transform: 'translateY(-50%)',
      };
    });

    const timeTicks = computed(() => generateTimeTicks(props.totalTraceDuration));

    return {
      label,
      setShortLabel,
      setLongLabel,
      barStyle,
      labelPosition,
      timeTicks,
      toPercent,
    };
  },

  render() {
    const { span } = this.$props;
    const { is_virtual: isVirtual } = span as ISpan;

    return (
      <div
        class="span-bar-wrapper"
        onMouseout={this.setShortLabel}
        onMouseover={this.setLongLabel}
      >
        {this.timeTicks.map(tick => (
          <div
            key={tick.time}
            class={['time-tick', { 'is-last': tick.isLast }]}
            style={{ left: this.toPercent(tick.percent) }}
          />
        ))}

        <div
          style={this.barStyle}
          class={{
            'span-bar': true,
            'is-infer': isVirtual,
          }}
        >
          <span class={['span-duration', this.labelPosition]}>
            <AgIcon name="tongbu" />
            {this.label}
          </span>
        </div>
      </div>
    );
  },
});
