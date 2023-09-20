<template>
  <div class="bk-keyer">
    <div class="biz-keys-list mb10">
      <div class="label" v-if="label">{{label}}</div>

      <div class="values">
        <template v-if="list.length">
          <div class="biz-key-item" v-for="(keyItem, index) in list" :key="index">
            <bk-form
              :ref="`key-${index}`"
              style="width: 190px; display: inline-block;"
              :label-width="0"
              :model="keyItem">
              <bk-form-item
                :rules="rules.key"
                :property="'key'"
                :error-display-type="'normal'">
                <bk-input
                  type="text"
                  :placeholder="keyPlaceholder || $t('键')"
                  v-model="keyItem.key"
                  @keyup="valueChange">
                </bk-input>
              </bk-form-item>
            </bk-form>
            <bk-button class="ml5 mr5 ag-icon-btn" @click.stop.prevent="addKey">
              <i class="apigateway-icon icon-ag-plus"></i>
            </bk-button>
            <bk-button class="ag-icon-btn" @click.stop.prevent="removeKey(keyItem, index)">
              <i class="apigateway-icon icon-ag-minus"></i>
            </bk-button>
          </div>
        </template>
        <div v-else>
          <bk-button class="mr5 ag-icon-btn" @click.stop.prevent="addKey">
            <i class="apigateway-icon icon-ag-plus"></i>
          </bk-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import { bkForm, bkFormItem, bkInput, bkButton } from 'bk-magic-vue'

  export default {
    components: {
      bkForm,
      bkFormItem,
      bkInput,
      bkButton
    },
    props: {
      value: {
        type: Array,
        default () {
          return []
        }
      },
      tip: {
        type: String,
        default: ''
      },
      keyPlaceholder: {
        type: String,
        default: ''
      },
      label: {
        type: String,
        default: ''
      }
    },
    data () {
      return {
        itemIndex: 0,
        list: [],
        rules: {
          key: [
            // {
            //     required: true,
            //     message: '必填项',
            //     trigger: 'blur'
            // },
            // {
            //     regex: /^[a-zA-Z0-9_]*$/,
            //     message: '变量名由英文字母、数字、_ 组成',
            //     trigger: 'blur'
            // },
            {
              regex: /^[a-zA-Z0-9-]+$/,
              message: this.$t('键由英文字母、数字、连接符（-）组成'),
              trigger: 'blur'
            },
            {
              validator: (value) => {
                const matches = this.list.filter(item => value && (item.key === value))
                if (matches.length < 2) {
                  return true
                }
                return false
              },
              message: this.$t('键不允许重复'),
              trigger: 'blur'
            }
          ]
        }
      }
    },
    watch: {
      value: {
        immediate: true,
        handler (value) {
          this.list.splice(0, this.list.length, ...[])
          for (const key of value) {
            this.list.push({
              id: this.itemIndex,
              key: key
            })
            this.itemIndex++
          }
        }
      }
    },
    methods: {
      update () {
        const data = this.list.map(item => {
          return item.key
        })
        this.$emit('input', data)
      },
      getValue () {
        const result = []
        this.list.filter(item => {
          if (item.key) {
            result.push(item.key)
          }
        })
        // return [...new Set(result)]
        return result
      },
      addKey () {
        const params = {
          id: this.itemIndex,
          key: ''
        }
        this.itemIndex++
        this.list.push(params)
      },
      removeKey (item, index) {
        this.list.splice(index, 1)
        this.validate()
        this.update()
      },
      valueChange () {
        this.$nextTick(() => {
          this.update()
        })
      },
      validate () {
        this.list.forEach((item, index) => {
          this.$refs[`key-${index}`][0].validate()
        })
      }
    }
  }
</script>

<style scoped lang="postcss">
    @import '../../css/variable.css';

    .bk-keyer {
        margin-bottom: 10px;
    }
    .biz-key-item {
        display: flex;
        width: 100%;
        margin-bottom: 5px;

        /deep/ .bk-label {
            display: none;
        }
    }
    .biz-keys-list {
        display: flex;

        .label {
            font-size: 14px;
            font-weight: bold;
            color: #313238;
            width: 50px;
        }
        .operator {
            width: 20px;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            display: inline-block;
            color: #313238;
            vertical-align: middle;
        }
    }
    .biz-keys-list .action-btn {
        width: auto;
        padding: 0;
        margin-left: 5px;
        &.disabled {
            cursor: default;
            color: #ddd !important;
            border-color: #ddd !important;
            .bk-icon {
                color: #ddd !important;
                border-color: #ddd !important;
            }
        }
        &:hover {
            color: $primaryColor;
            border-color: $primaryColor;
            .bk-icon {
                color: $primaryColor;
                border-color: $primaryColor;
            }
        }
    }
    .is-danger {
        color: $dangerColor;
    }
    .bk-input-box {
        display: inline-block;
        position: relative;
    }
</style>
