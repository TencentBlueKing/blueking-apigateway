/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
import path from 'path'
import fs from 'fs'
import config from './config'

const APP_VERSION = process.env.APP_VERSION || 'te'
const JSON_DIR_PATH = path.resolve(__dirname, '../static/json')
const JS_DIR_PATH = path.resolve(__dirname, '../static/js')
const RUNTIME_DIR_PATH = path.resolve(__dirname, '../static/runtime')

class VersionPatchPlugin {
    constructor () {
        console.time('Pre task')
        const configPath = path.resolve(JSON_DIR_PATH, './config.js')
        const bklogoutPath = path.resolve(JS_DIR_PATH, './bklogout.js')
        const runtimePath = path.resolve(RUNTIME_DIR_PATH, './runtime.js')

        if (fs.existsSync(configPath)) {
            fs.unlinkSync(configPath)
        }

        if (fs.existsSync(bklogoutPath)) {
            fs.unlinkSync(bklogoutPath)
        }

        if (fs.existsSync(runtimePath)) {
            fs.unlinkSync(runtimePath)
        }

        // 复制config
        const staticData = fs.readFileSync(path.resolve(JSON_DIR_PATH, `./config-${APP_VERSION}.js`))
        fs.writeFileSync(configPath, staticData)

        // 复制runtime
        const runtimeData = fs.readFileSync(path.resolve(RUNTIME_DIR_PATH, `./runtime-${APP_VERSION}.js`))
        let envs = {}
        let fileContent = runtimeData.toString()

        if (process.env.NODE_ENV === 'production') {
            envs = Object.assign({}, config.build.env, process.env)
        } else {
            envs = Object.assign({}, config.dev.env, process.env)
        }
        for (const key in envs) {
            const reg = new RegExp(`<%=${key}%>`)
            fileContent = fileContent.replace(reg, JSON.stringify(envs[key]))
        }
        
        fileContent = fileContent.replace(/<%=[\w]+%>/g, "''")
        fs.writeFileSync(runtimePath, fileContent)

        // 复制bklogout
        const logoutData = fs.readFileSync(path.resolve(JS_DIR_PATH, `./bklogout-${APP_VERSION}.js`))
        fs.writeFileSync(bklogoutPath, logoutData)
        console.timeEnd('Pre task')
    }

    apply (compiler) {
        compiler.plugin('done', function () {})
    }
}

module.exports = VersionPatchPlugin
