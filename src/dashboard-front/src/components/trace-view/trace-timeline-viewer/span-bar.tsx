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
import { useElementSize } from '@vueuse/core';
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
} as const;

type SpanBarPropsType = ExtractPropTypes<typeof SpanBarProps>;

export default defineComponent({
  name: 'SpanBar',
  props: SpanBarProps,

  setup(props: SpanBarPropsType) {
    const textWidthCache = new Map<string, number>();
    let canvasCtx: CanvasRenderingContext2D | null = null;

    const wrapperRef = ref<HTMLElement | null>(null);
    const label = ref(props.shortLabel);

    const { width: containerWidth } = useElementSize(wrapperRef);

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

    // 自适应不同电脑设备的字体
    const getCanvasContext = () => {
      if (!canvasCtx) {
        const canvas = document.createElement('canvas');
        canvasCtx = canvas.getContext('2d');
        if (canvasCtx) {
          const appEl = document.querySelector('.app');
          const fontMap = {
            mac: 'PingFang SC, Microsoft Yahei, Helvetica, Arial',
            win: 'Microsoft Yahei, Helvetica, Arial',
          };

          const key = appEl?.classList?.contains('win') ? 'win' : 'mac';

          canvasCtx.font = `12px ${fontMap[key]}`;
        }
      }
      return canvasCtx;
    };

    // 估算文字宽度（根据 label 长度和字体大小）
    const estimateTextWidth = (text: string): number => {
      if (textWidthCache.has(text)) {
        return textWidthCache.get(text)!;
      }

      const ctx = getCanvasContext();
      if (!ctx) {
        // 按字符粗略估算
        let width = 0;
        for (const char of text) {
          width += /[\x00-\x7F]/.test(char) ? 7 : 12;
        }
        const fallbackWidth = width + 14 + 4; // icon + gap
        textWidthCache.set(text, fallbackWidth);
        return fallbackWidth;
      }

      const metrics = ctx.measureText(text);
      const textWidth = metrics.width + 14 + 4; // icon 宽度 + gap
      textWidthCache.set(text, textWidth);
      return textWidth;
    };

    // 文字放左边、右边还是线条里面, 优先使用 longLabel
    const labelPosition = computed(() => {
      if (isFullWidth.value) return 'inside';

      const calcLabel = props.longLabel || props.label;
      const textWidth = estimateTextWidth(calcLabel);

      const total = props.totalTraceDuration || 1;
      const startPos = viewStart.value / total;
      const endPos = viewEnd.value / total;
      const barWidth = endPos - startPos;

      const currentContainerWidth = containerWidth.value || 900;
      const barPixelEnd = endPos * currentContainerWidth;
      const barPixelStart = startPos * currentContainerWidth;

      // 处理右边是否绝对放得下
      const canRight = barPixelEnd + textWidth + 4 <= currentContainerWidth;

      // 右端+窄条 → 尝试左边
      const preferLeft = endPos > 0.8 && barWidth < 0.2;

      if (preferLeft) {
        // 特殊场景：先试左，左放不下再右；右也放不下才 inside
        const canLeft = barPixelStart - textWidth - 4 >= 0;
        if (canLeft) return 'left';
        if (canRight) return 'right';
        return 'inside';
      }
      else {
        // 正常场景：【强制优先右】，右放不下才左；左也放不下才 inside
        if (canRight) return 'right';
        const canLeft = barPixelStart - textWidth - 4 >= 0;
        if (canLeft) return 'left';
        return 'inside';
      }
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

    onUnmounted(() => {
      textWidthCache.clear();
    });

    return {
      wrapperRef,
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
        ref="wrapperRef"
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
