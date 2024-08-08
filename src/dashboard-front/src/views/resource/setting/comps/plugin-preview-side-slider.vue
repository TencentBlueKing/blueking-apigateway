<template>
  <div class="edit-container">
    <bk-sideslider
      v-model:isShow="renderShow"
      width="640"
      :title="t('查看插件')"
      quick-close
      @hidden="handleHidden"
    >
      <template #default>
        <div class="collapse-wrap">
          <bk-collapse
            v-model="activeIndex"
            class="collapse-cls"
            use-card-theme
          >
            <bk-collapse-panel v-for="plugin in plugins" :key="plugin.type" :name="plugin.name || plugin.type">
              <template #header>
                <div class="panel-header">
                  <angle-up-fill
                    :class="[activeIndex?.includes(plugin.type) ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">{{ plugin.name || plugin.type }}</div>
                </div>
              </template>
              <template #content>
                <article class="p24">{{ parseYaml(plugin.yaml) }}</article>
              </template>
            </bk-collapse-panel>
          </bk-collapse>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, toRefs, watch } from 'vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import yaml from 'js-yaml';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

type PluginType = {
  id?: number;
  name?: string;
  type: string;
  yaml: string;
};

interface IProps {
  isSliderShow: boolean;
  plugins: PluginType[];
}

const props = withDefaults(defineProps<IProps>(), {
  isSliderShow: false,
  plugins: () => [],
});

const { plugins } = toRefs(props);

const emits = defineEmits<{
  'on-hidden': [],
}>();

const activeIndex = computed(() => plugins.value.map(plugin => plugin.type));
const renderShow = ref(props.isSliderShow);

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

const parseYaml = (yamlStr: string) => {
  try {
    return (yamlStr && typeof yamlStr === 'string') ? JSON.stringify(yaml.load(yamlStr, { json: true })) : '{}';
  } catch {
    return yamlStr;
  }
};

watch(() => props.isSliderShow, (val) => {
  renderShow.value = val;
});

</script>
<style scoped lang="scss">

:deep(.bk-modal-content) {
  background-color: #f5f7fa;
}

.collapse-wrap {
  padding: 24px 24px 0 24px;

  :deep(.collapse-cls) {
    margin-bottom: 52px;

    .bk-collapse-item {
      background: #fff;
      box-shadow: 0 2px 4px 0 #1919290d;
      margin-bottom: 16px;
    }
  }

  .panel-header {
    display: flex;
    align-items: center;
    padding: 24px;
    cursor: pointer;

    .title {
      font-weight: 700;
      font-size: 14px;
      color: #313238;
      margin-left: 8px;
    }

    .panel-header-show {
      transition: .2s;
      transform: rotate(0deg);
    }

    .panel-header-hide {
      transition: .2s;
      transform: rotate(-90deg);
    }
  }

  :deep(.bk-collapse-content) {
    padding-top: 0 !important;
    padding-left: 0 !important;
  }
}

:deep(.bk-modal-body),
:deep(.bk-sideslider-footer) {
  background-color: #f5f7fa;
}
</style>
