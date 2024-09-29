<template>
  <div class="ag-container">
    <div class="left">
      <div class="simple-side-nav">
        <div class="metedata p0" style="min-height: 60px;">
          <bk-select
            class="ag-apigw-select"
            size="large"
            v-model="curApigw.name"
            filterable
            :input-search="false"
            :clearable="false"
            :placeholder="t('请输入关键字')"
            @change="handleApigwChange">
            <bk-option
              v-for="option in apigwList"
              :key="option.id"
              :value="option.name"
              :label="option.name">
              <div>
                <span>{{option.name}}</span>
                <bk-tag theme="success" v-if="option.is_official">
                  {{ $t('官方') }}
                </bk-tag>
              </div>
            </bk-option>
          </bk-select>
        </div>
        <div class="component-list-box">
          <p
            :class="['span', { 'active': routeName === 'apigwAPIDetailIntro' }]"
            @click="handleShowIntro"
            style="cursor: pointer;">
            {{ $t('简介') }}
          </p>
          <div class="list-data" style="color: #979BA5;">
            {{ $t('环境') }}:
          </div>
          <!-- 环境切换时添加 query参数 ， 根据query参数切换对应的环境 -->
          <bk-select
            v-model="curStageId"
            style="width: 228px; margin: auto;"
            class="select-custom"
            :clearable="false"
            filterable
            behavior="simplicity"
            :input-search="false"
            @change="handleStageChange">
            <bk-option
              v-for="option in stageList"
              :key="option.id"
              :value="option.name"
              :label="option.name">
            </bk-option>
          </bk-select>
          <div class="search">
            <bk-input
              :placeholder="searchPlaceholder"
              type="search"
              clearable
              v-model="keyword">
            </bk-input>
          </div>
          <bk-collapse class="ml10 my-menu" v-model="activeName" v-if="Object.keys(resourceGroup).length">
            <template v-for="group of resourceGroup">
              <bk-collapse-panel
                v-if="group?.resources?.length"
                :name="group.labelName"
                :key="group.labelId">
                {{group.labelName}}
                <template #content>
                  <div>
                    <ul class="component-list list">
                      <li
                        v-for="component of group.resources"
                        :key="component.name"
                        :title="component.name"
                        :class="{ 'active': curComponentName === component.name }"
                        @click="handleShowDoc(component)">
                        <!-- eslint-disable-next-line vue/no-v-html -->
                        <p class="name" v-dompurify-html="hightlight(component.name)" v-bk-overflow-tips></p>
                        <!-- eslint-disable-next-line vue/no-v-html -->
                        <p class="label" v-dompurify-html="hightlight(component.description) || $t('暂无描述')" v-bk-overflow-tips>
                        </p>
                      </li>
                    </ul>
                  </div>
                </template>
              </bk-collapse-panel>
            </template>
          </bk-collapse>
          <template v-else-if="keyword">
            <TableEmpty
              :keyword="keyword"
              @clear-filter="keyword = ''"
            />
          </template>
        </div>
      </div>
    </div>

    <div class="right">
      <bk-loading
        :loading="mainContentLoading"
      >
        <router-view></router-view>
      </bk-loading>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { getGatewaysDetailsDocs, getApigwStagesDocs, getGatewaysDocs, getApigwResourcesDocs } from '@/http';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const curApigwId = ref<any>(0);
const curApigw = ref<any>({});
const resourceList = ref<any>([]);
const stageList = ref<any>([]);
const curStageId = ref<any>('');
const originResourceGroup = ref<any>({});
const curComponentName = ref<any>('');
const activeName = ref<any>([]);
const apigwList = ref<any>([]);
const keyword = ref<string>('');
const curResource = ref<any>({});
const mainContentLoading = ref<boolean>(false);

const searchPlaceholder = computed(() => {
  return t('在{resourceLength}个资源中搜索...', { resourceLength: resourceList.value?.length });
});

const routeName = computed(() => route.name);

const curGroup = computed(() => {
  for (const key of Object.keys(originResourceGroup.value)) {
    const cur = originResourceGroup.value[key];
    const match = cur?.resources?.find((item: any) => {
      return item.name === curComponentName.value;
    });
    if (match) {
      return cur;
    }
  }
  return null;
});

const resourceGroup = computed(() => {
  const group: any = {};
  let keys = Object.keys(originResourceGroup.value).sort();

  if (keys.includes('默认')) {
    const list = keys.filter(item => item !== '默认');
    keys = ['默认', ...list];
  }
  for (const key of keys) {
    const resources: any = [];
    const obj: any = {};
    const item = originResourceGroup.value[key];
    item?.resources?.forEach((resource: any) => {
      if ((resource.name || '').indexOf(keyword.value) > -1 || (resource.description || '').indexOf(keyword.value) > -1) {
        resources.push(resource);
      }
    });
    if (resources.length) {
      obj.labelId = item.labelId;
      obj.labelName = item.labelName;
      obj.resources = resources;
      group[key] = obj;
    }
  }
  return group;
});

const getApigwAPIDetail = async () => {
  try {
    const res = await getGatewaysDetailsDocs(curApigwId.value);
    curApigw.value = res;
  } catch (e) {
    console.log(e);
  }
};

