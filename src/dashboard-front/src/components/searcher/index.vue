<template>
  <div class="searcher" v-if="versionList.length">
    <bk-dropdown-menu ref="dropdown">
      <div class="dropdown-trigger-btn" slot="dropdown-trigger">
        <span>{{curVersion.board_label}}</span>
        <i class="ag-doc-icon doc-down-shape apigateway-icon icon-ag-down-shape"></i>
      </div>
      <ul class="bk-dropdown-list" slot="dropdown-content">
        <li v-for="version of versionList" :key="version.board">
          <a href="javascript:;" @click="triggerHandler(version)" class="f14">{{version.board_label}}</a>
        </li>
      </ul>
    </bk-dropdown-menu>
    <div class="input-wrapper bk-dropdown-menu search-result-box">
      <input type="text" style="width: 400px;" v-model="keyword" class="input" :placeholder="$t('请输入API名称')" @input="searchAPI" @keydown="keyupHandle">
      <div v-bk-clickoutside="handleHidePanel" class="bk-dropdown-content is-show left-align" style="width: 300px; min-width: 300px; top: 43px; max-height: 550px; overflow: auto;" v-if="keyword">
        <ul ref="searchListContainer" id="result-list" class="bk-dropdown-list" :style="{ 'max-height': `${contentMaxHeight}px` }" v-bkloading="{ isLoading: isLoading, opacity: 1 }">
          <template v-if="resultList.length">
            <li v-for="(item, index) of resultList" :key="index" :class="selectIndex === index ? 'cur' : ''" @click="handleShowDoc(item)">
              <a href="javascript:;">
                <p class="name">
                  <strong class="mr5" v-html="hightlightSystemName(item)"></strong>
                  <span v-html="hightlight(item)"></span>
                </p>
                <p class="desc">{{item.description || $t('暂无描述')}}</p>
              </a>
            </li>
          </template>
          <template v-else>
            <li>
              <a href="javascript:;" style="text-align: center; line-height: 41px;">
                {{ $t('没有找到相应记录') }}
              </a>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    props: {
      versionList: {
        type: Array,
        default () {
          return []
        }
      }
    },
    data () {
      return {
        contentMaxHeight: 410,
        selectIndex: 0,
        isLoading: false,
        keyword: '',
        resultList: [],
        curVersion: {
          board: '',
          board_label: ''
        }
      }
    },
    watch: {
      versionList () {
        if (this.versionList.length) {
          this.curVersion = this.versionList[0]
        }
      }
    },
    methods: {
      hightlight (node) {
        if (this.keyword) {
          return node.name.replace(new RegExp(`(${this.keyword})`), '<em class="keyword">$1</em>')
        } else {
          return node.name
        }
      },
      hightlightSystemName (node) {
        if (this.keyword) {
          return node.system_name.replace(new RegExp(`(${this.keyword.toUpperCase()})`), '<em class="keyword">$1</em>')
        } else {
          return node.system_name
        }
      },
      triggerHandler (version) {
        this.curVersion = version
        this.$refs.dropdown.hide()
      },

      handleHidePanel () {
        this.keyword = ''
      },

      handleShowDoc (component) {
        this.$router.push({
          name: 'ComponentAPIDetailDoc',
          params: {
            version: this.curVersion.board,
            id: component.system_name,
            componentId: component.name
          }
        })
      },

      async searchAPI () {
        try {
          this.isLoading = true
          this.selectIndex = 0
          const keyword = this.keyword
          const version = this.curVersion.board
          const res = await this.$store.dispatch('esb/searchAPI', {
            version,
            keyword
          })
          this.resultList = res.data
        } catch (e) {
          console.error(e)
        } finally {
          this.isLoading = false
        }
      },

      /**
       * 文本框 keyup
       *
       * @param {Object} e 事件对象
       */
      keyupHandle (e) {
        const keyCode = e.keyCode
        const length = this.resultList.length

        switch (keyCode) {
          // 上
          case 38:
            e.preventDefault()
            if (this.selectIndex === -1 || this.selectIndex === 0) {
              this.selectIndex = length - 1
              this.$refs.searchListContainer.scrollTop = this.$refs.searchListContainer.scrollHeight
            } else {
              this.selectIndex--
              this.$nextTick(() => {
                const curSelectNode = this.$refs.searchListContainer.querySelector('li.cur')
                const offsetTop = curSelectNode.offsetTop
                if (offsetTop < this.$refs.searchListContainer.scrollTop) {
                  this.$refs.searchListContainer.scrollTop -= 41
                }
              })
            }
            break
          // 下
          case 40:
            e.preventDefault()
            if (this.selectIndex < length - 1) {
              this.selectIndex++
              this.$nextTick(() => {
                const curSelectNode = this.$refs.searchListContainer.querySelector('li.cur')
                const offsetTop = curSelectNode.offsetTop
                // this.$refs.searchListContainer 上下各有 6px 的 padding
                if (offsetTop > this.contentMaxHeight - 2 * 6) {
                  // 每一个 item 是 41px height
                  this.$refs.searchListContainer.scrollTop += 41
                }
              })
            } else {
              this.selectIndex = 0
              this.$refs.searchListContainer.scrollTop = 0
            }
            break
          case 13:
            e.preventDefault()
            if (this.resultList[this.selectIndex]) {
              this.handleShowDoc(this.resultList[this.selectIndex], true)
            }
            break
          default:
            break
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .searcher {
        width: 700px;
        height: 40px;
        background: #FFF;
        border-radius: 2px;
        position: inherit;
        display: flex;

        .dropdown-trigger-btn {
            height: 40px;
            line-height: 40px;
            padding: 0 15px;
            color: #63656E;
            font-size: 14px;
        }

        .input-wrapper {
            flex: 1;
            line-height: 40px;
        }
        .input {
            outline: none;
            border: none;
            line-height: 16px;
            font-size: 14px;
            background: transparent;
            padding-left: 20px;
            border-left: 1px solid #c4c6cc;
            position: relative;
        }
    }

    .search-result-box .bk-dropdown-list>li.cur>a {
        background-color: #eaf3ff;
        color: #3a84ff;
    }
    .search-result-box .bk-dropdown-list>li>a {
        height: auto;
        line-height: 1;
        padding: 6px 10px;
        margin-bottom: 9px;

        .name {
            margin-bottom: 5px;
            color: #63656E;
            display: block;

            /deep/ .keyword {
                color: #3a84ff;
                font-style: normal;
            }
        }

        .desc {
            color: #C4C6CC;
            max-width: 290px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    }
</style>
