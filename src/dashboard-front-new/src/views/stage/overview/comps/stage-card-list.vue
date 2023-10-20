<template>
  <div class="card-list">
    <div class="card-item" v-for="(stageData, index) in stageList" :key="index" @click="handleToDetail(stageData)">
      <div class="title">
        <span :class="['dot', stageData.release.status]"></span>
        {{ stageData.name }}
      </div>
      <div class="content">
        <div class="apigw-form-item">
          <div class="label">{{ `${t('访问地址')}：` }}</div>
          <div class="value url">
            <p class="link">--</p>
            <i class="apigateway-icon icon-ag-copy-info" @click.self.stop="copy('--')"></i>
          </div>
        </div>
        <div class="apigw-form-item">
          <div class="label">{{ `${t('当前资源版本')}：` }}</div>
          <div class="value">
            <span class="unrelease" v-if="stageData.release.status === 'unreleased'">{{ t('未发布') }}</span>
            <span v-else>{{ stageData.resource_version.version || '--' }}</span>
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
    <div class="card-item add-stage" @click="handleAddStage">
      <i class="apigateway-icon icon-ag-add-small"></i>
    </div>

    <!-- 环境侧边栏 -->
    <edit-stage-sideslider ref="stageSidesliderRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { copy } from '@/common/util';
import editStageSideslider from './edit-stage-sideslider.vue';
import mitt from '@/common/event-bus';
const router = useRouter();
const route = useRoute();
const { t } = useI18n();

const props = defineProps<{
  stageList: any[];
}>();

// 环境列表
const { stageList } = toRefs(props);

// 环境详情
const handleToDetail = (data: any) => {
  console.log('data', data);
  mitt.emit('switch-mode', { id: data.id, name: data.name });
  // 改变tab
  // router.push({
  //   name: 'apigwStageDetail',
  //   params: {
  //     id: route.params.id,
  //   },
  //   query: {
  //     stage: data.name,
  //   }
  // });
}

// 新建环境
const stageSidesliderRef = ref(null)
const handleAddStage = () => {
  stageSidesliderRef.value.handleShowSideslider('add');
}

</script>

<style lang="scss" scoped>
.card-list {
  min-width: calc(1280px - 260px);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-gap: 18px; /* 设置盒子之间的间隔 */
}

/* 分辨率大于1920时 */
@media (min-width: 1921px) {
  .card-list {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 适应更小的分辨率，每行最多显示三个盒子 */
@media (max-width: 1920px) {
  .card-list {
    grid-template-columns: repeat(3, 1fr);
  }
}

.card-item {
  font-size: 12px;
  height: 223px;
  background: #ffffff;
  padding: 0 24px;
  box-shadow: 0 2px 4px 0 #1919290d;
  border-radius: 2px;

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
            margin-left: 3px;
            font-size: 12px;
            padding: 3px;
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
