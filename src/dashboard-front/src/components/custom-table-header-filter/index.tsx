import {
  defineComponent,
  ref,
  unref,
  watch,
} from 'vue';
import { Popover } from 'bkui-vue';
import { Funnel } from 'bkui-vue/lib/icon';
import { cloneDeep } from 'lodash';
import './custom-table-header-filter.scss';
import i18n from '@/language/i18n';

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
      type: Array,
      default: () => {
        return [] as any[];
      },
    },
  },
  emits: ['selected'],
  setup(props, ctx) {
    const { t } = i18n.global;
    const popoverRef = ref();
    const isShowFilterPopover = ref(false);
    const curSelectValue = ref('') as any;
    const filterList = ref([]);

    // 处理打开弹出框的逻辑
    const handleOpenPopover = (e: Event) => {
      e.stopPropagation();
      isShowFilterPopover.value = !isShowFilterPopover.value;
    };

    // 处理选中项的逻辑
    const handleSelected = (e: Event, payload: Record<string, string>) => {
      e.stopPropagation();
      curSelectValue.value = cloneDeep(payload.id);
      ctx.emit('selected', payload);
      isShowFilterPopover.value = false;
    };

    // 处理点击弹出框外部的逻辑
    const handleClickOutSide = (e: any) => {
      if (
        isShowFilterPopover.value
        && !unref(popoverRef).content.el?.contains(e.target)
      ) {
        isShowFilterPopover.value = false;
      }
    };

    ctx.expose({ popoverRef, onSelected: handleSelected });

    // 监听 selectValue 属性的变化
    watch(
      () => props.selectValue, (payload: string | number) => {
        curSelectValue.value = cloneDeep(payload);
      },
      { immediate: true, deep: true },
    );

    // 监听 list 属性的变化
    watch(
      () => props.list, (payload: any[]) => {
        filterList.value = props.hasAll ? cloneDeep([...[{ id: 'ALL', name: t('全部') }], ...payload]) : cloneDeep(payload);
      },
      { immediate: true, deep: true },
    );

    return () => (
      <div class="custom-header-column-wrapper">
        <div>{props.columnLabel}</div>
        <Popover
          {...ctx.attrs}
          trigger='manual'
          theme='light'
          placement="bottom-start"
          ref={popoverRef}
          is-show={isShowFilterPopover.value}
          extCls='custom-filter-popover'
          arrow={false}
          componentEventDelay={400}
          content={
            <div class='custom-radio-filter-wrapper'>
              {
                filterList.value.map((item: Record<string, string>) => {
                  return (
                    <div
                      class={[
                        'custom-radio-filter-content',
                      ]}
                      onClick={(e: Event) => handleSelected(e, item)}
                    >
                      <div
                        class={[
                          'custom-radio-filter-item',
                          { 'is-selected': curSelectValue.value === item.id },
                        ]}>
                        {item.name}
                      </div>
                    </div>
                  );
                })
              }
            </div>
          }
        >
          <div v-clickOutSide={(e: any) => handleClickOutSide(e)}>
            <Funnel
              class={[
                'custom-filter-icon',
                { 'is-open': isShowFilterPopover.value },
                { 'is-active': curSelectValue.value  && !['ALL'].includes(curSelectValue.value) },
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