const getApigwStages = async () => {
  if (stageList.value.length) {
    return;
  }
  try {
    const query = {
      limit: 10000,
      offset: 0,
    };
    const res = await getApigwStagesDocs(curApigwId.value, query);
    stageList.value = res;
    if (route.params.stage) {
      curStageId.value = route.params.stage;
    } else if (stageList.value?.length) {
      curStageId.value = stageList.value[0]?.name;
    } else {
      curStageId.value = '';
    }
    // query参数是的环境是否存在
    const queryStage = route.query.stage;
    // prod为默认环境
    const prodStage = stageList.value?.find((item: any) => item.name === 'prod');
    const resStage = prodStage ? prodStage.name : stageList.value[0]?.name;
    if (queryStage) {
      const stageDetils = stageList.value?.filter((item: any) => item.name === queryStage);
      if (stageDetils.length) {
        curStageId.value = queryStage;
      } else {
        curStageId.value = resStage;
        router.push({
          name: 'apigwAPIDetailIntro',
          params: {
            apigwId: curApigwId.value,
          },
          query: {
            stage: curStageId.value,
          },
        });
      }
    } else {
      curStageId.value = resStage;
      router.push({
        name: 'apigwAPIDetailIntro',
        params: {
          apigwId: curApigwId.value,
        },
        query: {
          stage: curStageId.value,
        },
      });
    }
    await getApigwResources();
  } catch (e) {
    console.log(e);
  }
};

const getApigwAPI = async () => {
  if (apigwList.value.length) {
    return;
  }
  const pageParams = {
    limit: 10000,
    offset: 0,
  };
  try {
    const res = await getGatewaysDocs('', pageParams);
    apigwList.value = res?.results;
  } catch (e) {
    console.log(e);
  }
};

const getApigwResources = async () => {
  if (stageList.value.length) {
    try {
      const query = {
        limit: 10000,
        offset: 0,
        stage_name: curStageId.value,
      };
      const res = await getApigwResourcesDocs(curApigwId.value, query);
      const group: any = {};
      const defaultItem: any = {
        labelId: 'default',
        labelName: t('默认'),
        resources: [],
      };
      resourceList.value = res;
      resourceList.value?.forEach((resource: any) => {
        const { labels } = resource;
        if (labels?.length) {
          labels.forEach((label: any) => {
            if (typeof label === 'object') {
              if (group[label.id]) {
                group[label.id]?.resources.push(resource);
              } else {
                if (group[label.name]) {
                  group[label.name]?.resources.push(resource);
                } else {
                  const obj = {
                    labelId: label.id,
                    labelName: label.name,
                    resources: [resource],
                  };
                  group[label.name] = obj;
                }
              }
            } else {
              if (group[label]) {
                group[label]?.resources?.push(resource);
              } else {
                const obj = {
                  labelId: label,
                  labelName: label,
                  resources: [resource],
                };
                group[label] = obj;
              }
            }
          });
        } else {
          defaultItem.resources.push(resource);
        }
      });
      if (defaultItem.resources.length) {
        group['默认'] = defaultItem;
      }
      originResourceGroup.value = group;
    } catch (e) {
      console.log(e);
    }
  } else {
    originResourceGroup.value = {};
    resourceList.value = [];
  }
};

const reset = () => {
  curComponentName.value = '';
};

const handleShowDoc = (resource: any) => {
  curResource.value = resource;
  curComponentName.value = resource.name;

  router.push({
    name: 'apigwAPIDetailDoc',
    params: {
      apigwId: curApigwId.value,
      stage: curStageId.value,
      resourceId: resource.name,
    },
    query: {
      stage: curStageId.value,
    },
  });
};

const handleShowIntro = () => {
  curComponentName.value = '';
  router.push({
    name: 'apigwAPIDetailIntro',
  });
};

const hightlight = (value: string) => {
  if (keyword.value) {
    return value.replace(new RegExp(`(${keyword.value})`), '<em class="ag-keyword">$1</em>');
  }
  return value;
};

const handleApigwChange = async (data: string) => {
  reset();
  stageList.value = [];
  curApigwId.value = data;
  await getApigwStages();
  router.push({
    name: 'apigwAPIDetailIntro',
    params: {
      apigwId: data,
    },
    query: {
      stage: curStageId.value,
    },
  });
};

const handleStageChange = async () => {
  reset();
  await getApigwResources();
  const match = resourceList.value?.find((resource: any) => curResource.value?.name === resource.name);
  if (match) {
    handleShowDoc(match);
  } else {
    handleShowIntro();
  }
  router.push({
    query: { stage: curStageId.value },
  });
};

const init = async () => {
  const curRoute = route as any;
  const routeParams = route.params;
  curApigwId.value = routeParams.apigwId;
  curComponentName.value = routeParams.resourceId;
  // 回到页头
  const container = document.documentElement || document.body;
  container.scrollTo({
    top: 0,
    behavior: 'smooth',
  });
  getApigwAPI();
  if (['apigwAPIDetailIntro', 'apigwAPIDetailDoc'].includes(curRoute.name)) {
    await getApigwStages();
    return;
  }
  getApigwAPIDetail();
};

watch(
  () => keyword.value,
  (val) => {
    const keys = Object.keys(resourceGroup.value);
    if (val) {
      activeName.value = keys;
    } else if (curGroup.value) {
      activeName.value = [curGroup.value?.labelName];
    } else {
      activeName.value = [keys[0]];
    }
  },
);

watch(
  () => curGroup.value,
  () => {
    if (curGroup.value) {
      activeName.value = [curGroup.value?.labelName];
    }
  },
);

watch(
  () => resourceGroup.value,
  () => {
    if (!activeName.value?.length) {
      activeName.value = [Object.keys(resourceGroup.value)[0]];
    }
  },
);

watch(
  () => route,
  (payload: any) => {
    if (payload.params?.apigwId) {
      curApigw.value = { name: payload.params?.apigwId };
      init();
    }
  },
  { immediate: true, deep: true },
);

</script>

<style lang="scss" scoped>
  @import './detail.css';
</style>
