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

// @ts-ignore
import { inject, provide } from 'vue';

import type { IChildrenHiddenStore, IFocusMatchesStore, ISpanBarStore, IViewRangeStore } from '../typings';

export const VIEW_RANGE = 'viewRange';
export const SPAN_BAR_CURRENT = 'spanBarCurrent';
export const FOCUS_MATCHES = 'focusMatches';
export const CHILDREN_HIDDEN = 'childrenHidden';

export const useViewRangeProvide = (viewRange: IViewRangeStore) => {
  provide(VIEW_RANGE, viewRange);
};
export const useSpanBarCurrentProvide = (currentBar: ISpanBarStore) => {
  provide(SPAN_BAR_CURRENT, currentBar);
};
export const useFocusMatchesProvide = (focusMatches: IFocusMatchesStore) => {
  provide(FOCUS_MATCHES, focusMatches);
};
export const useChildrenHiddenProvide = (childrenHidden: IChildrenHiddenStore) => {
  provide(CHILDREN_HIDDEN, childrenHidden);
};

export const useViewRangeInject = () => inject<IViewRangeStore>(VIEW_RANGE);
export const useSpanBarCurrentInject = () => inject<ISpanBarStore>(SPAN_BAR_CURRENT);
export const useFocusMatchesInject = () => inject<IFocusMatchesStore>(FOCUS_MATCHES);
export const useChildrenHiddenInject = () => inject<IChildrenHiddenStore>(CHILDREN_HIDDEN);
