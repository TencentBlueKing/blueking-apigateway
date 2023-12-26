<template>
  <div class="card-list">
    <div class="card-item" v-for="(stageData, index) in stageList" :key="index">
      <div class="title">
        <div class="title-lf">
          <spinner v-if="getStatus(stageData) === 'doing'" fill="#3A84FF" />
          <span v-else :class="['dot', getStatus(stageData)]"></span>
          {{ stageData.name }}
        </div>
        <div class="title-rg">
          <bk-button
            theme="primary"
            size="small"
            @click="handleRelease(stageData)"
          >
            发布资源
          </bk-button>
          <bk-button
            class="ml10"
            size="small"
            :disabled="stageData.status !== 1"
            @click="handleStageUnlist(stageData.id)"
          >
            下架
          </bk-button>

        </div>
      </div>
      <div class="content" @click="handleToDetail(stageData)">
        <div class="apigw-form-item">
          <div class="label">{{ `${t('访问地址')}：` }}</div>
          <div class="value url">
            <p
              class="link"
              v-bk-tooltips="{ content: getStageAddress(stageData.name) }">
              {{ getStageAddress(stageData.name) || '--' }}
            </p>
            <i
              class="apigateway-icon icon-ag-copy-info"
              v-if="getStageAddress(stageData.name)"
              @click.self.stop="copy(getStageAddress(stageData.name))">
            </i>
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

    <!-- 发布资源至环境 -->
    <release-sideslider
      :current-assets="currentStage"
      ref="releaseSidesliderRef"
      @release-success="handleReleaseSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { copy, getStatus } from '@/common/util';
import editStageSideslider from './edit-stage-sideslider.vue';
import releaseSideslider from '../comps/release-sideslider.vue';
import mitt from '@/common/event-bus';
import { useGetGlobalProperties } from '@/hooks';
import { useCommon } from '@/store';
import { Message, InfoBox } from 'bkui-vue';
import { removalStage } from '@/http';
import { Spinner } from 'bkui-vue/lib/icon';
import { useRoute } from 'vue-router';

const common = useCommon();
const { t } = useI18n();
const route = useRoute();

// 网关id
const apigwId = computed(() => +route.params.id);

const releaseSidesliderRef = ref();
const currentStage = ref<any>({});

// 全局变量
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

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
};

// 发布资源
const handleRelease = (stage: any) => {
  currentStage.value = stage;
  releaseSidesliderRef.value?.showReleaseSideslider();
};

// 发布成功
const handleReleaseSuccess = async () => {
  await mitt.emit('get-stage-list');
};

// 下架环境
const handleStageUnlist = async (id: number) => {
  InfoBox({
    title: t('确认下架吗？'),
    onConfirm: async () => {
      const data = {
        status: 0,
      };
      try {
        await removalStage(apigwId.value, id, data);
        Message({
          message: t('下架成功'),
          theme: 'success',
        });
        // 获取网关列表
        await mitt.emit('get-stage-list');
        // 开启loading
      } catch (error) {
        console.error(error);
      }
    },
  });
};

// 访问地址
const getStageAddress = (name: string) => {
  const keys: any = {
    api_name: common.apigwName?.name,
    stage_name: name,
    resource_path: '',
  };

  let url = GLOBAL_CONFIG.STAGE_DOMAIN;
  for (const name in keys) {
    const reg = new RegExp(`{${name}}`);
    url = url?.replace(reg, keys[name]);
  }
  return url;
};

// 新建环境
const stageSidesliderRef = ref(null);
const handleAddStage = () => {
  stageSidesliderRef.value.handleShowSideslider('add');
};

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
  cursor: pointer;

  .title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 52px;
    border-bottom: 1px solid #DCDEE5;
    .title-lf {
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
      span {
        margin-right: 8px;
      }
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

    &.success {
      border: 1px solid #3FC06D;
      background: #E5F6EA;
    }

    &.unreleased {
      border: 1px solid #C4C6CC;
      background: #F0F1F5;
    }

    &.delist {
      border: 1px solid #C4C6CC;
      background: #F0F1F5;
    }

    &.failure {
      border: 1px solid #EA3636;
      background: #FFE6E6;
    }
  }
}</style>
