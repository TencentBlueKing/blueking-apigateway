<template>
  <div class="index-wrapper">
    <div class="banner">
      <searcher class="ag-searcher-box" :version-list="componentList"></searcher>
    </div>

    <loader
      class="ag-container"
      :delay="1000"
      :is-loading="mainContentLoading"
      :background-color="'#FAFBFD'"
      :loader="'index-loader'"
      :height="800"
      :offset-left="0"
      :offset-top="0"
      :has-border="false">
      <template v-if="componentList.length">
        <div class="left">
          <div :class="['side-nav', { 'fixed': isFixed }]">
            <div class="group" v-for="(component, index) of componentList" :key="index">
              <strong class="category-title" @click="handleScrollTo(component.board)" style="cursor: pointer;">{{component.board_label}}</strong>
              <svg aria-hidden="true" class="category-icon">
                <use :xlink:href="`#doc-icon${index % 4}`"></use>
              </svg>
              <ul class="list">
                <li
                  :class="{ 'selected': curCategoryId === `${component.board}_${category.id}` }"
                  v-for="(category) of component.categories"
                  :key="category.id"
                  v-bk-overflow-tips
                  @click="handleScrollTo(component.board, category)">
                  <a href="javascript: void(0);">{{category.name}}</a>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div class="right">
          <div class="main-content">
            <div class="version-panel" v-for="(component, i) of componentList" :key="component.board">
              <p class="version-name">
                <svg aria-hidden="true" class="category-icon">
                  <use :xlink:href="`#doc-icon${i % 4}`"></use>
                </svg>
                <strong :id="`version_${component.board}`">{{component.board_label}}</strong>
              </p>

              <div class="ag-card" v-for="(category, index) of component.categories" :key="index">
                <p class="card-title" :id="`${component.board}_${category.id}`">{{category.name}} <span class="total">({{category.systems.length}})</span></p>
                <div class="card-content">
                  <ul class="systems">
                    <li v-for="item of category.systems" :key="item.name">
                      <router-link :to="{ name: 'ComponentAPIDetailIntro', params: { version: component.board, category: category.name, id: item.name } }">{{item.description}}</router-link>
                      <p class="desc">{{item.name}}</p>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
      <div class="mt20" v-else style="width: 100%; border-radius: 2px; border: 1px solid #eee; background: #FFF;">
        <table-empty empty />
      </div>
    </loader>
  </div>
</template>

<script>
  import Searcher from '@/components/searcher'
  import loader from '@/components/loader'

  export default {
    components: {
      loader,
      Searcher
    },
    data () {
      return {
        formData: {
          name: '',
          date: ''
        },
        curCategoryId: '',
        componentList: [],
        curVersionData: {},
        isFixed: false,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        }
      }
    },
    computed: {
      mainContentLoading () {
        return this.$store.state.mainContentLoading
      }
    },
    created () {
      this.init()
    },
    mounted () {
      const self = this
      const sideNav = document.querySelector('.side-nav')
      const winHeight = window.innerHeight
      const sideHeight = winHeight - 52 - 16 - 105
      const container = document.querySelector('#app .container-content') || window
      container.onscroll = function () {
        const scrollTop = container.scrollTop || document.documentElement.scrollTop || document.body.scrollTop
        self.isFixed = scrollTop > 160
        if (self.isFixed) {
          if (sideNav) {
            sideNav.style = `height: ${sideHeight}px;`
          }
        }
      }
    },
    methods: {
      init () {
        this.getComponentAPI()
      },
      async getComponentAPI () {
        this.$store.commit('setMainContentLoading', true)
        try {
          const res = await this.$store.dispatch('esb/getComponentAPI')
          this.componentList = res.data
          if (this.componentList.length) {
            this.curVersionData = this.componentList[0]
          }
        } catch (e) {
          console.error(e)
        } finally {
          this.$store.commit('setMainContentLoading', false)
        }
      },
      toggleTableSize () {
        const size = ['small', 'medium', 'large']
        const index = (size.indexOf(this.size) + 1) % 3
        this.size = size[index]
      },
      handlePageChange (page) {
        this.pagination.current = page
      },
      remove (row) {
        const index = this.tableData.indexOf(row)
        if (index !== -1) {
          this.tableData.splice(index, 1)
        }
      },
      reset (row) {
        row.status = this.$t('创建中')
      },
      handleScrollTo (version, category) {
        const OFFSET = category ? 87 : 75
        const categoryId = category ? `${version}_${category.id}` : `version_${version}`
        const element = document.getElementById(categoryId)
        this.curCategoryId = categoryId

        if (element) {
          const rect = element.getBoundingClientRect()
          const container = document.querySelector('#app .container-content') || document.documentElement || document.body
          const top = container.scrollTop + rect.top - OFFSET

          container.scrollTo({
            top: top,
            behavior: 'smooth'
          })
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './index.css';
</style>
