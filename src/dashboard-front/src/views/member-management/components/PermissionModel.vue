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

<template>
  <table class="permission-matrix">
    <thead>
      <tr>
        <th>{{ t('操作') }}</th>
        <th
          v-for="role in MEMBER_ROLES"
          :key="role"
          :class="{ 'is-active': highlightRole === role }"
          @click="highlightRole = role"
        >
          {{ getRoleLabel(role) }}
        </th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="item in visibleItems"
        :key="item.key"
      >
        <td>
          <span
            v-bk-tooltips="{
              content: item.tip || '',
              disabled: !item.tip,
              placement: 'top',
            }"
            :class="{ 'has-tip': item.tip }"
          >
            {{ item.label }}
          </span>
        </td>
        <td
          v-for="role in MEMBER_ROLES"
          :key="role"
          :class="{ 'is-active': highlightRole === role }"
        >
          <span
            class="perm-icon"
            :class="[
              item[role] ? 'is-allow' : 'is-deny',
              { 'is-muted': highlightRole && highlightRole !== role },
            ]"
          >
            <svg
              v-if="item[role]"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 1024 1024"
              class="perm-check"
            >
              <path d="M704 352l48 48-304 304-176-176 48-48 128 128z" />
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 1024 1024"
              class="perm-cross"
            >
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                :d="DENY_ICON_PATH"
              />
            </svg>
          </span>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import { PERMISSION_ITEMS } from '../constants';
import { getRoleLabel } from '../utils';
import { MEMBER_ROLES, type MemberRole } from '@/constants/gateway-permission';

interface IProps {
  aiGateway?: boolean
}

const highlightRole = defineModel<MemberRole | ''>('highlightRole', { default: '' });

const { aiGateway = false } = defineProps<IProps>();

const { t } = useI18n();

const DENY_ICON_PATH = [
  'M452.7573333333333 510.91200000000003',
  'L225.83338666666668 737.8346666666666',
  '286.1730133333333 798.1738666666666',
  '513.0965333333334 571.2511999999999',
  '739.8399999999999 797.9946666666666',
  '797.9946666666666 739.8399999999999',
  '571.2511999999999 513.0965333333334',
  '798.1738666666666 286.1730133333333',
  '737.8346666666666 225.83338666666668',
  '510.91200000000003 452.7573333333333',
  '283.9867733333333 225.83338666666668',
  '225.83338666666668 283.9867733333333',
  '452.7573333333333 510.91200000000003Z',
].join(' ');

const visibleItems = computed(() => {
  const items = PERMISSION_ITEMS.filter(item => !item.aiOnly || aiGateway);
  return [...items].sort((left, right) => Number(right.operator) - Number(left.operator));
});

</script>

<style lang="scss" scoped>
.permission-matrix {
  width: 100%;
  font-size: 12px;
  color: #313238;
  background: #fff;
  border: 1px solid #dcdee5;
  border-collapse: collapse;

  th,
  td {
    height: 42px;
    padding: 0 16px;
    text-align: left;
    background: #fff;
    border-bottom: 1px solid #dcdee5;
  }

  th {
    font-weight: 700;
    background: #fafbfd;
  }

  th:not(:first-child),
  td:not(:first-child) {
    width: 180px;
    text-align: center;
    cursor: pointer;
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  .is-active {
    background: #f0f5ff;
  }

  th.is-active {
    box-shadow: inset 1px 0 0 #3a84ff, inset -1px 0 0 #3a84ff, inset 0 1px 0 #3a84ff;
  }

  td.is-active {
    box-shadow: inset 1px 0 0 #3a84ff, inset -1px 0 0 #3a84ff;
  }

  tbody tr:last-child td.is-active {
    box-shadow: inset 1px 0 0 #3a84ff, inset -1px 0 0 #3a84ff, inset 0 -1px 0 #3a84ff;
  }
}

.has-tip {
  cursor: pointer;
  border-bottom: 1px dashed #979ba5;
}

.perm-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  line-height: 1;

  .perm-check,
  .perm-cross {
    overflow: hidden;
    vertical-align: middle;
  }

  .perm-check {
    width: 24px;
    height: 26px;
    fill: #2caf5e;
  }

  .perm-cross {
    width: 18px;
    height: 26px;
    fill: #ea3636;
  }

  &.is-muted {

    .perm-check,
    .perm-cross {
      fill: #c4c6cc;
    }
  }
}
</style>
