# 执行作业方案并收集日志

## 不适用场景

- 临时在主机上执行脚本或分发文件（fast_execute_script、fast_transfer_file）：不在本 Skill 范围。
- 只查已有作业实例的状态和日志：用「作业执行失败诊断」。
- 不知道方案 ID：先在作业平台查到方案 ID 再使用。

## 前置条件

按 [references/permissions.md](references/permissions.md) 申请权限。接口清单里「需申请权限」为「是」的资源，申请通过后才能调用；为「否」的不必申请网关接口权限。业务侧权限（业务、模板、方案、流水线）由各系统自己校验，缺少时按「异常处理」提示用户申请。

## 接口清单

每个接口一行。认证和是否要申请权限以这张表为准；参数位置和取值见「执行步骤」里每一步的 OpenAPI 片段。

| 资源 | 网关 | 环境 | 方法 | 路径 | 说明 | 用户认证 | 应用认证 | 需申请权限 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `execute_job_plan` | jobv3-cloud | prod | POST | `/api/v3/execute_job_plan` | 启动作业执行方案。 | 是 | 是 | 是 |
| `get_job_instance_status` | jobv3-cloud | prod | GET | `/api/v3/get_job_instance_status` | 根据作业实例 ID 查询作业执行状态。 | 是 | 是 | 是 |
| `batch_get_job_instance_ip_log` | jobv3-cloud | prod | POST | `/api/v3/batch_get_job_instance_ip_log` | 根据主机列表批量查询作业执行日志。 | 是 | 是 | 是 |

## 输入

必填缺失时先问用户，不要猜测。说明里写了拟定规则的，按规则拟定并写进回复，不要为拟定值再问一次。选填缺失时用默认值；没有默认值就不传。

| 参数 | 类型 | 必填 | 说明 | 示例 | 默认值 |
| --- | --- | --- | --- | --- | --- |
| `bk_scope_id` | string | 是 | 业务 ID；bk_scope_type 为 biz_set 时是业务集 ID | `2` | - |
| `job_plan_id` | integer | 是 | 作业执行方案 ID，可在作业平台方案列表中看到 | `1024` | - |
| `bk_scope_type` | string | 否 | 资源范围类型：biz 业务，biz_set 业务集 | `biz` | `biz` |
| `global_var_list` | array | 否 | 要覆盖的全局变量，元素为 `{name, value}` 或主机变量 `{name, server}`；不传则使用方案默认值 | `[{"name": "version", "value": "1.2.3"}]` | - |

## 输出

完成后按下表组织回复，字段取值只来自「来源」列，不要编造。

| 字段 | 类型 | 说明 | 来源 |
| --- | --- | --- | --- |
| `job_instance_id` | integer | 作业实例 ID | `${{ steps.run-plan.outputs.data.job_instance_id }}` |
| `job_status` | integer | 作业状态码：3 成功，4 失败，7 等待用户，其余见第 2 步响应字段 | `${{ steps.wait-result.outputs.data.job_instance.status }}` |
| `step_results` | array | 每个步骤的状态，以及每台主机的状态、退出码和错误码 | `${{ steps.wait-result.outputs.data.step_instance_list }}` |
| `failed_host_logs` | array | 每个失败步骤中失败主机的日志摘录。`data.log_type` 为 1 时取 `script_task_logs`，为 2 时取 `file_task_logs` | `${{ steps.collect-log.outputs.data }}` |

## 执行步骤

来源和取值里的 `steps.<步骤 id>` 指该步骤调用的响应体，对应关系如下。

| 步骤 | id | 名称 | 资源 |
| --- | --- | --- | --- |
| 1 | `run-plan` | 执行作业方案 | `execute_job_plan` |
| 2 | `wait-result` | 轮询作业状态 | `get_job_instance_status` |
| 3 | `collect-log` | 拉取失败主机日志 | `batch_get_job_instance_ip_log` |

run-plan 返回的 `data.job_instance_id` 贯穿后两步；三个接口的 `bk_scope_type`、`bk_scope_id` 必须相同。collect-log 只在作业没有成功时执行。

每步写成一段 OpenAPI 3.1 片段：`paths` 下是路径和方法，`x-bk-gateway`、`x-bk-stage` 是网关和环境；只列本 Skill 要传的参数，`responses` 只列要读的响应字段。参数位置看 `in`：`query` 放查询串；`requestBody` 里的字段组成 JSON 正文。

