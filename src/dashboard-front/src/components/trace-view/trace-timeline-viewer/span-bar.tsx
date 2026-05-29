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
    default: 5,
  },
};

export default defineComponent({
  name: 'SpanBar',
  props: SpanBarProps,

  setup(props: any) {
    const label = ref(props.shortLabel);

    // 百分比格式化
    function toPercent(value: number): string {
      const percent = value * 100;

      if (percent >= 99 && !['inside'].includes(labelPosition.value)) return '99%';

      const decimalLen = (String(percent).split('.')[1] || '').length;
      const formatted = decimalLen > 2 ? percent.toFixed(3) : percent;

      return `${formatted}%`;
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

    // 估算文字宽度（根据 label 长度和字体大小）
    const estimateTextWidth = (text: string): number => {
      // 这里的 8 是估算的每个字符的平均像素宽度（12px 字体）
      const charWidth = 8;
      // 加上 icon 的宽度和 gap
      const iconWidth = 14;
      const gap = 4;
      return text.length * charWidth + iconWidth + gap;
    };

    // 文字放左边、右边还是线条里面
    const labelPosition = computed(() => {
      if (isFullWidth.value) return 'inside';

      const total = props.totalTraceDuration || 1;
      const startPos = viewStart.value / total;
      const endPos = viewEnd.value / total;
      const barWidth = endPos - startPos;

      // 默认放右边
      let position = 'right';
      if (endPos > 0.8 && barWidth < 0.2) {
        position = 'left';
      }

      // 计算文字放在条外时是否会超出容器, 线条区域默认是900px
      const textWidth = estimateTextWidth(label.value);
      const containerWidth = 900;
      const barPixelEnd = endPos * containerWidth;
      const barPixelStart = startPos * containerWidth;
      const barPixelWidth = barWidth * containerWidth;

      // 右边模式：文字放在条右侧，需要判断 barPixelEnd + textWidth 是否超过容器宽度
      if (position === 'right') {
        // 条块结束位置 + 文字宽度 + 间距 4px > 容器宽度，就超出了
        if (barPixelEnd + textWidth + 4 > containerWidth) {
          // 再判断：条块宽度是否足够放下文字
          if (barPixelWidth >= textWidth + 8) { // +8 是左右内边距
            return 'inside';
          }
          else {
            // 条块也放不下，只能放左边
            return 'left';
          }
        }
      }

      // 左边模式：文字放在条左侧，需要判断 barPixelStart - textWidth - 4 是否小于 0
      if (position === 'left') {
        if (barPixelStart - textWidth - 4 < 0) {
          // 条块宽度足够的话，放里面
          if (barPixelWidth >= textWidth + 8) {
            return 'inside';
          }
          else {
            // 条块也放不下，只能放右边（虽然会超出，但比被切掉好）
            return 'right';
          }
        }
      }

      return position;
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

    return {
      label,
      barStyle,
      labelPosition,
      setShortLabel,
      setLongLabel,
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
