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

/**
 * Drop <style> tags and their bodies. The package whitelist keeps the tag,
 * so global rules and @import would otherwise survive filtering.
 */
export function rejectStyleTag(
  tag: string,
  _html: string,
  options: { isWhite?: boolean },
): void {
  if (tag === 'style') {
    options.isWhite = false;
  }
}

export const xssFilterDefaultOptions = {
  stripIgnoreTagBody: ['style'],
  onTag: rejectStyleTag,
};
