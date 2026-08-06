#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import json
import logging
from typing import TYPE_CHECKING, ClassVar, Dict, Iterable, List, Optional, Tuple, Type

from django.utils.encoding import force_str
from etcd3.utils import prefix_range_end

from apigateway.controller.registry.base import Registry
from apigateway.utils.etcd import get_etcd_client

if TYPE_CHECKING:
    import etcd3

    from apigateway.controller.models import ApisixModel

logger = logging.getLogger(__name__)


class AtomicReplaceConflictError(RuntimeError):
    """etcd 事务 compare 失败：前缀在快照后发生并发变更，成功分支未执行"""


class EtcdRegistry(Registry):
    """Etcd 注册配置中心，数据实际存储在 etcd 中"""

    registry_type: ClassVar[str] = "etcd"

    def __init__(self, key_prefix: str, etcd_client: "etcd3.Etcd3Client" = None):
        super().__init__(key_prefix)
        self._etcd_client = etcd_client or get_etcd_client()

    def _delete_by_key(self, key: str) -> bool:
        return self._etcd_client.delete(key)

    def apply_resource(self, resource: ApisixModel) -> bool:
        payload = resource.model_dump_json(exclude_none=True)
        self._etcd_client.put(self._get_key(resource.kind, resource.id), payload)
        return True

    def sync_resources_by_key_prefix(self, resources: List[ApisixModel]) -> List[ApisixModel]:
        """按 key_prefix 同步资源，若 key_prefix 下的资源不在待同步资源列表中，将被删除；返回同步失败的资源列表"""

        sync_fail_resources = []
        remaining_keys = self._get_exist_keys_by_key_prefix()

        for resource in resources:
            key = self._get_key(resource.kind, resource.id)
            remaining_keys.pop(key, None)
            if not self.apply_resource(resource):
                sync_fail_resources.append(resource)

        for key in remaining_keys:
            if not self._delete_by_key(key):
                logger.warning(
                    "failed to remove key [%s] from registry %s",
                    key,
                    self.registry_type,
                )

        return sync_fail_resources

    def replace_resources_by_key_prefix_atomically(
        self,
        resources: List[ApisixModel],
        *,
        expected_max_mod_revision: Optional[int] = None,
    ) -> None:
        """在单个 etcd 事务内，将 key_prefix 下的数据整体替换为 resources

        DANGEROUS: key_prefix 下所有不属于 resources 的 key 都会被删除；resources 为空时，
        key_prefix 下的所有 key 都会被删除。调用方必须先确认 key_prefix 的范围。

        etcd 拒绝同一事务内 PUT key 落在 DELETE range 内（duplicate key given in txn request），
        因此这里按排序后的 PUT key 把 key_prefix 切分为互不重叠、且不包含任何 PUT key 的
        DELETE range，保证删除与写入仍在同一事务内完成。

        传入 expected_max_mod_revision 时，事务会要求前缀内所有 key 的 mod_revision
        都小于 revision+1，用于关闭“复查通过到提交”之间的并发写入窗口；compare 失败时
        不会执行任何 DELETE/PUT，并抛出 AtomicReplaceConflictError。
        """
        put_items = self._get_sorted_put_items(resources)
        delete_ops = [
            self._etcd_client.transactions.delete(range_start, range_end=range_end)
            for range_start, range_end in self._get_gap_delete_ranges([key.encode() for key, _ in put_items])
        ]
        put_ops = [self._etcd_client.transactions.put(key, payload) for key, payload in put_items]
        compare = []
        if expected_max_mod_revision is not None:
            compare = [
                self._etcd_client.transactions.mod(
                    self.key_prefix,
                    range_end=prefix_range_end(self.key_prefix.encode()),
                )
                < (expected_max_mod_revision + 1)
            ]
        succeeded, _ = self._etcd_client.transaction(
            compare=compare,
            success=[*delete_ops, *put_ops],
            failure=[],
        )
        if not succeeded:
            if expected_max_mod_revision is not None:
                raise AtomicReplaceConflictError(f"concurrent modification under etcd prefix: {self.key_prefix}")
            raise RuntimeError(f"failed to atomically replace etcd resources under prefix: {self.key_prefix}")

    def _get_sorted_put_items(self, resources: List[ApisixModel]) -> List[Tuple[str, str]]:
        """按 etcd 的 key 字节序返回 (key, payload)，并拒绝前缀外的 key 与重复 key"""
        items = []
        for resource in resources:
            key = self._get_key(resource.kind, resource.id)
            if not key.startswith(self.key_prefix) or key == self.key_prefix:
                raise ValueError(f"resource key is outside of the registry key prefix: {self.key_prefix}")

            items.append((key, resource.model_dump_json(exclude_none=True)))

        items.sort(key=lambda item: item[0].encode())
        keys = [key for key, _ in items]
        if len(set(keys)) != len(keys):
            raise ValueError(f"duplicated resource key under the registry key prefix: {self.key_prefix}")

        return items

    def _get_gap_delete_ranges(self, put_keys: List[bytes]) -> List[Tuple[bytes, bytes]]:
        """返回 key_prefix 下、跳过全部 put_keys 的删除区间；put_keys 必须已按字节序排序"""
        prefix = self.key_prefix.encode()
        prefix_end = prefix_range_end(prefix)

        ranges = []
        range_start = prefix
        for key in put_keys:
            if range_start < key:
                ranges.append((range_start, key))
            # key + b"\x00" 是 etcd 字节序中紧跟 key 之后的最小 key，用于把 key 本身排除在区间外
            range_start = key + b"\x00"

        if range_start < prefix_end:
            ranges.append((range_start, prefix_end))

        return ranges

    def _get_exist_keys_by_key_prefix(self) -> Dict[str, bool]:
        exist_keys: Dict[str, bool] = {}

        for _, kv_metadata in self._etcd_client.get_prefix(self.key_prefix, keys_only=True):
            exist_keys[force_str(kv_metadata.key)] = True

        return exist_keys

    def delete_resources_by_key_prefix(self):
        """删除 key_prefix 下的所有资源"""
        self._etcd_client.delete_prefix(self.key_prefix)

    def iter_by_type(self, resource_type: Type[ApisixModel]) -> Iterable[ApisixModel]:
        for payload, _ in self._etcd_client.get_prefix(self._get_kind_key_prefix(resource_type.kind)):
            try:
                value = json.loads(payload)
                yield resource_type(**value)
            except Exception as err:  # pylint: disable=broad-except
                logger.warning("deserialize resource %s failed: %s", resource_type, err)
                continue
