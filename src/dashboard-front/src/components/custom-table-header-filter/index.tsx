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
import { Popover } from 'bkui-vue'; // 引入 bkui-vue 库中的 Popover 组件
import { Funnel } from 'bkui-vue/lib/icon'; // 引入 bkui-vue 库中的 Funnel 图标组件
import { cloneDeep } from 'lodash-es'; // 引入 lodash 库中的 cloneDeep 方法，用于深拷贝对象
import { t } from '@/locales'; // 引入国际化配置
import './custom-table-header-filter.scss'; // 引入自定义的样式文件

type IFilter = {
  name: string
  id: string | number
};

export default defineComponent({
  props: {
    // 表格列的标签
    columnLabel: {
      type: String,
      default: '',
    },

    // 当前选中的值
    selectValue: {
      type: [String, Number],
      default: '',
    },

    // 是否包含“全部”选项
    hasAll: {
      type: Boolean,
      default: true,
    },

    // 过滤列表数据
    list: {
      type: Array as PropType<IFilter[]>,
      default: () => [],
    },
  },

  emits: ['selected'],

  setup(props, ctx) {
    // 引用弹出框组件的引用
    const popoverRef = ref();
    // 控制弹出框显示状态的变量
    const isShowFilterPopover = ref(false);
    // 当前选中的值
    const curSelectValue = ref<string | number>('');
    // 过滤列表数据
    const filterList = ref<IFilter[]>([]);

    // 处理打开弹出框的逻辑
    const handleOpenPopover = (e: Event) => {
      e.stopPropagation();
      isShowFilterPopover.value = !isShowFilterPopover.value;
    };

    // 处理选中项的逻辑
    const handleSelected = (e: Event, payload: Record<string, string | number>) => {
      e.stopPropagation();
      curSelectValue.value = cloneDeep(payload.id);
      ctx.emit('selected', payload);
      isShowFilterPopover.value = false;
    };

    // 处理点击弹出框外部的逻辑
    const handleClickOutSide = (e: MouseEvent) => {
      if (
        isShowFilterPopover.value
        && !unref(popoverRef).content.el?.contains(e.target)
      ) {
        isShowFilterPopover.value = false;
      }
    };

    ctx.expose({
      popoverRef,
      onSelected: handleSelected,
    });

    // 监听 selectValue 属性的变化
    watch(
      () => props.selectValue, (payload: string | number) => {
        curSelectValue.value = cloneDeep(payload);
      },
      {
        immediate: true,
        deep: true,
      },
    );

    // 监听 list 属性的变化
    watch(
      () => props.list as IFilter[], (payload: IFilter[]) => {
        const AllOption = [
          {
            id: 'ALL',
            name: t('全部'),
          },
        ];
        filterList.value = props.hasAll
          ? cloneDeep([...AllOption, ...payload])
          : cloneDeep(payload);
      },
      {
        immediate: true,
        deep: true,
      },
    );

    return () => (
      <div class="custom-header-column-wrapper">
        <div>{props.columnLabel}</div>
        <Popover
          {...ctx.attrs}
          trigger="manual"
          theme="light"
          placement="bottom-start"
          ref={popoverRef}
          is-show={isShowFilterPopover.value}
          extCls="custom-filter-popover"
          arrow={false}
          componentEventDelay={400}
          content={(
            <div class="custom-radio-filter-wrapper">
              {
                filterList.value.map((item: Record<string, string | number>) => {
                  return (
                    <div
                      class={[
                        'custom-radio-filter-content',
                      ]}
                      onClick={(e: MouseEvent) => handleSelected(e, item)}
                    >
                      <div
                        class={[
                          'custom-radio-filter-item',
                          { 'is-selected': curSelectValue.value === item.id },
                        ]}
                      >
                        {item.name}
                      </div>
                    </div>
                  );
                })
              }
            </div>
          )}
        >
          <div v-clickOutSide={(e: MouseEvent) => handleClickOutSide(e)}>
            <Funnel
              class={[
                'custom-filter-icon',
                { 'is-open': isShowFilterPopover.value },
                { 'is-active': curSelectValue.value && !['ALL'].includes(curSelectValue.value as string) },
              ]}
              onClick={(e: Event) => {
                handleOpenPopover(e);
              }}
            />
          </div>
        </Popover>
      </div>
    );
  },
});
