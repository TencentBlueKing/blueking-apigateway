<template>
  <div class="card-list">
    <div class="card-wrapper" v-for="(stageData, index) in stageList" :key="index" @click="handleToDetail(stageData)">
      <div class="title">
        <span :class="['dot', stageData.release.status]"></span>
        {{ stageData.name }}
      </div>
      <div class="content">
        <div class="apigw-form-item">
          <div class="label">{{ `${t('访问地址')}：` }}</div>
          <div class="value url">
            <p class="link">--</p>
            <i class="apigateway-icon icon-ag-copy-info"></i>
          </div>
        </div>
        <div class="apigw-form-item">
          <div class="label">{{ `${t('当前资源版本')}：` }}</div>
          <div class="value">
            <span class="unrelease" v-if="stageData.release.status === 'unreleased'">{{ t('未发布') }}</span>
            <span v-else>{{ stageData.resource_version || '--' }}</span>
          </div>
        </div>
        <div class="apigw-form-item">
          <div class="label">{{ `${t('发布人')}：` }}</div>
          <div class="value">
            {{ stageData.release.created_by || '--' }}
          </div>
        </div>
        <div class="apigw-form-item">
          <div class="label">{{ `${t('发布时间')}：` }}</div>
          <div class="value">
            {{ stageData.release.created_time || '--' }}
          </div>
        </div>
      </div>
    </div>
    <div class="card-wrapper add-stage">
      <i class="apigateway-icon icon-ag-add-small"></i>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from 'vue';
import { IStageData } from '../types/stage';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
const router = useRouter();
const { t } = useI18n();

const props = defineProps<{
  stageList: [IStageData];
}>();

// 环境列表
const { stageList } = toRefs(props);

// 环境详情
const handleToDetail = (data) => {
  console.log(data);

  router.push({
    name: 'apigwStageDetail',
    params: {
      id: 1
    }
  });
}

</script>

<style lang="scss" scoped>
.card-list {
  min-width: 1280px;
  display: flex;
}

.card-wrapper {
  flex: 1;
  font-size: 12px;
  height: 223px;
  background: #ffffff;
  padding: 0 24px;
  box-shadow: 0 2px 4px 0 #1919290d;
  border-radius: 2px;
  margin-right: 18px;

  &:last-child {
    margin-right: 0;
  }

  .title {
    height: 52px;
    display: flex;
    align-items: center;
    font-size: 14px;
    font-weight: 700;
    color: #313238;
    border-bottom: 1px solid #DCDEE5;

    span {
      margin-right: 8px;
    }
  }

  .content {
    padding-top: 5px;
    font-size: 12px;

    .apigw-form-item {
      display: flex;
      align-items: center;
      line-height: 32px;
      color: #63656e;

      .label {
        padding-right: 24px;
        width: 120px;
        text-align: right;
      }

      .value {
        max-width: 220px;
        color: #313238;

        &.url {
          max-width: 200px;
          display: flex;
          align-items: center;

          .link {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
          }

          i {
            cursor: pointer;
            color: #3A84FF;
            margin-left: 6px;
            font-size: 12px;
          }
        }
      }
    }

    .unrelease {
      display: inline-block;
      font-size: 10px;
      color: #FE9C00;
      background: #FFF1DB;
      border-radius: 2px;
      padding: 2px 5px;
      line-height: 1;
    }
  }

  &.add-stage {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;

    i {
      color: #979BA5;
      font-size: 40px;
    }

    &:hover {
      cursor: pointer;
      i {
        color: #3A84FF;
      }
    }
  }


  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #E5F6EA;

    &.success {
      border: 1px solid #3FC06D;
    }

    &.unreleased {
      border: 1px solid #3FC06D;
    }
  }
}</style>