取值：`x-from: ${{ inputs.<输入名> }}` 来自输入；`x-from: ${{ steps.<步骤 id>.outputs.<字段路径> }}` 来自该步骤的响应体；`x-value` 是固定值，按 JSON 原样传；`x-omit-if-unset: true` 表示取自选填输入，用户没给时整个参数不传；没有 `x-from`、`x-value` 的参数按该步说明取值。

带「执行条件」的步骤，条件不成立时跳过。

1. run-plan / execute_job_plan：执行作业方案

   执行方案。不传已弃用的 `bk_biz_id`。

   ```yaml
   paths:
     /api/v3/execute_job_plan:
       post:
         operationId: execute_job_plan
         x-bk-gateway: jobv3-cloud
         x-bk-stage: prod
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 required: [bk_scope_type, bk_scope_id, job_plan_id]
                 properties:
                   bk_scope_type:
                     type: string
                     description: 资源范围类型：biz 业务，biz_set 业务集
                     x-from: ${{ inputs.bk_scope_type }}
                   bk_scope_id:
                     type: string
                     description: 资源范围 ID，与 bk_scope_type 对应的业务 ID 或业务集 ID
                     x-from: ${{ inputs.bk_scope_id }}
                   job_plan_id:
                     type: integer
                     description: 作业执行方案 ID
                     x-from: ${{ inputs.job_plan_id }}
                   global_var_list:
                     type: array
                     items: {type: object}
                     description: 全局变量。元素字段：id 或 name 二选一作为标识；value 为字符、密码、数组、命名空间变量值；server 为主机变量值（host_id_list / ip_list / dynamic_group_list / topo_node_list）。未传的变量用方案默认值
                     x-from: ${{ inputs.global_var_list }}
                     x-omit-if-unset: true
         responses:
           '200':
             description: 只列本 Skill 要读的字段
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     data:
                       type: object
                       properties:
                         job_instance_id: {type: integer, description: 作业实例 ID}
   ```

2. wait-result / get_job_instance_status：轮询作业状态

   每 5 秒查一次，最多 120 次（约 10 分钟）；`data.finished` 为 true 时结束。`result` 为 false，或 `data.job_instance.status` 为 7（等待用户）时立即停止：状态为 7 时 `finished` 不会变 true，按「异常处理」告诉用户。`return_ip_result=true` 用于拿到每台主机的结果。到达次数上限仍未结束时，返回 `job_instance_id` 和当前状态。

   ```yaml
   paths:
     /api/v3/get_job_instance_status:
       get:
         operationId: get_job_instance_status
         x-bk-gateway: jobv3-cloud
         x-bk-stage: prod
         parameters:
           - name: bk_scope_type
             in: query
             required: true
             description: 资源范围类型：biz 业务，biz_set 业务集
             schema: {type: string}
             x-from: ${{ inputs.bk_scope_type }}
           - name: bk_scope_id
             in: query
             required: true
             description: 资源范围 ID
             schema: {type: string}
             x-from: ${{ inputs.bk_scope_id }}
           - name: job_instance_id
             in: query
             required: true
             description: 作业实例 ID
             schema: {type: integer}
             x-from: ${{ steps.run-plan.outputs.data.job_instance_id }}
           - name: return_ip_result
             in: query
             description: 是否返回每台主机的执行结果（step_ip_result_list），默认 false
             schema: {type: boolean}
             x-value: true
         responses:
           '200':
             description: 只列本 Skill 要读的字段
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     data:
                       type: object
                       properties:
                         job_instance:
                           type: object
                           properties:
                             status: {type: integer, description: 作业状态：1 未执行，2 正在执行，3 执行成功，4 执行失败，5 跳过，6 忽略错误，7 等待用户，8 手动结束，9 状态异常，10 强制终止中，11 强制终止成功}
                         step_instance_list: {type: array}
   ```

