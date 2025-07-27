/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

<template>
  <!--  文档详情的内容导航栏  -->
  <ul class="ag-component-nav">
    <li
      v-for="nav of list"
      :key="nav.id"
    >
      <span
        class="nav"
        :class="{ active: activeId === nav.id }"
        @click="handleAnchor(nav)"
      >
        {{ nav.name }}
      </span>
    </li>
  </ul>
</template>

<script lang="ts" setup>
import type { INavItem } from '../types.d.ts';

interface IProps { list?: INavItem[] }

const activeId = defineModel<string>({ default: '' });

const { list = [] } = defineProps<IProps>();

const handleAnchor = (nav: INavItem) => {
  const element = document.getElementById(nav.id);
  if (element) {
    activeId.value = nav.id;
    element.scrollIntoView({
      behavior: 'smooth', // 平滑滚动
      block: 'start', // 元素顶部与视口顶部对齐
    });
  }
};

// 目录变更时，默认高亮第一个目录
watch(
  () => list,
  () => {
    activeId.value = list[0]?.id || '';
  }, { deep: true });

</script>

<style lang="scss" scoped>
.ag-component-nav {
  width: 160px;
  font-size: 12px;
  line-height: 28px;
  color: #979ba5;
  text-align: left;
  border-left: 1px solid #dcdee5;

  .nav {
    display: block;
    padding-left: 16px;
    color: #63656e;
    text-decoration: none;
    cursor: pointer;

    &.active {
      margin-left: -1px;
      color: #3a84ff;
      border-left: 1px solid #3a84ff;
    }
  }
}
</style>
