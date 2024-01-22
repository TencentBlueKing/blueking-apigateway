import { defineComponent } from 'vue';

export default defineComponent({
  props: {
    englishName: {
      type: String,
      default: '',
    },
    chineseName: {
      type: String,
      default: '',
    },
  },
  setup(props) {
    return () => (
      <div class="flex-row align-items-center flex-1 p10">
        {props.englishName} ({props.chineseName})
      </div>
    );
  },
});
