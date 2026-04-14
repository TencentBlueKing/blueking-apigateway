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
import _has from 'lodash-es/has';
import _set from 'lodash-es/set';
import _unset from 'lodash-es/unset';

interface IDeprecation {
  currentKey: string
  formerKey: string
}

/**
 * 处理与配置相关的已弃用配置属性。
 * 注意：此操作会修改 `config`。
 *
 若发现`config`中设置了已弃用的配置属性，则会
 * 已移至新配置属性，除非存在冲突设置。如果
 * `issueWarning` 为 `true` 时，警告会在以下情况触发：
 *
 发现`config`属性上设置了已弃用的配置项
 已弃用配置属性的值已迁移到新属性
 * - 已弃用配置属性的值将被忽略，优先采用新属性的值
 */
export default function processDeprecation(
  config: Record<string, any>,
  deprecation: IDeprecation,
  issueWarning: boolean,
) {
  const { formerKey, currentKey } = deprecation;
  if (_has(config, formerKey)) {
    let isTransfered = false;
    let isIgnored = false;
    if (!_has(config, currentKey)) {
      // the new key is not set so transfer the value at the old key
      const value = _get(config, formerKey);
      _set(config, currentKey, value);
      isTransfered = true;
    }
    else {
      isIgnored = true;
    }
    _unset(config, formerKey);

    if (issueWarning) {
      const warnings = [
        `"${formerKey}" is deprecated, instead use "${currentKey}"`,
      ];
      if (isTransfered) {
        warnings.push(`The value at "${formerKey}" has been moved to "${currentKey}"`);
      }
      if (isIgnored) {
        warnings.push(`The value at "${formerKey}" is being ignored in favor of the value at "${currentKey}"`);
      }
    }
  }
}
