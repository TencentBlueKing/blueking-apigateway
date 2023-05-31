<template>
  <div class="ag-container">
    <div class="left">
      <div class="simple-side-nav">
        <div class="metedata" style="height: 65px;">
          <strong class="name">{{curSystem.description || '--'}}</strong>
          <p class="desc">{{curSystem.name}}</p>
          <i class="more ag-doc-icon doc-menu apigateway-icon icon-ag-menu" v-bk-tooltips.top="$t('所有系统')" @click="handleTogglePanel"></i>

          <div
            :class="`version-logo ${curVersion}`"
            :style="{ backgroundImage: `url(${versionLogoMap[curVersionIndex % 4].logo})` }">
            <em :style="{ backgroundColor: `${versionLogoMap[curVersionIndex % 4].color}` }">
              <span style="transform: scale(0.8); display: inline-block;">{{curBoardLabel}}</span>
            </em>
          </div>
        </div>
        <div class="component-list-box">
          <p :class="['span', { 'active': routeName === 'ComponentAPIDetailIntro' }]" @click="handleShowIntro"> {{ $t('简介') }} </p>
          <div class="list-data">
            {{ $t('API 列表') }}
            <span class="ag-badge">{{curComponentList.length}}</span>
          </div>
          <div class="search">
            <bk-input :placeholder="$t('请输入API名称')" right-icon="bk-icon icon-search" clearable v-model="keyword"></bk-input>
          </div>
          <ul class="component-list" v-if="curComponentList.length">
            <li
              :class="{ 'active': curComponentName === component.name }"
              v-for="component of curComponentList"
              :key="component.id"
              @click="handleShowDoc(component)">
              <p class="name" v-html="hightlight(component.name)" v-bk-overflow-tips></p>
              <p class="label" v-html="hightlight(component.description)" v-bk-overflow-tips></p>
            </li>
          </ul>
          <template v-else-if="keyword">
            <table-empty
              :keyword="keyword"
              @clear-filter="keyword = ''"
            />
          </template>
        </div>
      </div>

      <div class="nav-panel" v-if="isNavPanelShow" v-bk-clickoutside="handleTogglePanel">
        <div class="version-panel">
          <bk-dropdown-menu ref="dropdown" style="margin: 16px;">
            <p class="version-name" slot="dropdown-trigger">
              <svg aria-hidden="true" class="category-icon vm">
                <use :xlink:href="`#doc-icon${curVersionData.logoIndex % 4}`"></use>
              </svg>
              <strong class="vm">{{curVersionData.board_label}}</strong>
              <i class="ag-doc-icon doc-down-shape f12 apigateway-icon icon-ag-down-shape"></i>
            </p>
            <ul class="bk-dropdown-list" slot="dropdown-content" style="width: 250px;">
              <li v-for="(component) of componentList" :key="component.board">
                <a href="javascript:;" @click="handleSwitchVersion(component)">{{component.board_label}}</a>
              </li>
            </ul>
          </bk-dropdown-menu>

          <bk-input class="searcher" :placeholder="$t('请输入系统名称')" clearable v-model="panelKeyword"></bk-input>
          <div class="panel-container">
            <template v-if="filterData.categories.length">
              <div class="ag-card" v-for="(category, index) of filterData.categories" :key="index">
                <p class="card-title" :id="`${curVersionData.board_label}_${category.name}`">{{category.name}} <span class="total">({{category.systems.length}})</span></p>
                <div class="card-content">
                  <ul class="systems">
                    <li v-for="item of category.systems" :key="item.name">
                      <router-link :to="{ name: 'ComponentAPIDetailIntro', params: { version: curVersionData.board, category: category.name, id: item.name } }">
                        <span v-html="hightlight(item.description, 'panel')" @click="isNavPanelShow = false"></span>
                      </router-link>
                      <p class="desc">
                        <span v-html="hightlight(item.name, 'panel')"></span>
                      </p>
                    </li>
                  </ul>
                </div>
              </div>
            </template>
            <template v-else-if="panelKeyword">
              <table-empty
                :keyword="keyword"
                @clear-filter="keyword = ''"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="right">
      <loader :is-loading="mainContentLoading" :loader="'doc-loader'" :has-border="false" :height="1200" background-color="#FAFBFD">
        <router-view :key="$route.path"></router-view>
      </loader>
    </div>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import showdown from 'showdown'
  import 'mavon-editor/dist/css/index.css'
  import MarkdownIt from 'markdown-it'
  import Clipboard from 'clipboard'
  import { slugify } from 'transliteration'
  import rst2mdown from 'rst2mdown'
  import loader from '@/components/loader'
  import logo1 from '@/images/1.svg'
  import logo2 from '@/images/2.svg'
  import logo3 from '@/images/3.svg'
  import logo4 from '@/images/4.svg'

  export default {
    components: {
      loader
    },
    data () {
      return {
        curBoardLabel: '',
        curVersion: '',
        curCatefory: '',
        curSystemName: '',
        curComponentName: '',
        renderHtmlIndex: 0,
        keyword: '',
        panelKeyword: '',
        curComponent: {
          id: '',
          content: '',
          innerHtml: '',
          markdownHtml: ''
        },
        componentList: [],
        originComponentList: [],
        isNavPanelShow: false,
        curSystem: {
          name: '',
          label: ''
        },
        curVersionData: {
          board: '',
          board_label: '',
          categories: []
        },
        componentNavList: []
      }
    },
    computed: {
      routeName () {
        return this.$route.name
      },
      path () {
        return this.$route.fullpath
      },
      mainContentLoading () {
        return this.$store.state.mainContentLoading
      },
      curComponentList () {
        return this.originComponentList.filter(item => {
          return item.name.indexOf(this.keyword) > -1 || item.description.indexOf(this.keyword) > -1
        })
      },
      versionLogoMap () {
        return [
          {
            logo: logo1,
            color: '#3b83ff'
          },
          {
            logo: logo3,
            color: '#ff9700'
          },
          {
            logo: logo2,
            color: '#3babfe'
          },
          {
            logo: logo4,
            color: '#2dca56'
          }
        ]
      },
      curVersionIndex () {
        const match = this.componentList.find(item => item.board === this.curVersion)
        return match ? match.logoIndex : 0
      },
      filterData () {
        const data = {
          board: '',
          board_label: '',
          categories: []
        }
        this.curVersionData.categories.forEach(category => {
          const list = []
          const obj = { ...category }
          const keyword = this.panelKeyword.toLowerCase()
          category.systems.forEach(system => {
            if (system.description.toLowerCase().indexOf(keyword) > -1 || system.name.toLowerCase().indexOf(keyword) > -1) {
              list.push(system)
            }
          })

          if (list.length) {
            obj.systems = list
            data.categories.push(obj)
          }
        })
        return data
      }
    },
    watch: {
      '$route' () {
        // 回到页头
        const container = document.documentElement || document.body
        container.scrollTo({
          top: 0,
          behavior: 'smooth'
        })
      }
    },
    created () {
      // component-api/:version/:category/:id/detail'
      const routeParams = this.$route.params
      this.curVersion = routeParams.version
      this.curCatefory = routeParams.category
      this.curSystemName = routeParams.id
      this.curComponentName = routeParams.componentId
      this.init()
    },
    methods: {
      init () {
        this.$store.commit('setMainContentLoading', true)
        Promise.all([
          this.getSystemDetail(),
          this.getSystemComponents(),
          this.getComponentAPI()
        ]).finally(() => {
          this.$store.commit('setMainContentLoading', false)
        })
        // 回到页头
        const container = document.documentElement || document.body
        container.scrollTo({
          top: 0,
          behavior: 'smooth'
        })
      },

      async getSystemDetail () {
        try {
          const res = await this.$store.dispatch('esb/getSystemDetail', {
            version: this.curVersion,
            systemName: this.curSystemName
          })
          this.curSystem = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getComponentAPI () {
        try {
          const res = await this.$store.dispatch('esb/getComponentAPI')
          this.componentList = res.data
          this.componentList.forEach((item, index) => {
            item.logoIndex = index
          })
          if (this.componentList.length) {
            const match = this.componentList.find(item => item.board === this.curVersion)
            this.curVersionData = match || this.componentList[0]
            this.curBoardLabel = this.curVersionData.board_label
          }
        } catch (e) {
          console.error(e)
        }
      },

      async getSystemComponents () {
        try {
          const { data } = await this.$store.dispatch('esb/getSystemComponents', {
            version: this.curVersion,
            systemName: this.curSystemName
          })
          this.originComponentList = data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleTogglePanel () {
        clearTimeout(this.toggleTimer)
        this.toggleTimer = setTimeout(() => {
          this.isNavPanelShow = !this.isNavPanelShow
        }, 100)
      },

      handleShowIntro () {
        this.$router.push({
          name: 'ComponentAPIDetailIntro'
        })
      },

      handleShowDoc (component) {
        this.curComponent = component
        this.curComponentName = this.curComponent.name
        this.$router.push({
          name: 'ComponentAPIDetailDoc',
          params: {
            componentId: component.name
          }
        })
      },

      async getSystemComponentDoc (id) {
        try {
          const res = await this.$store.dispatch('esb/getSystemComponentDoc', {
            version: this.curVersion,
            systemName: this.curSystemName,
            componentId: this.curComponentName
          })
          const converter = new showdown.Converter()
          let content = res.data.content
          this.curComponent.content = content
          this.curComponent.innerHtml = converter.makeHtml(content)
          if (res.data.type === 'rst') {
            content = rst2mdown(content)
          }
          this.initMarkdownHtml(content)
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      initMarkdownHtml (content) {
        const md = new MarkdownIt({
          linkify: false
        })
        this.curComponent.markdownHtml = md.render(content)

        this.renderHtmlIndex++
                
        this.$nextTick(() => {
          const markdownDom = document.getElementById('markdown')
          // 右侧导航
          const titles = markdownDom.querySelectorAll('h3')
          this.componentNavList = []
          titles.forEach(item => {
            const name = String(item.innerText).trim()
            const id = slugify(name)
            this.componentNavList.push({
              id: id,
              name: name
            })
            item.id = `${this.curComponentName}?${id}`
          })

          // 复制代码
          markdownDom.querySelectorAll('a').forEach(item => {
            item.target = '_blank'
          })
          markdownDom.querySelectorAll('pre').forEach(item => {
            const btn = document.createElement('button')
            const codeBox = document.createElement('div')
            const code = item.querySelector('code').innerText
            btn.className = 'ag-copy-btn'
            codeBox.className = 'code-box'
            btn.innerHTML = '<span :title="$t(`复制`)"><i class="bk-icon icon-clipboard mr5"></i></span>'
            btn.setAttribute('data-clipboard-text', code)
            item.appendChild(btn)
            codeBox.appendChild(item.querySelector('code'))
            item.appendChild(codeBox)
          })
        })

        if (this.clipboardInstance && this.clipboardInstance.off) {
          this.clipboardInstance.off('success')
        }
        setTimeout(() => {
          this.clipboardInstance = new Clipboard('.ag-copy-btn')
          this.clipboardInstance.on('success', e => {
            this.$bkMessage({
              width: 100,
              limit: 1,
              theme: 'success',
              message: this.$t('复制成功')
            })
          })
        }, 2000)
      },

      handleSwitchVersion (component) {
        this.curVersionData = component
        this.$refs.dropdown.hide()
      },

      hightlight (value, type) {
        const keyword = type === 'panel' ? this.panelKeyword : this.keyword
        if (keyword) {
          return value.replace(new RegExp(`(${keyword})`), '<em class="ag-keyword">$1</em>')
        } else {
          return value
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './detail.css';
</style>
