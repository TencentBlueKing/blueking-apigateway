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
import { defineStore } from 'pinia';
import { t } from '@/locales';
import dayjs from 'dayjs';

export const usePermission = defineStore('usePermission', {
  state: () => ({
    // API 网关待审批数量
    count: 0,
    // MCP Server 权限待审批数量
    mcpCount: 0,
  }),
  actions: {
    /**
     * 设置待审批的数量
     * @param {number} count
     */
    setCount(count: number) {
      this.count = count;
    },
    /**
     * 设置 MCP Server 权限待审批的数量
     * @param {number} count
     */
    setMcpCount(count: number) {
      this.mcpCount = count;
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
      const daysLeft = expireDate.diff(today, 'day');
      // 有效期不足 24 小时但尚未过期时，以小时为单位展示；不足 1 小时时不显示“0小时”
      if (daysLeft < 1) {
        const hoursLeft = expireDate.diff(today, 'hour');
        return hoursLeft < 1 ? t('不足 1 小时') : `${hoursLeft}${t('小时')}`;
      }
      return `${daysLeft}${t('天')}`;
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
    // 计算续期后的剩余天数，与后端续期规则一致：
    // 未过期时从原到期时间顺延，已过期时从当前时间起算；0 天表示续期为永久
    getDurationAfterRenew(expireAt: string | null, day: number) {
      const curDay = day ?? 0;
      if (!expireAt || curDay === 0) {
        return t('永久');
      }
      const today = dayjs();
      const expireDate = dayjs(expireAt);
      const renewBase = expireDate.isAfter(today) ? expireDate : today;
      return `${renewBase.add(curDay, 'day').diff(today, 'day')}${t('天')}`;
    },
  },
});
