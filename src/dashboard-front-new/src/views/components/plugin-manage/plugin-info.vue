<template>
  <div class="plugin-info">
    <span class="cur-icon">{{ pluginCodeFirst(curInfo.code) }}</span>
    <div class="cur-text">
      <p class="cur-name">{{ curInfo.name }}</p>
      <ul class="cur-binding-info">
        <li>
          {{ t('当前版本：') }}
          <span class="cur-version">{{ t('1.0.0') }}</span>
        </li>
        <li>
          {{ t('已绑定的资源：') }}
          <span :class="[curInfo.related_scope_count.resource === 0 ? 'empty' : 'bound',]">
            {{ curInfo.related_scope_count.resource }}
          </span>
        </li>
        <li>
          {{ t('已绑定的环境：') }}
          <span :class="[curInfo.related_scope_count.stage === 0 ? 'empty' : 'bound',]">
            {{ curInfo.related_scope_count.stage }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPluginForm } from '@/http';
const { t } = useI18n();

const props = defineProps({
  curPlugin: {
    type: Object,
  },
});
const curInfo = ref<any>({});

const pluginCodeFirst = computed(() => (code: string) => {
  console.log(code);
  return code.charAt(3).toUpperCase();
});

const init = () => {
  curInfo.value = props.curPlugin;
};
init();
</script>

<style lang="scss" scoped>
.plugin-info {
  background-color: #f5f7fb;
  padding: 15px 20px;
  display: flex;

  .cur-icon {
    display: inline-block;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: #eff1f5;
    color: #3a84f6;
    text-align: center;
    line-height: 60px;
    font-weight: 600;
    font-size: 30px;
    margin-right: 18px;
  }

  .cur-name {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 5px;
    margin-top: 10px;
  }

  .cur-binding-info {
    display: flex;
    width: 370px;
    justify-content: space-between;
    color: #b9bac1;

    .cur-version {
      color: #333539;
      font-weight: 600;
    }

    .empty {
      color: #646569;
      font-weight: 600;
    }

    .bound {
      color: #4b8ceb;
      font-weight: 600;
    }
  }
}
</style>
