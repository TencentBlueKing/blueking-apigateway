import { cloneDeep } from 'lodash-es';
import { Popover } from 'bkui-vue';
import { Funnel } from 'bkui-lib/icon';
import { t } from '@/locales';
import { type IFilterValue } from '@/types/permission';
import './table-header-filter.scss';

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
        return [] as PropType<IFilterValue>[];
      },
    },
  },

  emits: ['selected'],

  setup(props, ctx) {
    // 引用弹出框组件的引用
    const popoverRef = ref();
    // 控制弹出框显示状态的变量
    const isShowFilterPopover = ref(false);
    // 当前选中的值
    const curSelectValue = ref();
    // 过滤列表数据
    const filterList: Ref<IFilterValue[]> = ref([]);

    // 处理打开弹出框的逻辑
    const handleOpenPopover = (event: Event) => {
      event?.stopPropagation();
      isShowFilterPopover.value = !isShowFilterPopover.value;
    };

    // 处理选中项的逻辑
    const handleSelected = (event: Event, payload: IFilterValue) => {
      event?.stopPropagation();
      curSelectValue.value = cloneDeep(payload.id);
      ctx.emit('selected', payload);
      isShowFilterPopover.value = false;
    };

    // 处理点击弹出框外部的逻辑
    const handleClickOutSide = (event: Event) => {
      if (
        isShowFilterPopover.value
        && !unref(popoverRef).content.el?.contains(event.target)
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
      () => props.list as IFilterValue[], (payload) => {
        const allList = cloneDeep([{
          id: 'ALL',
          name: t('全部'),
        }]);
        filterList.value = props.hasAll
          ? [...allList, ...payload]
          : cloneDeep(payload);
      },
      {
        immediate: true,
        deep: true,
      },
    );

    return () => (
      <div class=" flex items-center flex-grow custom-header-column-wrapper">
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
                filterList.value.map((item: IFilterValue) => {
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
          <div v-clickOutSide={(e: Event) => handleClickOutSide(e)}>
            <Funnel
              class={[
                'custom-filter-icon',
                { 'is-open': isShowFilterPopover.value },
                { 'is-active': curSelectValue.value && !['ALL'].includes(curSelectValue.value) },
              ]}
              onClick={(event: Event) => {
                handleOpenPopover(event);
              }}
            />
          </div>
        </Popover>
      </div>
    );
  },
});
