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

import { describe, expect, it } from 'vitest';
import { json2Yaml } from '@/utils/json2Yaml';
import { yaml2Json } from '@/utils/yaml2Json';

describe('utils/json2Yaml & yaml2Json', () => {
  it('正常完成 JSON 与 YAML 双向转换', () => {
    const source = {
      openapi: '3.0.1',
      info: {
        title: 'demo-api',
        version: '1.0.0',
      },
      tags: ['gateway', 'mcp'],
    };

    const dumped = json2Yaml(JSON.stringify(source));
    expect(dumped.error).toBe(false);
    expect(dumped.data).toContain('openapi: 3.0.1');

    const loaded = yaml2Json(dumped.data);
    expect(loaded.error).toBe(false);
    expect(loaded.data).toEqual(source);
  });

  it('yaml2Json 兼容 YAML 4.x 合并键 << 与紧凑的 |- 块标量', () => {
    const withMergeKey = [
      'base: &base',
      '  timeout: 30',
      '  retries: 2',
      'service:',
      '  <<: *base',
      '  retries: 5',
    ].join('\n');
    const merged = yaml2Json(withMergeKey);
    expect(merged.error).toBe(false);
    expect(merged.data).toEqual({
      base: {
        timeout: 30,
        retries: 2,
      },
      service: {
        timeout: 30,
        retries: 5,
      },
    });

    // 紧贴文本的 |- 自动补齐换行符后正常解析
    const compactBlock = 'desc: |-  hello';
    const parsed = yaml2Json(compactBlock);
    expect(parsed.error).toBe(false);
    expect(parsed.data).toEqual({ desc: 'hello' });
  });

  it('遇到非法 JSON 或非法 YAML 时返回 error: true 与空字符串', () => {
    expect(json2Yaml('{broken json')).toEqual({
      data: '',
      error: true,
    });
    expect(yaml2Json('a: [1, 2')).toEqual({
      data: '',
      error: true,
    });
  });
});
