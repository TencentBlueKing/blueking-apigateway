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

import { getStageList } from '@/services/source/stage';
import { useStage } from '@/stores';

/**
 * 获取阶段列表的自定义 Hook
 */
export const useGetStageList = () => {
  const stage = useStage();
  const route = useRoute();
  const apigwId = computed(() => +route.params.id);

  /**
   * 获取阶段状态
   */
  const getStagesStatus = async () => {
    if (!apigwId.value) return;
    const res = await getStageList(apigwId.value);

    // 筛选出未更新的阶段
    let notUpdatedStages = res?.filter((item: any) => {
      if (item.status === 1 && item.resource_version?.schema_version === '1.0') {
        return true;
      }
    });
    // 获取未更新阶段的名称
    notUpdatedStages = notUpdatedStages?.map((item: any) => item?.name);

    // 检查是否存在 schema_version 为 '2.0' 的阶段
    let exist2 = false;
    for (let i = 0; i < res?.length; i++) {
      const item = res[i];
      if (item.resource_version.schema_version === '2.0') {
        exist2 = true;
        break;
      }
    }

    // 设置未更新的阶段和是否存在 schema_version 为 '2.0' 的阶段
    stage.setNotUpdatedStages(notUpdatedStages);
    stage.setExist2(exist2);

    return {
      notUpdatedStages,
      exist2,
    };
  };

  return { getStagesStatus };
};
