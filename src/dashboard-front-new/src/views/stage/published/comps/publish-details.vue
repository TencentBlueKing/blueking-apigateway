<template>
  <bk-sideslider
    v-model:isShow="isShow"
    :width="1050"
    quick-close
  >
    <template #header>
      {{ t('操作详情') }}【{{ t('发布资源版本') }}: {{ props.id }}】
      <bk-tag theme="success">
        {{ t('操作成功') }}
      </bk-tag>
      <bk-tag theme="danger">
        {{ t('操作失败') }}
      </bk-tag>
    </template>
    <template #default>
      <div class="details-main">
        <div class="base-info">
          <div class="info-title">{{ t('基础信息') }}</div>
          <div class="info-content">
            <bk-container :margin="32">
              <bk-row>
                <bk-col :span="12">
                  <div class="content">
                    <div class="label">{{ t('操作对象') }}:</div>
                    <div class="value">网关</div>
                  </div>
                </bk-col>
                <bk-col :span="12">
                  <div class="content">
                    <div class="label">{{ t('实例') }}:</div>
                    <div class="value">bkapigateway</div>
                  </div>
                </bk-col>
              </bk-row>
              <bk-row>
                <bk-col :span="12">
                  <div class="content">
                    <div class="label">{{ t('操作类型') }}:</div>
                    <div class="value">更新</div>
                  </div>
                </bk-col>
                <bk-col :span="12">
                  <div class="content">
                    <div class="label">{{ t('生效环境') }}:</div>
                    <div class="value">--</div>
                  </div>
                </bk-col>
              </bk-row>
              <bk-row>
                <bk-col :span="12">
                  <div class="content">
                    <div class="label">{{ t('操作者') }}:</div>
                    <div class="value">{{ info?.created_by || '--' }}</div>
                  </div>
                </bk-col>
                <bk-col :span="12">
                  <div class="content">
                    <div class="label">{{ t('操作时间') }}:</div>
                    <div class="value">{{ info?.created_time || '--' }}</div>
                  </div>
                </bk-col>
              </bk-row>
            </bk-container>
          </div>
        </div>
        <div class="base-info">
          <div class="info-title">{{ t('差异对比') }}</div>
          <div class="info-content">
            <div class="tag-box">
              <div class="tag-add">{{ t('新增') }}</div>
              <div class="tag-del">{{ t('删除') }}</div>
              <div class="tag-update">{{ t('更新') }}</div>
            </div>
            <div class="diff-box">
              <div class="diff-title">
                <div class="diff-before-title">
                  {{ t('操作前') }}（1.0.0）
                </div>
                <div class="diff-after-title">
                  {{ t('操作后') }}（1.0.1）
                </div>
              </div>
              <div class="diff-content">
                <div class="diff-version">
                  {{ t('资源版本') }}: <span>1.0.0</span>
                </div>
                <div class="diff-version">
                  {{ t('资源版本') }}: <span>1.0.2</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </bk-sideslider>
</template>

<script lang="ts" setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { getReleaseLatest } from '@/http';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const route = useRoute();
const apigwId = computed(() => +route.params.id);

const props = defineProps({
  id: String,
});

const isShow = ref<boolean>(false);
const info = ref<any>();

const showSideslider = () => {
  isShow.value = true;
};

const getDetails = async () => {
  try {
    const res = await getReleaseLatest(apigwId.value);
    info.value = res;
    console.log(res);
  } catch (e) {
    console.log(e);
  }
};

watch(
  () => props.id,
  (id) => {
    if (id && isShow.value) {
      getDetails();
    }
  },
);

defineExpose({
  showSideslider,
});
</script>

<style lang="scss" scoped>
.details-main {
  padding: 24px;
  .base-info {
    margin-bottom: 38px;
    .info-title {
      font-size: 14px;
      color: #313238;
      font-family: MicrosoftYaHei-Bold;
      font-weight: 700;
      margin-bottom: 20px;
    }
    .info-content {
      .content {
        display: flex;
        align-items: center;
        padding-bottom: 12px;
        .label {
          color: #63656E;
          font-size: 12px;
          margin-right: 10px;
          min-width: 64px;
          text-align: right;
        }
        .value {
          color: #313238;
          font-size: 12px;
        }
      }

      .tag-box {
        display: flex;
        align-items: center;
        width: 100%;
        justify-content: flex-end;
        margin-bottom: 16px;
        >div {
          font-size: 12px;
          color: #63656E;
          margin-left: 12px;
          &:before {
            content: ' ';
            display: inline-block;
            width: 10px;
            height: 10px;
            margin-right: 6px;
            vertical-align: middle;
          }
          &.tag-add:before {
            background: #DCFFE2;
            border: 1px solid #94F5A4;
          }
          &.tag-del:before {
            background: #FFE9E8;
            border: 1px solid #FFBDBD;
          }
          &.tag-update:before {
            background: #FFEFD6;
            border: 1px solid #FFE3B5;
          }
        }
      }

      .diff-box {
        border: 1px solid #DCDEE5;
        border-radius: 2px 0 0 2px;
        .diff-title,
        .diff-content {
          display: flex;
          align-items: center;
          position: relative;
          &:after {
            content: ' ';
            width: 1px;
            height: 45px;
            background-color: #DCDEE5;
            position: absolute;
            left: 50%;
          }
        }
        .diff-title {
          line-height: 45px;
          text-align: center;
          border-bottom: 1px solid #DCDEE5;
          >div {
            width: 50%;
            box-sizing: border-box;
            font-size: 13px;
            color: #63656E;
            font-weight: bold;
            &.diff-before-title {
              background-color: #f5f7fb;
            }
            &.diff-after-title {
              background-color: #eff1f5;
            }
          }
        }
        .diff-content {
          padding-left: 70px;
          line-height: 45px;
          >div {
            width: 50%;
            box-sizing: border-box;
            font-size: 12px;
            color: #63656E;
            span {
              color: #313238;
              margin-left: 10px;
            }
          }
        }
      }
    }
  }
}
</style>
