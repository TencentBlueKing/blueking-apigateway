<template>
  <div class="ring-wrapper" :class="extCls" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :height="size" :width="size" :class="[text === 'hover' ? 'show-text' : '']">
      <circle
        :cx="size / 2" :cy="size / 2" :r="size / 2 - strokeWidth" fill="none" :stroke="strokeColor"
        :stroke-width="strokeWidth" stroke-linecap="round" />
      <circle
        :cx="size / 2" :cy="size / 2" :r="size / 2 - fillWidth" fill="none" :stroke="fillColor"
        stroke-linecap="round" :stroke-width="fillWidth" stroke-dasharray="0,10000" />
      <text
        :style="textStyle" :fill="(textStyle || {}).color" :class="text !== 'always' ? 'hide' : ''" x="50%"
        y="50%" dy=".3em" text-anchor="middle">
        {{ roundDecimalNum(realPercent, 2) }}%
      </text>
    </svg>
    <slot name="text"></slot>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue';
const props = defineProps({
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
  },
  percentChangeHandler: {
    type: Function,
    default: () => { },
  },
});
const queue = ref([]);
const timer = ref(null);
const node = ref(null);
const circleLen = ref(0);
const realPercent = ref(props.percent) as any;

//   watch: {
//     percent(val) {
//       this.updateProcess(val);
//       this.queue.push(val);
//       if (this.timer) {
//         return;
//       }
//       while (1) {
//         const curTarget = this.queue.pop();
//         if (!curTarget) {
//           return;
//         }
//         let curNum = this.realPercent;
//         let change;
//         this.timer = setInterval(() => {
//           if (parseInt(parseFloat(curNum).toFixed(0), 10) !== parseInt(parseFloat(curTarget).toFixed(0), 10)) {
//             if (curNum < curTarget) {
//               change = ++curNum;
//             } else if (curNum > curTarget) {
//               change = --curNum;
//             }
//             this.percentChangeHandler(change);
//             this.updateProcess(change);
//           } else {
//             clearInterval(this.timer);
//             this.timer = null;
//           }
//         }, 30);
//       }
//     },
//   },
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

watch(() => props.percent, (val: number) => {
  updateProcess(val);
  queue.value.push(val);
  if (timer.value) {
    return;
  }
  while (1) {
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
        } else if (curNum > curTarget) {
          change -= curNum;
        }
        props.percentChangeHandler(change);
        updateProcess(change);
      } else {
        clearInterval(timer.value);
        timer.value = null;
      }
    }, 30);
  }
});

onMounted(() => {
  const r = props.size / 2 - props.fillWidth;
  circleLen.value = Math.floor(2 * Math.PI * r);
  [node.value] = [document.querySelectorAll('.ring-wrapper circle')[1]];
  updateProcess(props.percent);
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

