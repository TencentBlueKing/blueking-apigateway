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

// 仅用于类型检查：tdesign-vue-next 的类型声明从 tdesign-icons-vue-next 根入口引用了下面两项，
// 原入口会连带加载 4700+ 个图标声明文件，拖慢 vue-tsc。tsconfig.app.json 的 paths 将该模块指向此文件。
// 如需在项目中直接使用 tdesign-icons-vue-next 的图标，请在此补充对应声明。
import type { DefineComponent } from 'vue';

export type GlobalIconType = () => unknown;
export type GlobalIconConfig = Partial<Record<string, GlobalIconType>>;
export declare const CaretRightSmallIcon: DefineComponent;
