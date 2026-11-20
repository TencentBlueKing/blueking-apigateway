/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

import assert from 'node:assert/strict';
import { test } from 'node:test';
import { computed, reactive } from 'vue';
import {
  createDiffIndex,
  filterDiffData,
  getPluginDiffClass,
  hasOnlyDocTimeDiff,
  matchesResourceKeyword,
  normalizeResource,
} from '../resource-diff.ts';
import type { IDiffData } from '@/types/resource-version';

const resource = {
  id: 1,
  name: 'get_user',
  method: 'GET',
  path: '/users/',
  proxy: {
    type: 'http',
    backend_id: 1,
    config: { path: '/backend/users/' },
  },
};

test('空差异不高亮任何字段', () => {
  assert.deepEqual([...createDiffIndex({}, null)], []);
});

test('差异字段存在即高亮，保留 false、0、空字符串和空集合', () => {
  for (const value of [false, 0, '', null, [], {}]) {
    const index = createDiffIndex({ is_public: value }, {});
    assert.equal(index.has('is_public'), true);
    assert.equal(index.has('name'), false);
  }
});

test('只高亮完整路径和父字段，避免字段前缀和插件串扰', () => {
  const index = createDiffIndex({
    description_en: '',
    plugins: { 'bk-rate-limit-extra': { config: { rate: 0 } } },
    contexts: { resource_auth: { config: { auth_verified_required: false } } },
  }, {});
  assert.equal(index.has('description'), false);
  assert.equal(index.has('plugins.bk-rate-limit'), false);
  assert.equal(index.has('plugins.bk-rate-limit-extra'), true);
  assert.equal(index.has('contexts'), true);
  assert.equal(index.has('contexts.resource_auth.config.auth_verified_required'), true);
  assert.equal(index.has('contexts.resource_auth.config.app_verified_required'), false);
});

test('列表和空对象按字段高亮，父字段可以用于分组显示', () => {
  const index = createDiffIndex({ api_labels: [1, 2],
    proxy: { config: { headers: {} } } }, {});
  assert.equal(index.has('api_labels'), true);
  assert.equal(index.has('proxy'), true);
  assert.equal(index.has('proxy.config.headers'), true);
  assert.equal(index.has('proxy.config.body'), false);
});

test('合并两侧差异后，新增或删除文档都高亮相同语言', () => {
  for (const [current, other] of [
    [{ doc_updated_time: {} }, { doc_updated_time: { zh: '2026-11-20' } }],
    [{ doc_updated_time: { zh: '2026-11-20' } }, { doc_updated_time: {} }],
  ]) {
    const index = createDiffIndex(current, other);
    assert.equal(index.has('doc_updated_time.zh'), true);
    assert.equal(index.has('doc_updated_time.en'), false);
  }
});

test('代理类型切换时合并两侧配置字段，后端 ID 为零仍是差异', () => {
  const index = createDiffIndex(
    { proxy: { type: 'http',
      backend_id: 0,
      config: { path: '/old/' } } },
    { proxy: { type: 'mock',
      config: { body: '' } } },
  );
  for (const path of ['proxy.type', 'proxy.backend_id', 'proxy.config.path', 'proxy.config.body']) {
    assert.equal(index.has(path), true);
  }
});

test('插件按后端 type 分类：两侧存在为更新，单侧存在为新增或删除', () => {
  const current = { plugins: { 'bk-rate-limit': { id: 1,
    config: {} } } };
  const empty = { plugins: {} };
  for (const isSource of [true, false]) {
    assert.equal(getPluginDiffClass('bk-rate-limit', current, current, isSource), 'item-updated');
    assert.equal(getPluginDiffClass('bk-rate-limit', current, empty, isSource),
      isSource ? 'item-deleted' : 'item-added');
    assert.equal(getPluginDiffClass('bk-rate-limit', empty, current, isSource), 'no-diff');
    assert.equal(getPluginDiffClass('bk-rate-limit-extra', current, current, isSource), 'no-diff');
  }
});

test('不变插件不会被名称有相同前缀的其他插件误高亮', () => {
  const diff = { plugins: { 'bk-rate-limit-extra': { config: { rate: 1 } } } };
  assert.equal(getPluginDiffClass('bk-rate-limit', diff, diff, false), 'no-diff');
});

test('文档过滤检查两侧字段，空差异不视为仅文档更新', () => {
  assert.equal(hasOnlyDocTimeDiff({}, null), false);
  assert.equal(hasOnlyDocTimeDiff({ doc_updated_time: {} }, { doc_updated_time: { zh: 'today' } }), true);
  assert.equal(hasOnlyDocTimeDiff({ doc_updated_time: {} }, { name: '' }), false);
});

test('关键词不区分大小写，匹配方法、前后端路径或名称', () => {
  for (const keyword of ['', 'GET', '/USERS', 'get_USER', '/BACKEND/']) {
    assert.equal(matchesResourceKeyword(resource, keyword), true);
  }
  assert.equal(matchesResourceKeyword(resource, 'missing'), false);
  assert.equal(matchesResourceKeyword({ ...resource,
    proxy: undefined }, '/backend/'), false);
  assert.equal(matchesResourceKeyword({
    ...resource,
    proxy: { ...resource.proxy,
      config: JSON.stringify(resource.proxy.config) },
  }, '/BACKEND/'), true);
});

