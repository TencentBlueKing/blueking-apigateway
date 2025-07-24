/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
<template>
  <div
    class="ring-wrapper"
    :class="extCls"
    :style="{ width: size + 'px', height: size + 'px' }"
  >
    <svg
      :height="size"
      :width="size"
      :class="[text === 'hover' ? 'show-text' : '']"
    >
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="size / 2 - strokeWidth"
        fill="none"
        :stroke="strokeColor"
        :stroke-width="strokeWidth"
        stroke-linecap="round"
      />
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="size / 2 - fillWidth"
        fill="none"
        :stroke="fillColor"
        stroke-linecap="round"
        :stroke-width="fillWidth"
        stroke-dasharray="0,10000"
      />
      <text
        :style="textStyle"
        :fill="(textStyle || {}).color"
        :class="text !== 'always' ? 'hide' : ''"
        x="50%"
        y="50%"
        dy=".3em"
        text-anchor="middle"
      >
        {{ roundDecimalNum(realPercent, 2) }}%
      </text>
    </svg>
    <slot name="text" />
  </div>
</template>

<script lang="ts" setup>
const {
  percent,
  size,
  strokeWidth,
  strokeColor,
  fillWidth,
  fillColor,
  text,
  textStyle,
} = defineProps({
  // 圆环百分比数字
  percent: {
    type: Number,
    default: 0,
  },

  // 圆环大小
  size: {
    type: Number,
    default: 100,
  },

  // 外圈宽度，外圈指 100% 的圈
  strokeWidth: {
    type: Number,
    default: 5,
  },

  strokeColor: {
    type: String,
    default: '#ebf0f5',
  },

  // 内圈宽度，内圈指根据 percent 计算的那个圈
  fillWidth: {
    type: Number,
    default: 5,
  },

  fillColor: {
    type: String,
    default: '#3a84ff',
  },

  // 显示 ring-text 的方式
  text: {
    validator(value: string) {
      return [
        'none', // 不显示 text
        'always', // 总是显示 text
        'hover', // hover 时显示 text
      ].indexOf(value) > -1;
    },

    default: 'always',
  },

  textStyle: {
    type: Object,

    default: () => {
      return {
        fontSize: '12px',
        color: '#3a84ff',
      };
    },
  },

  extCls: {
    type: String,
    default: '',
  },

  percentChangeHandler: {
    type: Function,

    default: () => {

    },
  },
});
const queue = ref([]);
const timer = ref(null);
const node = ref(null);
const circleLen = ref(0);
const realPercent = ref(percent);

/**
   * 更新圆环百分比
   *
   * @param {number} percent 百分比数字
   */
const updateProcess = (percent: number) => {
  node.value.setAttribute('stroke-dasharray', `${circleLen.value * percent / 100},10000`);
  realPercent.value = percent;
};

const roundDecimalNum = (value: number, n: number) => {
  return Math.round(value * (10 ** n)) / (10 ** n);
};

watch(() => percent, (val: number) => {
  updateProcess(val);
  queue.value.push(val);
  if (timer.value) {
    return;
  }
  while (true) {
    const curTarget = queue.value.pop();
    if (!curTarget) {
      return;
    }
    const curNum = realPercent.value;
    let change = 0;
    timer.value = setInterval(() => {
      if (parseInt(parseFloat(curNum).toFixed(0), 10) !== parseInt(parseFloat(curTarget).toFixed(0), 10)) {
        if (curNum < curTarget) {
          change += curNum;
        }
        else if (curNum > curTarget) {
          change -= curNum;
        }
        percentChangeHandler(change);
        updateProcess(change);
      }
      else {
        clearInterval(timer.value);
        timer.value = null;
      }
    }, 30);
  }
});

onMounted(() => {
  const r = size / 2 - fillWidth;
  circleLen.value = Math.floor(2 * Math.PI * r);
  [node.value] = [document.querySelectorAll('.ring-wrapper circle')[1]];
  updateProcess(percent);
});
</script>

<style scoped lang="scss">
.ring-wrapper {
    position: relative;
    display: inline-block;
    margin: 0;
    padding: 0;
    font-size: 0;

    .show-text {
      &:hover {
        text {
          display: block;
        }
      }
    }

    circle {
      -webkit-transform-origin: center;
      transform-origin: center;
      -webkit-transform: rotate(-90deg);
      transform: rotate(-90deg);
    }

    text {
      cursor: default;

      &.hide {
        display: none;
      }
    }
}
</style>
