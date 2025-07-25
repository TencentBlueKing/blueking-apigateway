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

/**
 * @desc DOM 元素 offset
 * @param { DomElement } target
 * @returns { Object }
 */
export const getOffset = (target: HTMLElement) => {
  let totalLeft = 0;
  let totalTop = 0;
  let par = target.offsetParent as HTMLElement;
  totalLeft += target.offsetLeft;
  totalTop += target.offsetTop;
  while (par) {
    if (navigator.userAgent.indexOf('MSIE 8.0') === -1) {
      // 不是IE8我们才进行累加父级参照物的边框
      totalTop += par.clientTop;
      totalLeft += par.clientLeft;
    }
    totalTop += par.offsetTop;
    totalLeft += par.offsetLeft;
    par = par.offsetParent as HTMLElement;
  }
  return {
    left: totalLeft,
    top: totalTop,
  };
};

/**
 * @desc DOM 节点的 scrollParent
 * @param { DomElement } node
 * @returns { DomElement }
 */
export const getScrollParent = (node: HTMLElement): HTMLElement | null => {
  if (node === null) {
    return null;
  }

  if (node.scrollHeight > node.clientHeight) {
    return node;
  }
  return getScrollParent(node.parentNode as HTMLElement);
};

/**
 * @desc 滚动动画
 * @param { DomElement } target
 * @param { Number } destScrollTop
 */
export const scrollTopSmooth = function (target: HTMLElement, destScrollTop: number) {
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = function (cb) {
      return setTimeout(cb, 20);
    };
  }
  let { scrollTop } = target;
  const step = function () {
    const distance = destScrollTop - scrollTop;
    scrollTop = scrollTop + distance / 5;
    if (Math.abs(distance) < 1) {
      target.scrollTo(0, destScrollTop);
    }
    else {
      target.scrollTo(0, scrollTop);
      requestAnimationFrame(step);
    }
  };
  step();
};

export const getParentByClass = (node: Element, className: string) => {
  let parentNode: Element | null = node;
  while (parentNode) {
    if (parentNode.classList && parentNode.classList.contains(className)) {
      return parentNode;
    }
    parentNode = parentNode.parentNode as Element;
  }
  return parentNode;
};
