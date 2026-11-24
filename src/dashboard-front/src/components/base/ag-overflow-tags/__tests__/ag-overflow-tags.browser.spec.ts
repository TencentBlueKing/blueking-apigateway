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

import { nextTick } from 'vue';
import { describe, expect, it } from 'vitest';
import AgOverflowTags from '@/components/base/ag-overflow-tags/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';
import { useFeatureFlag } from '@/stores/useFeatureFlag';

describe('AgOverflowTags 标签溢出折叠与多租户展示名切换', () => {
  it('空数组或单个标签时不展示 +N 溢出标记', async () => {
    const empty = await renderWithApp(AgOverflowTags, { props: { data: [] } });
    expect(empty.screen.container.querySelector('.overflow-tag')).toBeNull();

    const single = await renderWithApp(AgOverflowTags, { props: { data: ['tag-only'] } });
    expect(single.screen.container.textContent).toContain('tag-only');
    expect(single.screen.container.querySelector('.overflow-tag')).toBeNull();
  });

  it('超过 1 个标签时仅直接展示首个并聚合剩余计数为 +N', async () => {
    const { screen } = await renderWithApp(AgOverflowTags, {
      props: { data: ['alpha', 'beta', 'gamma'] },
    });

    expect(screen.container.textContent).toContain('alpha');
    expect(screen.container.querySelector('.overflow-tag')?.textContent?.trim()).toBe('+2');
    // 未开启多租户成员展示名时，不渲染自定义元素 bk-user-display-name
    expect(screen.container.querySelector('bk-user-display-name')).toBeNull();
  });

  it('同时开启 ENABLE_DISPLAY_NAME_RENDER 且 isMember=true 时渲染 bk-user-display-name 自定义元素', async () => {
    const { screen } = await renderWithApp(AgOverflowTags, {
      props: {
        data: ['alice', 'bob'],
        isMember: true,
      },
    });
    const flagStore = useFeatureFlag();
    flagStore.flags.ENABLE_DISPLAY_NAME_RENDER = true;

    await nextTick();
    const displayEl = screen.container.querySelector('bk-user-display-name');
    expect(displayEl).not.toBeNull();
    expect(displayEl?.getAttribute('user-id')).toBe('alice');
    expect(screen.container.querySelector('.overflow-tag')?.textContent?.trim()).toBe('+1');
  });
});
