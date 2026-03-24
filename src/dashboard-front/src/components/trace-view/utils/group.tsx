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

import type { ISpan } from '@/components/trace-view/typings';

type IToggleStatus = 'collpase' | 'expand';

/** 基于 traceTree 进行折叠分组
 * 当前节点为折叠的聚合节点 parent_span_id !== span_id
 */
export const handleTraceTreeGroup = (spans: ISpan[]) => {
  const list: ISpan[] = [];
  spans.forEach((span) => {
    if (span.parent_span_id !== span.span_id || span.is_expand) {
      list.push(span);
    }
  });

  return list;
};

/** 切换 traceTree 分组的折叠状态 */
export const handleToggleCollapse = (spans: ISpan[], groupID: string, status: IToggleStatus) => {
  let list = [];
  // 点击切换折叠状态时 只需要更改 is_expand 的值
  list = spans.map(span => ({
    ...span,
    is_expand: span.group_info?.id === groupID ? status === 'expand' : span.is_expand,
  }));

  return list;
};
