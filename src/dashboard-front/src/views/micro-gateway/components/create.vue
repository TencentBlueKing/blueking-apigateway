<template>
  <div class="app-content">
    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('基本信息') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="basicForm" :label-width="200" :model="bcsInfo">
            <bk-form-item
              :label="$t('名称')"
              :required="true"
              :rules="rules.name"
              :property="'name'"
              :error-display-type="'normal'">
              <bk-input
                :placeholder="$t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于20个字符')"
                v-model="bcsInfo.name">
              </bk-input>
            </bk-form-item>
            <bk-form-item
              :label="$t('描述')"
              :required="true"
              :rules="rules.description"
              :property="'description'"
              :error-display-type="'normal'">
              <bk-input
                v-model="bcsInfo.description"
                :placeholder="$t('请输入描述')"></bk-input>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>
    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('实例信息') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="instanceForm" :label-width="200" :model="bcsInfo">
            <bk-form-item :label="$t('创建方式')" v-if="isCreate === 'create'" :required="true">
              <bk-radio-group v-model="createType" @change="createTypeChange" style="margin-top: 5px">
                <bk-radio :value="'microgateway'"> {{ $t('新部署微网关实例') }} </bk-radio>
                <bk-radio :value="'deploy'" style="margin-left: 24px"> {{ $t('接入已部署微网关实例') }} </bk-radio>
              </bk-radio-group>
            </bk-form-item>
            <bk-form-item
              :label="$t('容器项目')"
              :required="true"
              :rules="rules.projectId"
              :property="'projectId'"
              :error-display-type="'normal'">
              <bk-select v-model="bcsInfo.projectId" :disabled="isProject" searchable @change="containerProjectChange">
                <bk-option
                  v-for="option in projects"
                  :key="option.project_id"
                  :id="option.project_id"
                  :name="option.project_name">
                </bk-option>
              </bk-select>
            </bk-form-item>
            <bk-form-item
              :label="$t('容器集群')"
              :required="true"
              :rules="rules.cluster"
              :property="'cluster'"
              :error-display-type="'normal'">
              <bk-select v-model="bcsInfo.cluster" :disabled="isDisabled" :loading="clusterIsLoading" searchable @change="clusterChange">
                <bk-option
                  v-for="option in clustersList"
                  :key="option.cluster_id"
                  :id="option.cluster_id"
                  :name="option.cluster_id">
                </bk-option>
              </bk-select>
            </bk-form-item>
            <bk-form-item
              :label="$t('命名空间')"
              :required="true"
              :rules="rules.namespace"
              :property="'namespace'"
              :error-display-type="'normal'">
              <bk-select v-model="bcsInfo.namespace" :disabled="isNamespace" :loading="namespaceIsLoading" searchable @change="namespaceChange">
                <bk-option
                  v-for="option in namespaces"
                  :key="option.namespace"
                  :id="option.namespace"
                  :name="option.namespace">
                </bk-option>
              </bk-select>
            </bk-form-item>
            <bk-form-item
              :label="$t('Release 名称')"
              v-if="createType === 'microgateway'"
              :required="true"
              :rules="rules.releaseName"
              :property="'releaseName'"
              :error-display-type="'normal'">
              <bk-input
                :placeholder="$t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符')"
                :disabled="releaseIsdisabled"
                v-model="bcsInfo.releaseName">
              </bk-input>
              <p slot="tip" class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                <span>{{ $t('Release 标识，创建后不可修改') }}</span>
              </p>
            </bk-form-item>
            <bk-form-item
              :label="$t('Release 名称')"
              v-else
              :required="true"
              :rules="rules.release"
              :property="'release'"
              :error-display-type="'normal'">
              <bk-select v-model="bcsInfo.release" :disabled="isRelease" :loading="releaseIsLoading" searchable>
                <bk-option
                  v-for="option in releases"
                  :key="option.release_name"
                  :id="option.release_name"
                  :name="option.release_name">
                </bk-option>
              </bk-select>
              <p slot="tip" class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                <span>{{ $t('Release 标识，创建后不可修改') }}</span>
              </p>
            </bk-form-item>
            <bk-form-item
              :label="$t('微网关版本')">
              <bk-input
                v-model="bcsInfo.version"
                :placeholder="$t('无需填写，由系统自动生成')"
                :disabled="true">
              </bk-input>
            </bk-form-item>
            <bk-form-item :label="$t('实例 ID')">
              <bk-input
                v-model="bcsInfo.instanceID"
                :placeholder="$t('无需填写，由系统自动生成')"
                :disabled="true"></bk-input>
            </bk-form-item>
            <bk-form-item :label="$t('JWT 密钥')">
              <bk-input
                :type="autocomplete ? 'text' : 'password'"
                v-model="bcsInfo.JWT"
                :placeholder="$t('无需填写，由系统自动生成')"
                :native-attributes="{ autocomplete: 'off' }"
                :disabled="true"></bk-input>
              <p class="off-icon" @click="showJWT">
                <i :class="autocomplete ? 'apigateway-icon icon-ag-insights' : 'apigateway-icon icon-ag-bukeyulan'"></i>
              </p>
            </bk-form-item>
            <bk-form-item :label="$t('管理端接口地址')">
              <bk-input
                v-model="bcsInfo.apiUrl"
                :placeholder="$t('无需填写，由系统自动生成')"
                :disabled="true"></bk-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                <span> {{ $t('微网关实例通过管理端接口，可上报当前实例状态，拉取网关配置') }} </span>
              </p>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>
    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('实例配置') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="instanceConfigForm" :label-width="200" :model="bcsInfo">
            <bk-form-item
              :label="$t('访问地址')"
              :required="true"
              :rules="rules.url"
              :property="'url'"
              :error-display-type="'normal'">
              <bk-input
                :placeholder="$t('如: http://api.example.com/v1/')"
                v-model="bcsInfo.url">
              </bk-input>
              <p slot="tip" class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                <span> {{ $t('微网关对外提供接口服务的地址，此地址加上具体接口的路径，即为该微网关对外提供接口的完整访问地址') }} </span>
              </p>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>
    <section class="ag-panel-action mt20">
      <div class="panel-content" style="margin-left: 270px;">
        <div class="panel-wrapper tc">
          <bk-button class="mr5" theme="primary" style="width: 120px;" @click="changeDialog" :loading="isDataLoading"> {{ $t('提交') }} </bk-button>
          <bk-button style="width: 120px;" @click="handleMicrogatewayCancel"> {{ $t('取消') }} </bk-button>
        </div>
      </div>
    </section>
    <bk-dialog v-model="createDialogConf.visiable"
      theme="primary"
      :width="525"
      :title="$t('确认创建微网关实例')"
      :mask-close="true"
      @cancel="createDialogConf.visiable = false"
      @confirm="submitMicrogateway">
      <p> {{ $t('微网关实例配置如下：') }} </p>
      <p> {{ $t('容器项目：') }} {{tipProjectName && tipProjectName.project_name}}</p>
      <p> {{ $t('容器集群：') }} {{bcsInfo.cluster}}</p>
      <p> {{ $t('命名空间：') }} {{bcsInfo.namespace}}</p>
      <p> {{ $t('Release 名称') }}：{{createType === 'microgateway' ? bcsInfo.releaseName : bcsInfo.release}}</p>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import i18n from '@/language/i18n.js'

  export default {
    name: 'createMicroGateway',
        
    data () {
      return {
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 19,
              message: this.$t('不能多于20个字符'),
              trigger: 'blur'
            },
            {
              min: 3,
              message: this.$t('不能小于3个字符'),
              trigger: 'blur'
            },
            {
              validator (value) {
                const reg = /^[a-z][a-zA-Z0-9-]{3,19}$/
                return reg.test(value)
              },
              message: this.$t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于20个字符'),
              trigger: 'blur'
            }
          ],

          description: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],

          projectId: [
            {
              required: true,
              message: this.$t('请选择容器项目'),
              trigger: 'blur'
            }
          ],

          cluster: [
            {
              required: true,
              message: this.$t('请选择容器集群'),
              trigger: 'blur'
            }
          ],

          releaseName: [
            {
              required: true,
              message: this.$t('请输入Release名称'),
              trigger: 'blur'
            },
            {
              validator: this.verifyName,
              message: this.$t('该名称已存在!'),
              trigger: 'blur'
            },
            {
              validator: this.rulesReleaseName,
              message: this.$t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符'),
              trigger: 'blur'
            }
          ],

          release: [
            {
              required: true,
              message: this.$t('请选择Release名称'),
              trigger: 'blur'
            }
          ],

          namespace: [
            {
              required: true,
              message: this.$t('请选择命名空间'),
              trigger: 'blur'
            }
          ],
                    
          version: [
            {
              required: true,
              message: this.$t('请选择微网关版本'),
              trigger: 'blur'
            }
          ],

          url: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        },
        instanceInfo: {
        },
        typeList: [],
        curStrategy: {},
        bcsInfo: {
          'name': '',
          'description': '',
          cluster: '',
          namespace: '',
          projectId: '',
          releaseName: '',
          release: '',
          version: '',
          url: '',
          instanceID: '',
          JWT: '',
          apiUrl: ''
        },
        clustersList: [],
        namespaces: [],
        projects: [],
        releases: [],
        createType: 'microgateway',
        isDataLoading: false,
        leave: false,
        MicrogatewayData: {},
        createDialogConf: {
          visiable: false
        },
        autocomplete: false,
        MicrogatewayList: [],
        tipProjectName: [],
        namespaceIsLoading: false,
        clusterIsLoading: false,
        releaseIsLoading: false,
        releaseIsdisabled: false
      }
    },

    computed: {
      isDisabled () {
        if (this.bcsInfo.projectId !== '' && this.isCreate === 'create') {
          return false
        } else {
          return true
        }
      },

      isNamespace () {
        if (this.bcsInfo.projectId !== '' && this.bcsInfo.cluster !== '' && this.isCreate === 'create') {
          return false
        } else {
          return true
        }
      },

      isRelease () {
        if (this.bcsInfo.projectId !== '' && this.bcsInfo.cluster !== '' && this.bcsInfo.namespace !== '' && this.isCreate === 'create') {
          return false
        } else {
          return true
        }
      },

      isProject () {
        if (this.isCreate === 'edit') {
          return true
        } else {
          return false
        }
      },
            
      isCreate () {
        return this.$route.meta.isCreate
      },

      apigwId () {
        return this.$route.params.id
      },

      releaseNameCom: {
        get () {
          const apigwList = this.$store.state.apis.apigwList
          const result = apigwList.find(apigw => {
            return String(apigw.id) === String(this.apigwId)
          })
          return result ? result.name : ''
        }
      },

      microId () {
        return this.$route.query.MicroId
      }
    },

    watch: {
      'bcsInfo.name' (val) {
        if (this.bcsInfo.releaseName && this.isCreate === 'edit') {
          return
        }
        if (val === '') {
          this.bcsInfo.releaseName = ''
          return
        }
        this.bcsInfo.releaseName = this.releaseNameCom + '-' + val
      },

      'bcsInfo.release' (val) {
        if (val) {
          this.bcsInfo.version = this.releases.find(e => e.release_name === val).chart_version
        }
      }
    },

    created () {
      this.getProjects()
    },

    mounted () {
      if (this.isCreate === 'create') {
        this.$store.commit('setMainContentLoading', false)
      }
      this.getMicrogatewayList()
    },

    beforeRouteEnter (to, from, next) {
      if (to.query.MicroId) {
        to.meta.title = i18n.t('编辑微网关实例')
        to.meta.isCreate = 'edit'
        next(vm => {
          vm.getMicrogateway()
          vm.releaseIsdisabled = true
        })
      } else {
        to.meta.title = i18n.t('新建微网关实例')
        to.meta.isCreate = 'create'
      }
      next()
    },

    beforeRouteLeave (to, from, next) {
      if (to.params.isLeave) {
        next()
      } else if (this.bcsInfo.name !== '' || this.bcsInfo.description !== '' || this.bcsInfo.projectId !== '' || this.bcsInfo.url !== '') {
        this.$bkInfo({
          type: 'warning',
          okText: i18n.t('确认'),
          title: i18n.t('确认离开当前页？'),
          subTitle: i18n.t('离开当前页面，填写内容将不会保留，请谨慎操作'),
          confirmFn () {
            next()
          }
        })
      } else {
        next()
      }
    },

    methods: {
      submitMicrogateway () {
        this.isCreate === 'create' ? this.createMicro() : this.editMicro()
      },

      hintBkMessage (msg, type = 'success') {
        this.$bkMessage({
          message: msg,
          offsetY: 80,
          theme: type
        })
      },

      changeDialog () {
        this.isDataLoading = true
        this.tipProjectName = this.projects.filter(v => v.project_id === this.bcsInfo.projectId)[0]
        const valiDateList = [this.$refs.basicForm.validate(), this.$refs.instanceForm.validate(), this.$refs.instanceConfigForm.validate()]
        Promise.all(valiDateList).then(() => {
          this.isCreate === 'create' ? this.createDialogConf.visiable = true : this.submitMicrogateway()
        }).catch((e) => {
          catchErrorHandler(e, this)
        }).finally(() => {
          this.isDataLoading = false
        })
      },

      async createMicro () {
        try {
          const apigwId = this.apigwId
          const projectList = this.projects.filter(v => v.project_id === this.bcsInfo.projectId)
          const projectName = projectList[0].project_name
          const data = {
            create_way: this.createType === 'microgateway' ? 'need_deploy' : 'relate_deployed',
            name: this.bcsInfo.name,
            description: this.bcsInfo.description,
            bcs_info: {
              project_name: projectName,
              project_id: this.bcsInfo.projectId,
              cluster_id: this.bcsInfo.cluster,
              namespace: this.bcsInfo.namespace,
              chart_version: this.bcsInfo.version,
              release_name: this.createType === 'microgateway' ? this.bcsInfo.releaseName : this.bcsInfo.release
            },
            http_info: {
              http_url: this.bcsInfo.url
            },
            jwt_auth_info: {}
          }
          const res = await this.$store.dispatch('microGateway/createMicrogateway', { apigwId, data })
          if (res.code === 0 && res.message === 'OK') {
            this.hintBkMessage('新建成功!')
            this.$router.push({
              name: 'microGateway',
              params: {
                isLeave: true
              }
            })
          }
        } catch (e) {
          this.hintBkMessage(e.message, 'error')
        }
      },

      async editMicro () {
        const apigwId = this.apigwId
        const id = this.microId
        const data = {
          name: this.bcsInfo.name,
          description: this.bcsInfo.description,
          'http_info': {
            'http_url': this.bcsInfo.url
          }
        }
        try {
          const res = await this.$store.dispatch('microGateway/updateMicrogateway', { apigwId, id, data })
          if (res.code === 0 && res.message === 'OK') {
            this.hintBkMessage('编辑成功!')
            this.$router.push({
              name: 'microGateway',
              params: {
                isLeave: true
              }
            })
          }
        } catch (e) {
          catchErrorHandler(e, this)
          this.hintBkMessage(e.message, 'error')
        }
      },

      handleMicrogatewayCancel () {
        this.$refs.basicForm.clearError()
        this.$refs.instanceForm.clearError()
        this.$refs.instanceConfigForm.clearError()
        this.$router.push({
          name: 'microGateway'
        })
      },

      getOptions () {
        // 根据容器项目获取projectId , 通过projectId获取其他下拉框数据
        const projectId = this.bcsInfo.projectId
        this.getClusters(projectId)
      },

      async getClusters (projectId) {
        this.clusterIsLoading = true
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('microGateway/getClusters', { apigwId, projectId })
          if (res.code === 0 && res.message === 'OK') this.clustersList = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.clusterIsLoading = false
        }
      },

      async getNamespaces (projectId) {
        this.namespaceIsLoading = true
        const apigwId = this.apigwId
        const cluster = this.bcsInfo.cluster
        try {
          const res = await this.$store.dispatch('microGateway/getNamespaces', { apigwId, projectId, cluster })
          if (res.code === 0 && res.message === 'OK') this.namespaces = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.namespaceIsLoading = false
        }
      },

      // 获取 project_id
      async getProjects () {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('microGateway/getProjects', { apigwId })
          if (res.code === 0 && res.message === 'OK') {
            this.projects = res.data
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getReleases (projectId) {
        this.releaseIsLoading = true
        const apigwId = this.apigwId
        const clusterName = this.bcsInfo.cluster
        const namespace = this.bcsInfo.namespace
        try {
          const res = await this.$store.dispatch('microGateway/getReleases', { apigwId, projectId, clusterName, namespace })
          if (res.code === 0 && res.message === 'OK') this.releases = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.releaseIsLoading = false
        }
      },

      // 根据id获取微网关实例
      async getMicrogateway () {
        const apigwId = this.apigwId
        const id = this.microId
        try {
          const res = await this.$store.dispatch('microGateway/getMicrogateway', { apigwId, id })
          if (res.code === 0 && res.message === 'OK') {
            const MircroData = res.data
            this.bcsInfo.name = MircroData.name
            this.bcsInfo.description = MircroData.description
            this.bcsInfo.projectId = MircroData.bcs_info.project_id
            this.bcsInfo.url = MircroData.http_info.http_url
            this.bcsInfo.instanceID = MircroData.id
            this.bcsInfo.apiUrl = MircroData.bk_apigateway_api_url
            this.bcsInfo.JWT = MircroData.jwt_auth_info.secret_key
            this.bcsInfo.cluster = MircroData.bcs_info.cluster_id
            this.bcsInfo.namespace = MircroData.bcs_info.namespace
            this.bcsInfo.releaseName = MircroData.bcs_info.release_name
            this.bcsInfo.version = MircroData.bcs_info.chart_version
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getMicrogatewayList () {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('microGateway/getMicrogatewayList', { apigwId })
          this.MicrogatewayList = res.data.results || []
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      showJWT () {
        this.autocomplete = !this.autocomplete
      },

      verifyName () {
        if (this.isCreate === 'create') {
          return !this.MicrogatewayList.find(arrItem => arrItem.release_name === this.bcsInfo.releaseName)
        } else {
          return true
        }
      },

      rulesReleaseName (value) {
        if (this.isCreate === 'create') {
          const reg = /^[a-z][a-zA-Z0-9-]{3,29}$/
          return reg.test(value)
        }
        const reg = /^[a-z][a-zA-Z0-9-]{3,47}$/
        return reg.test(value)
      },

      containerProjectChange () {
        if (this.isCreate === 'create') {
          this.bcsInfo.cluster = ''
          this.bcsInfo.namespace = ''
          this.bcsInfo.release = ''
        }
        if (this.bcsInfo.projectId !== '') {
          this.getOptions()
        }
      },

      clusterChange () {
        if (this.isCreate === 'create') {
          this.bcsInfo.namespace = ''
          this.bcsInfo.release = ''
        }
        if (this.bcsInfo.projectId !== '' && this.bcsInfo.cluster !== '') {
          this.getNamespaces(this.bcsInfo.projectId)
        }
      },

      namespaceChange () {
        if (this.bcsInfo.projectId !== '' && this.bcsInfo.cluster !== '' && this.bcsInfo.namespace !== '') {
          this.getReleases(this.bcsInfo.projectId)
        }
      },
            
      createTypeChange () {
        this.$refs.instanceForm.clearError()
      }
    }
  }
</script>

<style lang="postcss" scoped>
    
    .off-icon {
        position: absolute;
        top: 5px;
        right: 5px;
        width: 15px;
        height: 15px;
        .apigateway-icon {
            font-size: 15px;
            color: #727985;
            z-index: 0;
        }
    }
</style>
