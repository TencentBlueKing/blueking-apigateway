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
import { defineStore } from 'pinia';
import { t } from '@/locales';
import dayjs from 'dayjs';

export const usePermission = defineStore('usePermission', {
  state: () => ({ count: 0 }),
  actions: {
    /**
     * 设置待审批的数量
     * @param {number} count
     */
    setCount(count: number) {
      this.count = count;
    },
    // 获取有效期时间
    getDurationText(expireAt: string | null) {
      if (!expireAt) {
        return t('永久');
      }
      const today = dayjs();
      const expireDate = dayjs(expireAt);
      if (today.isAfter(expireDate)) {
        return t('已过期');
      }
      return `${expireDate.diff(today, 'day')}${t('天')}`;
    },
    // 获取有效期时间对应样式
    getDurationTextColor(expireAt: string | null) {
      if (!expireAt) {
        return '#2caf5e';
      }
      const today = dayjs();
      const expireDate = dayjs(expireAt);
      if (today.isAfter(expireDate)) {
        return '#f59500';
      }
      return '#63656e';
    },
    // 计算续期后的过期时间
    getDurationAfterRenew(expireAt: string | null, day: number) {
      const curDay = day ?? 0;
      if (!expireAt || curDay === 0) {
        return t('永久');
      }
      const today = dayjs();
      const expireDate = dayjs(expireAt);
      // 已过期
      if (today.isAfter(expireDate)) {
        return `${curDay}${t('天')}`;
      }
      const daysLeft = expireDate.diff(today, 'day');
      return `${daysLeft + curDay}${t('天')}`;
    },
  },
});
