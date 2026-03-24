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

import _get from 'lodash-es/get';

import EUpdateTypes from './e-update-types';

import type { TNil } from '@/components/trace-view/typings';
import type { DraggableBounds, DraggingUpdate } from '@/components/trace-view/utils/draggable-manager/types';

const LEFT_MOUSE_BUTTON = 0;

type DraggableManagerOptions = {
  getBounds: (tag: string | TNil) => DraggableBounds
  onDragEnd?: (update: DraggingUpdate) => void
  onDragMove?: (update: DraggingUpdate) => void
  onDragStart?: (update: DraggingUpdate) => void
  onMouseEnter?: (update: DraggingUpdate) => void
  onMouseLeave?: (update: DraggingUpdate) => void
  onMouseMove?: (update: DraggingUpdate) => void
  resetBoundsOnResize?: boolean
  tag?: string
};

export default class DraggableManager {
  constructor({ getBounds, tag, resetBoundsOnResize = true, ...rest }: DraggableManagerOptions) {
    /** @type {DraggableBounds | TNil} */
    this._bounds = undefined;
    this._isDragging = false;

    // 绑定回调
    this._onMouseEnter = rest.onMouseEnter;
    this._onMouseLeave = rest.onMouseLeave;
    this._onMouseMove = rest.onMouseMove;
    this._onDragStart = rest.onDragStart;
    this._onDragMove = rest.onDragMove;
    this._onDragEnd = rest.onDragEnd;

    this.getBounds = getBounds;
    this.tag = tag;
    this._resetBoundsOnResize = Boolean(resetBoundsOnResize);

    // 绑定 DOM 事件处理器
    this.handleMouseDown = this._handleDragEvent;
    this.handleMouseEnter = this._handleMinorMouseEvent;
    this.handleMouseMove = this._handleMinorMouseEvent;
    this.handleMouseLeave = this._handleMinorMouseEvent;

    if (this._resetBoundsOnResize) {
      window.addEventListener('resize', this.resetBounds);
    }
  }

  // 类属性（方法/值）直接在这里定义，不需要提前声明类型
  _bounds: DraggableBounds | TNil = undefined; // 或者直接在 constructor 赋值
  _isDragging: boolean = false;
  _onMouseEnter: ((update: DraggingUpdate) => void) | TNil = undefined;
  _onMouseLeave: ((update: DraggingUpdate) => void) | TNil = undefined;
  _onMouseMove: ((update: DraggingUpdate) => void) | TNil = undefined;
  _onDragStart: ((update: DraggingUpdate) => void) | TNil = undefined;
  _onDragMove: ((update: DraggingUpdate) => void) | TNil = undefined;
  _onDragEnd: ((update: DraggingUpdate) => void) | TNil = undefined;
  _resetBoundsOnResize: boolean = true;

  getBounds: (tag: string | TNil) => DraggableBounds;
  tag: string | TNil = undefined;

  handleMouseEnter: (event: MouseEvent) => void;
  handleMouseMove: (event: MouseEvent) => void;
  handleMouseLeave: (event: MouseEvent) => void;
  handleMouseDown: (event: MouseEvent) => void;

  _getBounds(): DraggableBounds {
    if (!this._bounds) {
      this._bounds = this.getBounds(this.tag);
    }
    return this._bounds;
  }

  _getPosition(clientX: number) {
    const { clientXLeft, maxValue, minValue, width } = this._getBounds();
    let x = clientX - clientXLeft;
    let value = x / width;
    if (minValue != null && value < minValue) {
      value = minValue;
      x = minValue * width;
    }
    else if (maxValue != null && value > maxValue) {
      value = maxValue;
      x = maxValue * width;
    }
    return {
      value,
      x,
    };
  }

  _stopDragging() {
    window.removeEventListener('mousemove', this._handleDragEvent);
    window.removeEventListener('mouseup', this._handleDragEvent);
    const style = _get(document, 'body.style');
    if (style) {
      style.userSelect = '';
    }
    this._isDragging = false;
  }

  isDragging() {
    return this._isDragging;
  }

  dispose() {
    if (this._isDragging) {
      this._stopDragging();
    }
    if (this._resetBoundsOnResize) {
      window.removeEventListener('resize', this.resetBounds);
    }
    this._bounds = undefined;
    this._onMouseEnter = undefined;
    this._onMouseLeave = undefined;
    this._onMouseMove = undefined;
    this._onDragStart = undefined;
    this._onDragMove = undefined;
    this._onDragEnd = undefined;
  }

  resetBounds = () => {
    this._bounds = undefined;
  };

  _handleMinorMouseEvent = (event: MouseEvent) => {
    const { button, clientX, type: eventType } = event;
    if (this._isDragging || button !== LEFT_MOUSE_BUTTON) {
      return;
    }
    let type: EUpdateTypes | null = null;
    let handler: ((update: DraggingUpdate) => void) | TNil;
    if (eventType === 'mouseenter') {
      type = EUpdateTypes.MouseEnter;
      handler = this._onMouseEnter;
    }
    else if (eventType === 'mouseleave') {
      type = EUpdateTypes.MouseLeave;
      handler = this._onMouseLeave;
    }
    else if (eventType === 'mousemove') {
      type = EUpdateTypes.MouseMove;
      handler = this._onMouseMove;
    }
    else {
      throw new Error(`invalid event type: ${eventType}`);
    }
    if (!handler) {
      return;
    }
    const { value, x } = this._getPosition(clientX);
    handler({
      event,
      type,
      value,
      x,
      manager: this,
      tag: this.tag,
    });
  };

  _handleDragEvent = (event: MouseEvent) => {
    const { button, clientX, type: eventType } = event;
    let type: EUpdateTypes | null = null;
    let handler: ((update: DraggingUpdate) => void) | TNil;
    if (eventType === 'mousedown') {
      if (this._isDragging || button !== LEFT_MOUSE_BUTTON) {
        return;
      }
      window.addEventListener('mousemove', this._handleDragEvent);
      window.addEventListener('mouseup', this._handleDragEvent);
      const style = _get(document, 'body.style');
      if (style) {
        style.userSelect = 'none';
      }
      this._isDragging = true;

      type = EUpdateTypes.DragStart;
      handler = this._onDragStart;
    }
    else if (eventType === 'mousemove') {
      if (!this._isDragging) {
        return;
      }
      type = EUpdateTypes.DragMove;
      handler = this._onDragMove;
    }
    else if (eventType === 'mouseup') {
      if (!this._isDragging) {
        return;
      }
      this._stopDragging();
      type = EUpdateTypes.DragEnd;
      handler = this._onDragEnd;
    }
    else {
      throw new Error(`invalid event type: ${eventType}`);
    }
    if (!handler) {
      return;
    }
    const { value, x } = this._getPosition(clientX);
    handler({
      event,
      type,
      value,
      x,
      manager: this,
      tag: this.tag,
    });
  };
}
