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
export function useStickyBottom({
  // 底部固定距离内容区域的margin/padding
  offsetBottom = 0,
  // 固定footer节点
  footerNodeClass = '',
  // 内容区域节点
  scrollNodeClass = '',
  // 整个滚动区域的外层父节点
  parentNodeClass = '',
}: {
  offsetBottom?: number
  footerNodeClass: string
  scrollNodeClass: string
  parentNodeClass?: string
}) {
  let resizeObserver: ResizeObserver | null = null;
  // 获取按钮底部距离
  function getDistanceToBottom(el: Element) {
    const parentNode = document.querySelector(parentNodeClass);
    const clientH = parentNode?.getBoundingClientRect()?.height || 0;
    const clientRect = el?.getBoundingClientRect();
    if (clientRect) {
      return Math.max(0, clientH - clientRect.height - offsetBottom);
    }
    return 0;
  };

  // 元素滚动判断元素是否吸顶
  function controlStickyToggle() {
    const clientEl = document.querySelector(scrollNodeClass);
    const footerEl = document.querySelector(footerNodeClass);
    const footerH = footerEl?.getBoundingClientRect()?.height || 0;
    const bottomDistance = getDistanceToBottom(clientEl as Element);
    const isStickyBottom = bottomDistance > footerH ? false : true;
    // 是否吸附
    return { isStickyBottom };
  };

  function observerNodeScroll() {
    const container = document.querySelector(scrollNodeClass);
    container?.addEventListener('scroll', controlStickyToggle);

    if (resizeObserver) {
      resizeObserver.disconnect();
    }
    const parentDom = document.querySelector(parentNodeClass) as Element;
    resizeObserver = new ResizeObserver(() => {
      controlStickyToggle();
    });
    resizeObserver?.observe(parentDom);
  };

  function destroyEvent() {
    const container = document.querySelector(scrollNodeClass);
    container?.removeEventListener('scroll', controlStickyToggle);
    resizeObserver?.disconnect();
  };

  return {
    controlStickyToggle,
    observerNodeScroll,
    destroyEvent,
  };
}
