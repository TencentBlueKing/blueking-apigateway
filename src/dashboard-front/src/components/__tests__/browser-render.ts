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

import { type Component, type Plugin } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import {
  Button,
  Dropdown,
  Exception,
  Form,
  Input,
  Popover,
  Radio,
  Select,
  Sideslider,
  Tag,
} from 'bkui-vue';
import 'bkui-vue/dist/style.css';
import { BkXssFilterDirective } from '@blueking/xss-filter';
import { render } from 'vitest-browser-vue';
import AgCopyButton from '@/components/base/ag-copy-button/Index.vue';
import AgIcon from '@/components/base/ag-icon/Index.vue';
import AgIconButton from '@/components/base/ag-icon-button/Index.vue';
import directive from '@/directives';
import i18n from '@/locales';

// 按需注册浏览器组件测试用到的 bkui-vue 组件，避免全量安装产生重复注册告警；
// 后续测试依赖未包含的组件时，可补充到此处或通过 options.global.components 局部传入
const BKUI_COMPONENTS = {
  BkButton: Button,
  BkDropdown: Dropdown,
  BkDropdownItem: Dropdown.DropdownItem,
  BkDropdownMenu: Dropdown.DropdownMenu,
  BkException: Exception,
  BkForm: Form,
  BkFormItem: Form.FormItem,
  BkInput: Input,
  BkOption: Select.Option,
  BkPopover: Popover,
  BkRadio: Radio,
  BkRadioGroup: Radio.Group,
  BkSelect: Select,
  BkSideslider: Sideslider,
  BkTag: Tag,
};

/**
 * 在真实 Chromium 环境中挂载业务/基础组件，
 * 装配 Pinia、按需 bkui-vue 组件、i18n、XSS 过滤与全局基础组件。
 */
export async function renderWithApp<T extends Component>(
  component: T,
  options: Record<string, any> = {},
) {
  const pinia = createPinia();
  setActivePinia(pinia);

  const extraPlugins = (options.global?.plugins ?? []) as Plugin[];
  const extraComponents = options.global?.components ?? {};

  const screen = await render(component as any, {
    ...options,
    global: {
      ...options.global,
      plugins: [
        pinia,
        i18n,
        BkXssFilterDirective,
        directive,
        ...extraPlugins,
      ],
      components: {
        ...BKUI_COMPONENTS,
        AgIcon,
        AgIconButton,
        AgCopyButton,
        ...extraComponents,
      },
    },
  });

  return {
    pinia,
    screen,
  };
}
