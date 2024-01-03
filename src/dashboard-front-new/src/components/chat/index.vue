<template>
  <div class="chat-box" v-if="allowCreateAppChat">
    <a href="javascript: void(0);" class="support-btn" @click="handleShowDialog">
      <i class="ag-doc-icon doc-qw f16 apigateway-icon icon-ag-qw" style="margin-right: 3px;"></i> {{ $t('一键拉群') }}
    </a>

    <bk-dialog
      width="600"
      v-model:is-show="chatDialog.visible"
      header-align="left"
      theme="primary"
      :quick-close="false"
      :title="$t('一键拉群')"
      @confirm="handleConfirm"
      @closed="handleCancel">
      <div class="chat-dialog">
        <div class="header">
          <div class="icon">
            <i class="ag-doc-icon doc-qw apigateway-icon icon-ag-qw"></i>
          </div>
          <div class="desc">
            <p> {{ $t('一键拉群功能') }} </p>
            <p> {{ $t('可以通过企业微信将需求的相关人员邀请到一个群里进行讨论') }} </p>
          </div>
        </div>
        <bk-input
          :placeholder="$t('请输入群成员')"
          v-model="userlist"
          :key="renderKey"
          class="chat-selector"
        />
      </div>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { createChat, sendChat, getFeatures } from '@/http';
import { useStage } from '@/store';

const stageStore = useStage();
const { t } = useI18n();

const props = defineProps({
  name: {
    type: String,
    default: '',
  },
  owner: {
    type: String,
    default: '',
  },
  defaultUserList: {
    type: Array,
    default: () => {
      return [];
    },
  },
  content: {
    type: String,
    default: '',
  },
  isQuery: {
    type: Boolean,
    default: false,
  },
});

const renderKey = ref<number>(0);
const chatDialog = reactive<any>({
  visible: false,
});
const userlist = ref([...props.defaultUserList]);
const allowCreateAppChat = ref(false);

const curStage = computed(() => stageStore.curStageData?.id);

const handleShowDialog = () => {
  chatDialog.visible = true;
};

const handleCancel = () => {
  chatDialog.visible = false;
};

const handleConfirm = async () => {
  let contentStr = props.content;
  if (props.isQuery) {
    const qeury = contentStr.split('?')[1];
    if (!qeury) {
      contentStr = `${contentStr}?stage=${curStage.value}`;
    }
  }
  if (!userlist.value?.length) {
    Message({
      theme: 'error',
      message: t('请选择群成员'),
    });
    return false;
  }

  try {
    // 创建群
    const body = {
      bk_app_code: 'create-chat',
      name: props.name,
      owner: props.owner,
      userlist: [...userlist.value, props.owner],
    };
    const res = await createChat(body);
    // 发送消息
    const chartId = res.data.chatid;

    const data = {
      bk_app_code: 'create-chat',
      chatid: chartId,
      msgtype: 'text',
      text: {
        content: contentStr,
      },
    };
    await sendChat(data);
    Message({
      theme: 'success',
      message: t('创建成功'),
    });
  } catch (e) {
    console.log(e);
  }
};

const fetchFeature = async () => {
  try {
    const params = {
      limit: 10000,
      offset: 0,
    };
    const res = await getFeatures(params);
    allowCreateAppChat.value = res?.ALLOW_CREATE_APPCHAT;
  } catch (e) {
    console.log(e);
  }
};

watch(
  () => props.defaultUserList,
  () => {
    props.defaultUserList?.forEach((user: any) => {
      if (!userlist.value?.includes(user)) {
        userlist.value.push(user);
      }
    });
    renderKey.value += 1;
  },
);

onMounted(() => {
  fetchFeature();
});

</script>

<style lang="scss" scoped>
.chat-dialog {
  padding-bottom: 32px;
}
.chat-box {
  display: inline-block;
}
:deep(.chat-selector) {
  .bk-tag-input {
    min-height: 100px;
  }

  .bk-tag-selector .bk-tag-input {
    align-items: flex-start;
  }

  .clear-icon {
    display: none;
  }
}
.support-btn {
  font-size: 12px;
  color: #3A84FF;
  display: inline-block;
}

.header {
  display: flex;
  margin-bottom: 10px;

  .icon {
    width: 60px;
    text-align: left;
    font-size: 50px;
    line-height: 1;
  }

  .desc {
    flex: 1;
    padding-top: 10px;

    p {
      font-size: 14px;
      line-height: 1;
      margin-bottom: 10px;
    }
  }
}
</style>
