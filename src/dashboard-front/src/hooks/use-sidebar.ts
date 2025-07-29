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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { usePopInfoBox } from '@/hooks';
// import mitt from '@/common/event-bus';

export function useSidebar() {
  const { t } = useI18n();
  const initDataStr = ref('');
  // const isBackDialogShow = ref(false);

  const initSidebarFormData = (data?: any) => {
    initDataStr.value = JSON.stringify(data);
  };

  const isSidebarClosed = (targetDataStr?: any) => {
    let isEqual = initDataStr.value === targetDataStr;
    if (typeof targetDataStr !== 'string') {
      // 数组长度对比
      const initData = JSON.parse(initDataStr.value);
      isEqual = initData.length === targetDataStr.length;
    }
    return new Promise((resolve) => {
      // 未编辑
      if (isEqual) {
        resolve(true);
      }
      else {
        // isBackDialogShow.value = true;
        // 已编辑
        usePopInfoBox({
          type: 'warning',
          isShow: true,
          title: t('确认离开当前页？'),
          subTitle: t('离开将会导致未保存信息丢失'),
          confirmText: t('离开'),
          cancelText: t('取消'),
          onConfirm: () => {
            resolve(true);
            // mitt.emit('on-leave-page-change', {});
            // isBackDialogShow.value = false;
          },
          onCancel: () => {
            resolve(false);
            // isBackDialogShow.value = false;
          },
        });
      }
    });
  };

  return {
    initSidebarFormData,
    isSidebarClosed,
    // isBackDialogShow,
  };
};
