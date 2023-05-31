<template>
  <div class="chat-box">
    <a href="javascript: void(0);" class="support-btn" @click="handleShowDialog">
      <i class="ag-doc-icon doc-qw f16 apigateway-icon icon-ag-qw" style="margin-right: 3px;"></i> {{ $t('一键拉群') }}
    </a>

    <bk-dialog
      width="600"
      v-model="chatDialog.visible"
      header-position="left"
      theme="primary"
      :mask-close="false"
      :title="$t('一键拉群')"
      @confirm="handleConfirm"
      @cancel="handleCancel">
      <div class="header">
        <div class="icon">
          <i class="ag-doc-icon doc-qw apigateway-icon icon-ag-qw"></i>
        </div>
        <div class="desc">
          <p> {{ $t('一键拉群功能') }} </p>
          <p> {{ $t('可以通过企业微信将需求的相关人员邀请到一个群里进行讨论') }} </p>
        </div>
      </div>
      <bk-member-selector class="chat-selector" :key="renderKey" v-model="userlist" :placeholder="$t('请选择群成员')"></bk-member-selector>
    </bk-dialog>
  </div>
</template>

<script>
  export default {
    components: {
      'bk-member-selector': () => {
        return import('@/components/user/member-selector/member-selector.vue')
      }
    },
    props: {
      name: {
        type: String,
        default: ''
      },
      owner: {
        type: String,
        default: ''
      },
      defaultUserList: {
        type: Array,
        default: () => {
          return []
        }
      },
      content: {
        type: String,
        default: ''
      },
      isQuery: {
        type: Boolean,
        default: false
      }
            
    },
    data () {
      return {
        renderKey: 0,
        chatDialog: {
          visible: false
        },
        userlist: [...this.defaultUserList]
      }
    },
    computed: {
      curStage () {
        return this.$store.state.apigw.curStage
      }
    },
    watch: {
      defaultUserList () {
        this.defaultUserList.forEach(user => {
          if (!this.userlist.includes(user)) {
            this.userlist.push(user)
          }
        })
        this.renderKey++
      }
    },
    methods: {
      handleShowDialog () {
        this.chatDialog.visible = true
      },
            
      async handleConfirm () {
        let contentStr = this.content
        if (this.isQuery) {
          const qeury = contentStr.split('?')[1]
          if (!qeury) {
            contentStr = `${contentStr}?stage=${this.curStage}`
          }
        }
        if (!this.userlist.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择群成员')
          })
          return false
        }
        // 创建群
        const res = await this.$store.dispatch('docs/createChat', {
          appCode: 'create-chat',
          params: {
            name: this.name,
            owner: this.owner,
            userlist: [...this.userlist, this.owner]
          }
        })
        // 发送消息
        const chartId = res.data.chatid
        await this.$store.dispatch('sendChat', {
          appCode: 'create-chat',
          params: {
            chatid: chartId,
            msgtype: 'text',
            text: {
              content: contentStr
            }
          }
        })
        this.$bkMessage({
          theme: 'success',
          message: this.$t('创建成功')
        })
      },

      handleCancel () {
        this.chatDialog.visible = false
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .chat-box {
        display: inline-block;
    }
    /deep/ .chat-selector {
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
