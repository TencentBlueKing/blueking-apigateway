<template>
  <div class="ag-container">
    <div class="left">
      <div class="simple-side-nav">
        <div class="metedata p0" style="min-height: 60px;">
          <bk-select
            class="ag-apigw-select"
            v-model="curApigw.name"
            :searchable="true"
            :clearable="false"
            @selected="handleApigwChange">
            <bk-option v-for="option in apigwList"
              :key="option.id"
              :id="option.name"
              :name="option.name">
              <span>{{option.name}}</span>
              <span class="ag-tag success ml5" v-if="option.name_prefix === '[官方]'"> {{ $t('官方') }} </span>
            </bk-option>
          </bk-select>
          <!-- <strong class="name">{{curApigw.name || '--'}}</strong> -->
          <!-- <p class="desc">{{curApigw.description}}</p> -->
        </div>
        <div class="component-list-box">
          <p :class="['span', { 'active': routeName === 'apigwAPIDetailIntro' }]" @click="handleShowIntro" style="cursor: pointer;"> {{ $t('简介') }} </p>
          <div class="list-data" style="color: #979BA5;">
            {{ $t('环境') }}:
          </div>
          <!-- 环境切换时添加 query参数 ， 根据query参数切换对应的环境 -->
          <bk-select
            v-model="curStageId"
            style="width: 228px; margin: auto;"
            ext-cls="select-custom"
            ext-popover-cls="select-popover-custom"
            :clearable="false"
            :searchable="true"
            @selected="handleStageChange">
            <bk-option v-for="option in stageList"
              :key="option.id"
              :id="option.name"
              :name="option.name">
            </bk-option>
          </bk-select>
          <div class="search">
            <bk-input :placeholder="searchPlaceholder" right-icon="bk-icon icon-search" clearable v-model="keyword"></bk-input>
          </div>
          <bk-collapse class="ml10 my-menu" v-model="activeName" v-if="Object.keys(resourceGroup).length">
            <bk-collapse-item v-if="group.resources.length" :name="group.labelName" v-for="group of resourceGroup" :key="group.labelId">
              <i class="ag-doc-icon doc-down-shape custom-icon apigateway-icon icon-ag-down-shape"></i>{{group.labelName}}
              <div slot="content">
                <ul class="component-list list">
                  <li
                    :title="component.name"
                    :class="{ 'active': curComponentName === component.name }"
                    v-for="component of group.resources"
                    :key="component.name"
                    @click="handleShowDoc(component)">
                    <p class="name" v-html="hightlight(component.name)" v-bk-overflow-tips></p>
                    <p class="label" v-html="hightlight(component.description) || $t('暂无描述')" v-bk-overflow-tips></p>
                  </li>
                </ul>
              </div>
            </bk-collapse-item>
          </bk-collapse>

          <template v-else-if="keyword">
            <table-empty
              :keyword="keyword"
              @clear-filter="keyword = ''"
            />
          </template>
        </div>
      </div>
    </div>

    <div class="right">
      <loader :is-loading="mainContentLoading" :loader="'doc-loader'" :has-border="false" :height="900" background-color="#FAFBFD">
        <router-view></router-view>
      </loader>
    </div>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import loader from '@/components/loader'
  // import Clipboard from 'clipboard'

  export default {
    components: {
      loader
    },
    data () {
      return {
        curApigwId: 0,
        curApigw: {},
        resourceList: [],
        stageList: [],
        curStageId: '',
        originResourceGroup: {},
        curComponentName: '',
        activeName: [],
        apigwList: [],
        keyword: '',
        curResource: {}
      }
    },
    computed: {
      searchPlaceholder () {
        return this.$t(`在{resourceLength}个资源中搜索...`, { resourceLength: this.resourceList.length })
      },
      routeName () {
        return this.$route.name
      },
      mainContentLoading () {
        return this.$store.state.mainContentLoading
      },
      curGroup () {
        for (const key in this.originResourceGroup) {
          const cur = this.originResourceGroup[key]
          const match = cur.resources.find(item => {
            return item.name === this.curComponentName
          })
          if (match) {
            return cur
          }
        }
        return null
      },
      resourceGroup () {
        const group = {}
        let keys = Object.keys(this.originResourceGroup).sort()

        if (keys.includes('默认')) {
          const list = keys.filter(item => item !== '默认')
          keys = ['默认', ...list]
        }
        for (const key of keys) {
          const resources = []
          const obj = {}
          const item = this.originResourceGroup[key]
          item.resources.forEach(item => {
            if ((item.name || '').indexOf(this.keyword) > -1 || (item.description || '').indexOf(this.keyword) > -1) {
              resources.push(item)
            }
          })
          if (resources.length) {
            obj.labelId = item.labelId
            obj.labelName = item.labelName
            obj.resources = resources
            group[key] = obj
          }
        }
        return group
      }
    },
    watch: {
      keyword (val) {
        const keys = Object.keys(this.resourceGroup)
        if (val) {
          this.activeName = keys
        } else if (this.curGroup) {
          this.activeName = [this.curGroup.labelName]
        } else {
          this.activeName = [keys[0]]
        }
      },
      curGroup () {
        if (this.curGroup) {
          this.activeName = [this.curGroup.labelName]
        }
      },
      resourceGroup () {
        if (!this.activeName.length) {
          this.activeName = [Object.keys(this.resourceGroup)[0]]
        }
      },
      '$route' () {
        this.init()
      },
      curStageId (value) {
        this.$store.commit('apigw/updateCurStage', value)
      }
    },
    created () {
      this.init()
    },
    methods: {
      async init () {
        // this.activeName = []
        const routeParams = this.$route.params
        this.curApigwId = routeParams.apigwId
        this.curComponentName = routeParams.resourceId
        this.getApigwAPIDetail()
        this.getApigwAPI()
        await this.getApigwStages()
        this.getApigwResources()

        // 回到页头
        const container = document.documentElement || document.body
        container.scrollTo({
          top: 0,
          behavior: 'smooth'
        })
      },

      async getApigwAPIDetail () {
        try {
          const res = await this.$store.dispatch('apigw/getApigwAPIDetail', {
            apigwId: this.curApigwId
          })
          this.curApigw = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwStages () {
        try {
          const res = await this.$store.dispatch('apigw/getApigwStages', {
            apigwId: this.curApigwId
          })
          this.stageList = res.data
          if (this.$route.params.stage) {
            this.curStageId = this.$route.params.stage
          } else if (this.stageList.length) {
            this.curStageId = this.stageList[0].name
          } else {
            this.curStageId = ''
          }
          // query参数是的环境是否存在
          const queryStage = this.$route.query.stage
          const resStage = this.stageList[0].name
          if (queryStage) {
            const stageDetils = this.stageList.filter(item => item.name === queryStage)
            if (stageDetils.length) {
              this.curStageId = queryStage
            } else {
              this.curStageId = resStage
              this.$router.push({
                query: { stage: resStage }
              })
            }
          } else {
            this.curStageId = resStage
            this.$router.push({
              query: { stage: resStage }
            })
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleApigwChange (data) {
        this.$router.push({
          name: 'apigwAPIDetailIntro',
          params: {
            apigwId: data
          }
        })
      },

      async getApigwAPI (page) {
        const pageParams = {}
        try {
          const { data: { results } } = await this.$store.dispatch('apigw/getApigwAPI', { pageParams })
          this.apigwList = results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async handleStageChange () {
        this.reset()
        await this.getApigwResources()
        const match = this.resourceList.find(resource => this.curResource.name === resource.name)
        if (match) {
          this.handleShowDoc(match)
        } else {
          this.handleShowIntro()
        }
        this.$router.push({
          query: { stage: this.curStageId }
        })
      },

      reset () {
        this.curComponentName = ''
      },

      async getApigwResources () {
        try {
          const res = await this.$store.dispatch('apigw/getApigwResources', {
            apigwId: this.curApigwId,
            stage: this.curStageId
          })

          const group = {}
          const defaultItem = {
            labelId: 'default',
            labelName: this.$t('默认'),
            resources: []
          }
          this.resourceList = res.data.results
          this.resourceList.forEach(resource => {
            const labels = resource.labels
            if (labels.length) {
              labels.forEach(label => {
                if (typeof label === 'object') {
                  if (group[label.id]) {
                    group[label.id].resources.push(resource)
                  } else {
                    if (group[label.name]) {
                      group[label.name].resources.push(resource)
                    } else {
                      const obj = {
                        labelId: label.id,
                        labelName: label.name,
                        resources: [resource]
                      }
                      group[label.name] = obj
                    }
                  }
                } else {
                  if (group[label]) {
                    group[label].resources.push(resource)
                  } else {
                    const obj = {
                      labelId: label,
                      labelName: label,
                      resources: [resource]
                    }
                    group[label] = obj
                  }
                }
              })
            } else {
              defaultItem.resources.push(resource)
            }
          })
          if (defaultItem.resources.length) {
            group['默认'] = defaultItem
          }
          this.originResourceGroup = group
        } catch (e) {
          // catchErrorHandler(e, this)
        }
      },

      handleShowDoc (resource) {
        this.curResource = resource
        this.curComponentName = resource.name

        this.$store.commit('setMainContentLoading', true)
        this.$router.push({
          name: 'apigwAPIDetailDoc',
          params: {
            apigwId: this.curApigwId,
            stage: this.curStageId,
            resourceId: resource.name
          },
          query: {
            stage: this.curStageId
          }
        })
      },

      handleShowIntro () {
        this.curComponentName = ''
        this.$router.push({
          name: 'apigwAPIDetailIntro'
        })
      },

      hightlight (value) {
        if (this.keyword) {
          return value.replace(new RegExp(`(${this.keyword})`), '<em class="ag-keyword">$1</em>')
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
