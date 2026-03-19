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

import { bkTooltips } from 'bkui-vue';
import { stopClickOutside } from '@/utils/stopClickOutside';

const clickOutSide = {
  mounted(el: {
    style: { display: string }
    hidden: boolean
    contains: (arg0: any) => any
    _clickOutSideHandler: (e: MouseEvent) => void
  }, binding: { value: (arg0: any) => void }) {
    const handler = (e: MouseEvent) => {
      // 先判断元素是否可见，不可见则直接返回
      if (el?.style?.display === 'none' || el?.hidden || stopClickOutside(e)) return;
      // 仅判断点击是否在当前元素外部，避免冗余逻辑
      if (!el.contains(e.target)) {
        binding.value(e);
      }
    };
    document.addEventListener('click', handler, { passive: true });
    el._clickOutSideHandler = handler;
  },
  unmounted(el: { _clickOutSideHandler: (this: Document, ev: MouseEvent) => any }) {
    document.removeEventListener('click', el._clickOutSideHandler);
  },
  updated(el: {
    _clickOutSideHandler: {
      (this: Document, ev: MouseEvent): any
      (e: MouseEvent): void
    }
    style: { display: string }
    hidden: boolean
    contains: (arg0: any) => any
  }, binding: { value: (arg0: any) => void }) {
    if (el._clickOutSideHandler) {
      document.removeEventListener('click', el._clickOutSideHandler);
    }
    const handler = (e: MouseEvent) => {
      if (el?.style?.display === 'none' || el?.hidden || stopClickOutside(e)) return;
      if (!el.contains(e.target)) {
        binding.value(e);
      }
    };
    document.addEventListener('click', handler, { passive: true });
    el._clickOutSideHandler = handler;
  },
};

const directives: Record<string, any> = {
  // 指令对象
  bkTooltips,
  // overflowTitle,
  clickOutSide,
};

export default {
  install(app: any) {
    Object.keys(directives).forEach((key) => {
      app.directive(key, directives[key]);
    });
  },
};