3. collect-log / batch_get_job_instance_ip_log：拉取失败主机日志

   执行条件：`data.job_instance.status` 不是 3（执行成功）

   对 wait-result 返回的 `data.step_instance_list` 中 `status` 为 4（执行失败）、9（状态异常）或 12（强制终止失败）的每个步骤各调用一次，没有这样的步骤时跳过：`step_instance_id` 取该步骤的 `step_instance_id`；请求体的 `host_id_list` 取该步骤 `step_ip_result_list` 中 `status` 不是 9（执行成功）的主机的 `bk_host_id`。只放失败的主机：成功主机的日志对排查没有帮助，还会让结果变长。

   ```yaml
   paths:
     /api/v3/batch_get_job_instance_ip_log:
       post:
         operationId: batch_get_job_instance_ip_log
         x-bk-gateway: jobv3-cloud
         x-bk-stage: prod
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 required: [bk_scope_type, bk_scope_id, job_instance_id, step_instance_id]
                 properties:
                   bk_scope_type:
                     type: string
                     description: 资源范围类型：biz 业务，biz_set 业务集
                     x-from: ${{ inputs.bk_scope_type }}
                   bk_scope_id:
                     type: string
                     description: 资源范围 ID
                     x-from: ${{ inputs.bk_scope_id }}
                   job_instance_id:
                     type: integer
                     description: 作业实例 ID
                     x-from: ${{ steps.run-plan.outputs.data.job_instance_id }}
                   step_instance_id:
                     type: integer
                     description: 步骤实例 ID
         responses:
           '200':
             description: 只列本 Skill 要读的字段
             content:
               application/json:
                 schema:
                   type: object
                   properties:
                     data: {type: object}
   ```

   资源定义中必填但未映射：`step_instance_id`，按本步说明处理。

## 运行约束

会改动线上状态的接口按用户原话选一种模式，整次只选一次。用户已经说出执行意图时直接执行，不要再问选哪种模式，也不要逐步再确认：

- 直接执行：用户要求现在就做（「跑一下」「执行」「启动」「直接执行」「不用再问」），且必填参数齐全。按拟定规则补上的值写进最终回复，不要为拟定值再问一次。
- 确认后执行：用户说先确认、先别执行，或必填参数有歧义。只问一次，列出将使用的参数，得到确认后再调用写接口。

- execute_job_plan 会在方案配置的主机上执行。一次请求只执行一次。执行接口返回后，后续任何失败都不要重新执行方案：重跑会在所有主机上再执行一遍，失败时更需要先看日志。
- 三个接口的 `bk_scope_type`、`bk_scope_id` 必须与输入一致，否则查不到这次作业实例。
- 日志可能很长：每台主机只摘录最后 50 行和含 error、fail、exception 的行，不整段贴出。

## 调用方式

按 [references/how-to-call-apis.md](references/how-to-call-apis.md) 把上面的取值代进调用。步骤里不写命令。

## 异常处理

- `result=false`：把 `code` 和 `message` 告诉用户并停止。
- 外壳 `status` 为 403 且 `headers` 里的 `X-Bkapi-Error-Code` 为 `1640301`：应用没有网关接口权限，按 references/permissions.md 申请。
- `message` 提示没有业务或方案权限：请用户在作业平台申请对应权限，不属于网关权限。
- `job_instance.status` 为 7（等待用户）：方案里有人工确认步骤，请用户到作业平台处理；不拉日志，也不要替用户确认。
- 主机 `status` 为 1 或 `error_code` 为 310（Agent 异常）：日志可能为空，直接报告 Agent 异常，建议检查该主机的 GSE Agent。

## 示例

用户：在业务 2 执行方案 1024，version 用 1.2.3。

用户要求现在执行，按直接执行。bk_scope_type 用默认值 `biz`。

1. execute_job_plan → `data.job_instance_id = 10000`。
2. get_job_instance_status 每 5 秒一次，第 6 次 `data.finished = true`，`job_instance.status = 4`；步骤 75 失败，主机 101 `status = 11`、`error_code = 104`。
3. batch_get_job_instance_ip_log（step_instance_id 75，host_id_list [101]）→ 日志末尾 `nginx: [emerg] unknown directive`。
4. 回复：作业 10000 失败。步骤“重载 nginx”在 10.0.0.1 上脚本返回码非零，报错 `nginx: [emerg] unknown directive`，其余 3 台成功。

用户若说「先别执行」：不调用接口，列出范围、方案 1024 和 global_var_list，等这一次确认。
