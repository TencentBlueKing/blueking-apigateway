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
/**
 * @file mock index module
 * @author
 */

import moment from 'moment'
import faker from 'faker'
import chalk from 'chalk'
import Mock from 'mockjs'

import { randomInt, sleep } from './util'

export async function response(getArgs, postArgs, req) {
    console.log(chalk.cyan('req', req.method))
    console.log(chalk.cyan('getArgs', JSON.stringify(getArgs, null, 0)))
    console.log(chalk.cyan('postArgs', JSON.stringify(postArgs, null, 0)))
    console.log()
    const invoke = getArgs.invoke
    if (invoke === 'getAlarms') {
        // https://github.com/nuysoft/Mock/wiki/Getting-Started
        const list = Mock.mock({
            'list|22': [{
                // 属性 id 是一个自增数，起始值为 1，每次增 1
                'id|+1': 1,
                'alarm_strategy_id': '222222',
                'alarm_strategy_name': '微信微信微信微信微信微信微信',
                'alarm_id': '1111',
                'status': 'received',
                'message': '正常111',
                'created_time': '2020-03-11 07:15:08',
            }]
        })
        return {
            "code": 0,
            "result": true,
            "message": "string",
            "data": {
                "count": 10,
                "has_next": true,
                "has_previous": true,
                "results": list.list
            }
        }
    }
    return {
        code: 0,
        data: {}
    }
}
