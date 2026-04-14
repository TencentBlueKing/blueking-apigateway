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
import type { ISpan } from '@/components/trace-view/typings';
import AgIcon from '@/components/ag-icon/Index.vue';

import './span-bar.scss';

const SpanBarProps = {
  color: { type: String },
  hintSide: { type: String },
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
  level: {
    type: Number,
    default: 0,
  },
  totalTraceDuration: {
    type: Number,
    default: 0,
  },
  containerWidth: {
    type: Number,
    default: 1000,
  },
};

// 百分比计算
function toPercent(value: number) {
  const percent = (value * 100).toFixed(2);
  return +percent < 0.5 ? '16px' : `${percent}%`;
}

// 生成时间刻度线配置（适配蓝鲸设计风格）
function generateTimeTicks(totalDuration: number) {
  if (!totalDuration || totalDuration <= 0) return [];

  const ticks = [];
  // 自动生成4个左右刻度，间隔为100的倍数，和截图0ms/373ms/746ms/1119ms/1493ms对齐
  const step = Math.ceil(totalDuration / 4 / 100) * 100;
  let current = 0;

  while (current <= totalDuration) {
    ticks.push({
      time: current,
      percent: current / totalDuration,
      label: `${current}ms`,
    });
    current += step;
  }

  // 强制添加总耗时刻度，确保最后一个刻度精准对齐
  if (ticks[ticks.length - 1].time !== totalDuration) {
    ticks.push({
      time: totalDuration,
      percent: 1,
      label: `${totalDuration}ms`,
    });
  }

  return ticks;
}

export default defineComponent({
  name: 'SpanBar',
  props: SpanBarProps,

  setup(props) {
    const label = ref(props.shortLabel);

    const setShortLabel = () => {
      label.value = props.shortLabel;
    };

    const setLongLabel = () => {
      label.value = props.longLabel;
    };

    // 从 span 真实字段计算开始 / 结束位置
    const viewStart = computed(() => {
      return props.span?.start_offset_ms ?? 0;
    });

    const viewEnd = computed(() => {
      const start = props.span?.start_offset_ms ?? 0;
      const dur = props.span?.latency_ms ?? 0;
      return start + dur;
    });

    // 判断是否铺满整个 trace（耗时 ≈ 总耗时）
    const isFullWidth = computed(() => {
      const total = props.totalTraceDuration;
      if (!total) return false;
      const dur = props.span?.latency_ms ?? 0;
      // 当前耗时 ≥ 总耗时的 99% → 判定铺满
      return dur >= total * 0.99;
    });

    // 铺满 → 直接沾满 100% 宽度
    // 没铺满 → 正常计算
    const barStyle = computed(() => {
      const total = props.totalTraceDuration || 1;
      const startMs = viewStart.value;
      const endMs = viewEnd.value;

      let left = 0;
      let width = 0;

      if (isFullWidth.value) {
        left = 0;
        width = 1; // 沾满 100%
      }
      else {
        left = startMs / total;
        width = (endMs - startMs) / total;
      }

      return {
        backgroundColor: props.color,
        left: toPercent(left),
        width: toPercent(width),
        top: '50%',
        transform: 'translateY(-50%)',
      };
    });

    // 铺满 → 文字必须放内部
    const isLabelInside = computed(() => {
      return isFullWidth.value;
    });

    // 时间刻度线列表
    const timeTicks = computed(() => {
      return generateTimeTicks(props.totalTraceDuration);
    });

    return {
      label,
      setShortLabel,
      setLongLabel,
      barStyle,
      isLabelInside,
      timeTicks,
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
        {/* 时间刻度 + 垂直时间线 */}
        {this.timeTicks.map(tick => (
          <div
            key={tick.time}
            class="time-tick"
            style={{ left: toPercent(tick.percent) }}
          />
        ))}

        {/* 原有 span 条 */}
        <div
          style={this.barStyle}
          class={{
            'span-bar': true,
            'is-infer': isVirtual,
          }}
        >
          <span class={['span-duration', this.isLabelInside ? 'inside' : '']}>
            <AgIcon name="tongbu" />
            {this.label}
          </span>
        </div>
      </div>
    );
  },
});
