// 引入自定义的 staffStore，用于获取员工数据
import { useStaff } from '@/stores';
// 引入 bkui-vue 组件库中的 Loading 和 TagInput 组件
import {
  Loading,
  TagInput,
} from 'bkui-vue';
import { cloneDeep, debounce } from 'lodash-es';
// 引入组件的样式文件
import './member-select.scss';
import Tpl from './Tpl';

// 员工类型枚举
export enum StaffEnum { RTX = 'rtx' }

// 员工接口
export interface IStaff {
  english_name: string // 英文名
  chinese_name: string // 中文名
  username: string // 用户名
  display_name: string // 显示名
}

export default defineComponent({
  props: {
    // 是否禁用组件
    disabled: { type: Boolean },
    // 绑定的值，类型为字符串数组
    modelValue: { type: Array as PropType<string[]> },

    // 员工类型，默认值为 StaffEnum.RTX
    type: {
      type: String as PropType<StaffEnum>,
      default: StaffEnum.RTX,
    },

    // 是否允许多选，默认值为 true
    multiple: {
      type: Boolean,
      default: true,
    },

    // 是否允许清除，默认值为 true
    clearable: {
      type: Boolean,
      default: true,
    },

    // 是否允许创建新标签，默认值为 false
    allowCreate: {
      type: Boolean,
      default: false,
    },

    // 是否显示删除图标，默认值为 false
    hasDeleteIcon: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['change', 'input', 'blur', 'focus'],

  setup(props, ctx) {
    const tagInputRef = ref(null);
    // 使用 staffStore 获取员工数据
    const staffStore = useStaff();
    const searchKey = ['username'];
    const userList: any = ref([]);
    // 根据 multiple 属性计算最大数据量
    const maxData = computed(() => (!props.multiple
      ? { maxData: 1 }
      : {}));
    const popoverProps = { boundary: document.body };

    // 监听 staffStore.list 的变化
    watch(
      () => staffStore.list,
      (list) => {
        if (list.length) {
          nextTick(() => {
            userList.value = cloneDeep(list);
          });
        }
        else {
          staffStore.fetchStaffs(props.modelValue?.join(',') || '');
        }
      },
      {
        immediate: true,
        deep: true,
      },
    );

    // 渲染员工信息模板
    function tpl(node: IStaff) {
      return (
        <Tpl
          englishName={node.username}
          chineseName={node.display_name}
        />
      );
    }
    // 处理输入变化事件
    function handleChange(val: IStaff[]) {
      ctx.emit('input', val);
      ctx.emit('change', val);
    }

    // 处理焦点事件
    function handleFocus(val: IStaff[]) {
      ctx.emit('focus', val);
    }

    // 处理失焦事件
    function handleBlur(val: IStaff[]) {
      ctx.emit('blur', val);
    }

    ctx.expose({ tagInputRef });

    // 获取用户列表，防抖处理
    const getUserList = debounce((userName: string) => {
      if (staffStore.fetching || !userName) return;
      staffStore.fetchStaffs(userName);
    }, 500);

    // 处理输入事件
    function handleInput(userName: string) {
      getUserList(userName);
    }

    // 组件挂载时执行
    onMounted(() => {
      if (props.modelValue?.length) {
        staffStore.fetchStaffs(props.modelValue.join(','));
        return;
      }
    });

    return () => (
      <>
        <TagInput
          {...ctx.attrs}
          {...maxData.value}
          list={userList.value}
          ref={tagInputRef}
          displayKey="display_name"
          saveKey="username"
          is-async-list
          searchKey={searchKey}
          hasDeleteIcon={props?.hasDeleteIcon}
          modelValue={props.modelValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onInput={handleInput}
          tpl={tpl}
          tagTpl={tpl}
          clearable={props.clearable}
          allowCreate={props.allowCreate}
          popoverProps={popoverProps}
          class="color-#63656e"
        >
          {{
            suffix: () => staffStore.fetching && (
              <Loading
                class="mr-10px"
                loading={staffStore.fetching}
                mode="spin"
                size="mini"
              />
            ),
          }}
        </TagInput>
      </>
    );
  },
});
