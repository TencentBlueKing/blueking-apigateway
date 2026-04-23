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

import DraggableManager, {
  type DraggableBounds,
  type DraggerStyle,
  type DraggingUpdate,
} from '../utils/draggable-manager';

import './vertical-resizer.scss';

const VerticalResizerProps = {
  max: {
    type: Number,
    default: 0,
  },
  min: {
    type: Number,
    default: 0,
  },
  onChange: Function as PropType<(newSize: number) => void>,
  position: {
    type: Number,
    default: 0,
  },
  rightSide: {
    required: false,
    type: Boolean,
  },
  columnResizeHandleHeight: { type: Number },
};

export default defineComponent({
  name: 'VerticalResizer',
  props: VerticalResizerProps,

  setup(props: any) {
    const verticalResizerRef = ref<HTMLDivElement>();
    const state = reactive<{ dragPosition: number | null }>({ dragPosition: null });

    const getDraggingBounds = (): DraggableBounds => {
      if (!verticalResizerRef.value) {
        throw new Error('invalid state');
      }
      const { left: clientXLeft, width } = verticalResizerRef.value.getBoundingClientRect();
      const { rightSide } = props;
      let { min, max } = props;
      if (rightSide) {
        [min, max] = [1 - max, 1 - min];
      }
      return {
        clientXLeft,
        width,
        maxValue: max,
        minValue: min,
      };
    };

    const handleDragUpdate = ({ value }: DraggingUpdate) => {
      const dragPosition = props.rightSide ? 1 - value : value;
      state.dragPosition = dragPosition;
    };

    const handleDragEnd = ({ manager, value }: DraggingUpdate) => {
      manager.resetBounds();
      state.dragPosition = null;
      const dragPosition = props.rightSide ? 1 - value : value;
      props.onChange?.(dragPosition);
    };

    const dragManager = new DraggableManager({
      getBounds: getDraggingBounds,
      onDragEnd: handleDragEnd,
      onDragMove: handleDragUpdate,
      onDragStart: handleDragUpdate,
    });

    onBeforeUnmount(() => {
      dragManager.dispose();
    });

    return {
      ...toRefs(state),
      verticalResizerRef,
      dragManager,
    };
  },

  render() {
    let left;
    let draggerStyle: Partial<DraggerStyle>;
    let isDraggingLeft = false;
    let isDraggingRight = false;
    const { position, rightSide, columnResizeHandleHeight } = this.$props;
    const { dragPosition } = this;
    left = `${position * 100}%`;
    const gripStyle = { left };

    if (this.dragManager.isDragging() && this.verticalResizerRef && dragPosition != null) {
      isDraggingLeft = dragPosition < position;
      isDraggingRight = dragPosition > position;
      left = `${dragPosition * 100}%`;
      const draggerLeft = `${Math.min(position, dragPosition) * 100}%`;
      const draggerRight = `calc(${(1 - Math.max(position, dragPosition)) * 100}% - 1px)`;
      draggerStyle = {
        left: draggerLeft,
        right: draggerRight,
      };
    }
    else {
      draggerStyle = gripStyle;
    }
    draggerStyle.height = `${columnResizeHandleHeight}px`;

    return (
      <div
        ref="verticalResizerRef"
        class={[
          'vertical-resizer',
          {
            isDraggingLeft,
            isDraggingRight,
            'is-flipped': rightSide,
          },
        ]}
      >
        <div
          style={gripStyle}
          class="vertical-resizer-gripIcon"
        />
        <div
          style={draggerStyle}
          class="vertical-resizer-dragger"
          aria-hidden
          onMousedown={this.dragManager.handleMouseDown}
        />
      </div>
    );
  },
});