test('资源展示支持配置对象和旧字符串配置，不修改接口数据', () => {
  const input = {
    ...resource,
    contexts: { resource_auth: { config: '{"auth_verified_required":false}' } },
    proxy: { ...resource.proxy,
      config: JSON.stringify(resource.proxy.config) },
  };
  const original = structuredClone(input);
  const data = normalizeResource(input, [{ id: 1,
    name: 'backend' }]);
  assert.equal(data.contexts.resource_auth.config.auth_verified_required, false);
  assert.equal(data.proxy.config.path, '/backend/users/');
  assert.equal(data.proxy.backend_name, 'backend');
  assert.deepEqual(input, original);
  assert.equal(normalizeResource(input, []).proxy.backend_name, '');
  assert.equal(normalizeResource(input, [{ id: 1,
    name: 'loaded later' }]).proxy.backend_name, 'loaded later');
});

test('缺少资源或历史可选字段时使用稳定的展示默认值', () => {
  for (const input of [null, resource]) {
    const data = normalizeResource(input, []);
    assert.deepEqual(data.contexts.resource_auth.config, {});
    assert.deepEqual(data.doc_updated_time, {});
    assert.deepEqual(data.plugins, []);
  }
});

test('配置对象与字符串产生相同展示结果，转换不修改嵌套配置', () => {
  const object = {
    ...resource,
    contexts: { resource_auth: { config: { auth_verified_required: false } } },
    plugins: [{ id: 10,
      name: 'rate limit',
      type: 'bk-rate-limit',
      config: { rate: 0 } }],
  };
  const string = {
    ...object,
    contexts: { resource_auth: { config: JSON.stringify(object.contexts.resource_auth.config) } },
    proxy: { ...object.proxy,
      config: JSON.stringify(object.proxy.config) },
  };
  const original = structuredClone(object);
  assert.deepEqual(normalizeResource(object, []), normalizeResource(string, []));
  assert.deepEqual(object, original);
});

test('非法历史配置不会被静默当作空配置', () => {
  assert.throws(() => normalizeResource({
    ...resource,
    proxy: { ...resource.proxy,
      config: '{' },
  }, []), SyntaxError);
});

test('响应式派生数据跟随晚到的后端列表和两侧差异更新', () => {
  const state = reactive({
    resource: { ...resource,
      diff: { is_public: false } },
    other: { doc_updated_time: { zh: '2026-11-20' } },
    backends: [] as { id: number
      name: string }[],
  });
  const display = computed(() => normalizeResource(state.resource, state.backends));
  const index = computed(() => createDiffIndex(state.resource.diff, state.other));
  assert.equal(display.value.proxy.backend_name, '');
  assert.equal(index.value.has('is_public'), true);
  assert.equal(index.value.has('doc_updated_time.zh'), true);
  state.backends.push({ id: 1,
    name: 'loaded later' });
  state.other.doc_updated_time = {};
  assert.equal(display.value.proxy.backend_name, 'loaded later');
  assert.equal(index.value.has('doc_updated_time.zh'), false);
});

test('筛选统一处理两侧关键词、差异类型和仅文档更新，保留展开状态', () => {
  const updated = {
    source: { ...resource,
      name: 'old_name',
      diff: { name: 'old_name' } },
    target: { ...resource,
      name: 'new_name',
      diff: { name: 'new_name' } },
    isExpanded: true,
  };
  const docOnly = {
    source: { ...resource,
      diff: { doc_updated_time: {} } },
    target: { ...resource,
      diff: { doc_updated_time: { zh: '2026-11-20' } } },
    isExpanded: false,
  };
  const data: IDiffData = {
    add: [{ ...resource,
      isExpanded: false }],
    delete: [{ ...resource,
      isExpanded: true }],
    update: [updated, docOnly],
  };
  const original = structuredClone(data);
  const filters = { keyword: '',
    diffType: '',
    hideOnlyDiffInDocUpdatedTime: false };
  assert.deepEqual(filterDiffData(data, filters), data);
  for (const keyword of ['old_name', 'NEW_NAME']) {
    const result = filterDiffData(data, { ...filters,
      keyword });
    assert.deepEqual(result, { add: [],
      delete: [],
      update: [updated] });
    assert.equal(result.update[0], updated);
  }
  const withoutDocOnly = filterDiffData(data, { ...filters,
    hideOnlyDiffInDocUpdatedTime: true });
  assert.deepEqual(withoutDocOnly, { ...data,
    update: [updated] });
  for (const diffType of ['add', 'delete', 'update'] as const) {
    const filtered = filterDiffData(data, { ...filters,
      diffType });
    for (const type of ['add', 'delete', 'update'] as const) {
      assert.deepEqual(filtered[type], type === diffType ? data[type] : []);
    }
  }
  assert.deepEqual(filterDiffData(data, { ...filters,
    keyword: 'missing' }), { add: [],
    delete: [],
    update: [] });
  assert.deepEqual(data, original);
});
