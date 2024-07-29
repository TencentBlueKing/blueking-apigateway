<template>
  <div class="edit-container">
    <bk-sideslider
      v-model:isShow="renderShow"
      width="800"
      title="修改配置"
      quick-close
      @hidden="handleHidden"
    >
      <template #default>
        <div style="padding: 24px 0 40px;">
          <bk-collapse
            v-model="activeIndex"
            use-card-theme
          >
            <bk-collapse-panel name="baseInfo" :title="t('基础信息')">
              <template #content>
                <base-info ref="baseInfoRef" :detail="props.resource"></base-info>
              </template>
            </bk-collapse-panel>

            <bk-collapse-panel name="frontConfig" :title="t('前端配置')">
              <template #content>
                <front-config ref="frontConfigRef" :detail="props.resource"></front-config>
              </template>
            </bk-collapse-panel>

            <bk-collapse-panel name="backConfig" :title="t('后端配置')">
              <template #content>
                <back-config ref="backConfigRef" :detail="props.resource"></back-config>
              </template>
            </bk-collapse-panel>
          </bk-collapse>
        </div>
      </template>
      <template #footer>
        <div style="padding-left: 60px;">
          <bk-button
            theme="primary"
            @click="handleSubmit"
          >
            {{ t('保存') }}
          </bk-button>
          <bk-button style="margin-left: 6px;" @click="handleHidden"> {{ t('取消') }}</bk-button>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import BaseInfo from '@/views/resource/setting/comps/base-info.vue';
import FrontConfig from '@/views/resource/setting/comps/front-config.vue';
import BackConfig from '@/views/resource/setting/comps/back-config.vue';

const { t } = useI18n();
const props = defineProps({
  isSliderShow: { type: Boolean, default: false },
  resource: { type: Object, default: () => ({}) },
});

const emits = defineEmits<{
  'on-hidden': [],
  'submit': [resConfig: any]
}>();

// 默认展开
const activeIndex = ref(['baseInfo', 'frontConfig', 'backConfig']);
const baseInfoRef = ref(null);
const frontConfigRef = ref(null);
const backConfigRef = ref(null);
const renderShow = ref(props.isSliderShow);

const formData = ref<any>({});

// 提交
const handleSubmit = async () => {
  await baseInfoRef.value?.validate();
  await frontConfigRef.value?.validate();
  await backConfigRef.value?.validate();
  const baseFormData = baseInfoRef.value.formData;
  const frontFormData = frontConfigRef.value.frontConfigData;
  const backFormData = backConfigRef.value.backConfigData;
  try {
    const payload = {
      ...baseFormData,
      ...frontFormData,
      backend: backFormData,
    };
    emits('submit', payload);
    emits('on-hidden');
  } catch (error) {
    console.log('error', error);
  }
};

const handleHidden = () => {
  renderShow.value = false;
  formData.value = {};
  emits('on-hidden');
};

watch(() => props.isSliderShow, (val) => {
  renderShow.value = val;
});

</script>
<style scoped lang="scss">

:deep(.bk-collapse-card .bk-collapse-item) {
  box-shadow: none;
}
</style>
