# API 资源路径冲突说明

## 结论

在使用 APISIX `radixtree_uri_with_parameter` 路由模式时，即使两个资源的请求路径字符串不同，也可能匹配同一个请求。配置资源时，应避免同一请求方法下的以下两种路径重叠：

1. **仅参数名不同，路径结构相同。**
2. **归一化后的父路径相同，最后一段分别为固定文本和路径参数。**

这类问题属于请求匹配重叠，并非路由注册失败。两个资源可能都能保存、注册，但请求只会命中其中一个。

## 类型 1：路径结构相同，仅参数名不同

例如：

```text
GET /api/v1/config/biz/{bizId}/apps/{appId}/template_revisions
GET /api/v1/config/biz/{bizI_d}/apps/{app_Id}/template_revisions
```

将参数名归一化后，两条路径均为：

```text
GET /api/v1/config/biz/{}/apps/{}/template_revisions
```

**两条资源的匹配范围相同，存在冲突。**

需要注意：命中结果并非只取决于注册顺序。同一树节点内的候选路由先比较 `priority`；优先级相同时，比较原始路由路径的字节长度，该长度包含参数名；优先级与长度都相同时，才按照插入顺序先匹配先注册的候选项。

本例中，第二条路径的参数名更长。在默认相同优先级下，无论按什么顺序注册，实测均命中第二条。

建议保留一个明确的资源定义。仅修改参数名称，不能消除冲突。

## 类型 2：末段固定文本与路径参数重叠

例如：

```text
DELETE /api/v3/set/{bk_biz_id}/batch
DELETE /api/v3/set/{bk_biz_id}/{bk_set_id}
```

归一化后，父路径均为 `/api/v3/set/{}/`，末段分别为 `batch` 和 `{}`。

请求 `DELETE /api/v3/set/1/batch` 同时满足两条路径：`batch` 也可以作为参数 `bk_set_id` 的值。

**在默认相同优先级下，本例实测命中第二条参数路由。** 两条路由均在首个参数前的 `/api/v3/set/` 节点下比较，第二条原始路由路径更长。

但不能据此认为“参数路由永远优先于固定文本路由”：

- 将第二条末段参数改为 `{id}` 后，第一条路径更长，实测命中 `batch` 路由。
- 对于 `/x/batch` 与 `/x/{long_name}`，第一条是完整静态路径，实测优先命中 `/x/batch`；它不经过上述同节点候选列表的长度竞争。
- 同节点内设置不同 `priority` 也会改变结果。默认网关资源配置不应依赖这种方式消除歧义。

因此，末段固定文本与参数重叠应作为配置风险提示；不能统一描述为“固定文本路由一定被参数路由覆盖”。

建议将不同操作放在不重叠的路径结构下，例如 `/api/v3/set/{bk_biz_id}/batch` 与 `/api/v3/set/{bk_biz_id}/items/{bk_set_id}`。不要依赖参数名长短或注册顺序控制路由行为。

## 实测范围

测试日期：2026-09-10。使用本机 OpenResty 实际调用 `lua-resty-radixtree`，不是根据文档推测结果。

- 本地 APISIX 工程的 rockspec 声明依赖 `lua-resty-radixtree 2.9.2-0`。
- 先验证本机安装的该版本，再直接加载上游 `v2.9.2` Lua 源码进行固定版本复测。
- 以下 6 种情形，各验证正反两种注册顺序，以及原始 APISIX 路径、网关转换后的路径，共 24 组断言全部通过。
- 网关路径转换测试包含共同的网关/环境前缀及参数路径末尾的 `/?`。

| 情形 | 实测结果 |
| --- | --- |
| 类型 1 原始示例 | 两种注册顺序均命中第二条 |
| `/x/{aa}` 与 `/x/{bb}`，优先级及长度相同 | 先注册的路由命中 |
| 类型 2 原始示例 | 两种注册顺序均命中第二条 |
| 类型 2 末段参数缩短为 `{id}` | 两种注册顺序均命中 `batch` 路由 |
| 完整静态路径 `/x/batch` 与 `/x/{long_name}` | 两种注册顺序均命中静态路径 |
| 类型 2 中将 `batch` 路由的 priority 设为 10，另一条为默认值 | 两种注册顺序均命中 `batch` 路由 |

上述结论针对已验证版本及测试条件；未在生产 APISIX 实例上回放。不同 host、请求条件、优先级和匹配子路径配置可能影响实际候选路由，不应仅凭路径长度推断所有场景的最终命中结果。

## 上游依据

- [APISIX 参数路由文档](https://github.com/apache/apisix/blob/master/docs/en/latest/router-radixtree.md)：参数路由使用 `:name` 语法。
- [lua-resty-radixtree 文档](https://github.com/api7/lua-resty-radixtree/tree/v2.9.2#parameters-in-path)：参数匹配与路由优先级。
- [v2.9.2 路由排序实现](https://github.com/api7/lua-resty-radixtree/blob/v2.9.2/lib/resty/radixtree.lua#L196-L212)：同节点先比较 priority，再比较原始路径长度；相等时保留插入顺序。
- [v2.9.2 参数路由建树实现](https://github.com/api7/lua-resty-radixtree/blob/v2.9.2/lib/resty/radixtree.lua#L443-L463)：以首个参数前的静态前缀作为树索引。
- [v2.9.2 匹配入口](https://github.com/api7/lua-resty-radixtree/blob/v2.9.2/lib/resty/radixtree.lua#L763-L799)：候选列表返回首个满足条件的路由，完整静态路径先查询哈希表。
