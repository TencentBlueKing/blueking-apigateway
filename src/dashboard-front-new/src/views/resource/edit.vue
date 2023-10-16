<template>
  <div class="edit-container p20">
    <bk-collapse
      class="collapse-cls"
      v-model="activeIndex"
      use-card-theme
    >
      <bk-collapse-panel name="baseInfo">
        <span class="panel-title">{{ t('基础信息') }}</span>
        <template #content>
          <div class="panel-content">
            <BaseInfo ref="baseInfoRef"></BaseInfo>
          </div>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="frontConfig">
        <span class="panel-title">{{ t('前端配置') }}</span>
        <template #content>
          <div class="panel-content">
            <FrontConfig ref="frontConfigRef"></FrontConfig>
          </div>
        </template>
      </bk-collapse-panel>

      <bk-collapse-panel name="backConfig">
        <span class="panel-title">{{ t('后端配置') }}</span>
        <template #content>
          <div class="panel-content">
            <BackConfig ref="backConfigRef"></BackConfig>
          </div>
        </template>
      </bk-collapse-panel>
    </bk-collapse>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseInfo from './comps/base-info.vue';
import FrontConfig from './comps/front-config.vue';
import BackConfig from './comps/back-config.vue';
const { t } = useI18n();

const activeIndex =  ref(['baseInfo', 'frontConfig', 'backConfig']);
const baseInfoRef = ref(null);

onMounted(() => {
  setTimeout(() => {
    console.log(11111, baseInfoRef.value.formData);
  }, 1000);
});
</script>
<style lang="scss" scoped>
  .edit-container{
    :deep(.collapse-cls){
      .bk-collapse-item{
        background: #fff;
        .panel-title{
            color: #63656e;
            font-weight: 700;
        }
        .panel-content{
            width: 1100px;
        }
      }
    }
  }
    .bk-collapse-demo {
      box-shadow: 0 0 8px 0px #ccc;
    }
  </style>
