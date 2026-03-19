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

/**
 * 判断是否需要阻止点击/鼠标按下事件的传播/处理
 * @param e 鼠标事件对象（可选，兼容无事件的场景）
 * @returns 是否需要阻止事件
 */
export function stopClickOutside(e?: MouseEvent): boolean {
  // 无事件对象时直接返回false，避免类型报错
  if (!e || !e.target) return false;

  const target = e.target as Element;
  // 定义需要阻止的选择器列表（集中管理，易扩展）
  const stopSelectors = [
    '.bk-checkbox',
    '.t-checkbox',
    '.t-select-option',
    'custom-ag-table-checkbox',
    '[draggable="true"]',
  ];

  // 目标元素是否匹配指定选择器
  const matchesSelector = (selector: string): boolean => {
    // 优先用closest（支持嵌套），兼容父节点匹配
    return target.closest(selector) !== null;
  };

  // - 复选框/选择项：直接阻止
  const isCheckboxOrOption = stopSelectors.slice(0, 3).some(matchesSelector);
  // - 拖拽元素：仅click事件时阻止
  const isDraggableMousedown = e.type === 'click' && matchesSelector(stopSelectors[3]);

  return isCheckboxOrOption || isDraggableMousedown;
}
