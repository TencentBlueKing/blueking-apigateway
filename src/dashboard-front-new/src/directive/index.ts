import { bkTooltips } from 'bkui-vue';
// import overflowTitle from './overflowTitle';

const clickOutSide = {
  beforeMount(el: any, binding: any) {
    function documentHandler(e: any) {
      if (el.contains(e.target)) return false;
      if (binding.value) {
        binding.value(e);
      }
    }
    el.__vueClickOutside__ = documentHandler;
    document.addEventListener('click', documentHandler);
  },
  unmounted(el: any) {
    document.removeEventListener('click', el.__vueClickOutside__);
    delete el.__vueClickOutside__;
  },
};


const directives: Record<string, any> = {
  // 指令对象
  bkTooltips,
  // overflowTitle,
  clickOutSide,
};

export default {
  install(app: any) {
    Object.keys(directives).forEach((key) => {
      app.directive(key, directives[key]);
    });
  },
};
