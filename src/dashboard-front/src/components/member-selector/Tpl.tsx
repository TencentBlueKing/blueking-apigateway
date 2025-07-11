import { defineComponent } from 'vue';

export default defineComponent({
  // 定义组件的props
  props: {
    // 英文名，类型为字符串，默认值为空字符串
    englishName: {
      type: String,
      default: '',
    },

    // 中文名，类型为字符串，默认值为空字符串
    chineseName: {
      type: String,
      default: '',
    },
  },

  // 组件的setup函数
  setup(props) {
    // 返回一个渲染函数
    return () => (
      <div class="flex items-center flex-grow-1 p-10px">
        {props.englishName}
        {' '}
        (
        {props.chineseName}
        )
      </div>
    );
  },
});
