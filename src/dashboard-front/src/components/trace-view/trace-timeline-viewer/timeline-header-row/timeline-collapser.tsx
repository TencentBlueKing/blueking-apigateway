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

import { type PropType, defineComponent } from 'vue';

import { Popover } from 'bkui-vue';
import { t } from '@/locales';
import AgIcon from '@/components/ag-icon/Index.vue';

import './timeline-collapser.scss';

const CollapserProps = {
  onCollapseAll: Function as PropType<() => void>,
  onCollapseOne: Function as PropType<() => void>,
  onExpandOne: Function as PropType<() => void>,
  onExpandAll: Function as PropType<() => void>,
};

export default defineComponent({
  name: 'TimelineCollapser',
  props: CollapserProps,

  render() {
    const { onCollapseAll, onCollapseOne, onExpandOne, onExpandAll } = this.$props;

    return (
      <div class="timeline-collapser">
        <Popover
          content={t('展开 1 层')}
          placement="top"
          popoverDelay={[500, 0]}
          theme="dark"
        >
          <div
            class="collapser-btn"
            onClick={onExpandOne}
          >
            <AgIcon
              name="down-small"
              size="24"
              color="#979ba5"
            />
          </div>
        </Popover>
        <Popover
          content={t('收起 1 层')}
          placement="top"
          popoverDelay={[500, 0]}
          theme="dark"
        >
          <div
            class="collapser-btn rotate-[-90deg]"
            onClick={onCollapseOne}
          >
            <AgIcon
              name="down-small"
              size="24"
              color="#979ba5"
            />
          </div>
        </Popover>
        <Popover
          content={t('全部展开')}
          placement="top"
          popoverDelay={[500, 0]}
          theme="dark"
        >
          <div
            class="collapser-btn"
            onClick={onExpandAll}
          >
            <AgIcon
              name="arrows-down"
              size="24"
              color="#979ba5"
            />
          </div>
        </Popover>
        <Popover
          content={t('全部收起')}
          placement="top"
          popoverDelay={[500, 0]}
          theme="dark"
        >
          <div
            class="collapser-btn rotate-[90deg]"
            onClick={onCollapseAll}
          >
            <AgIcon
              name="arrows-up"
              size="24"
              color="#979ba5"
              class="transform-rotateX"
            />
          </div>
        </Popover>
      </div>
    );
  },
});
