from apigateway.biz.sdk.managers.base import BaseSDKManager as BaseSDKManager
from apigateway.biz.sdk.managers.mixins import SDKManagerMixin as SDKManagerMixin
from apigateway.utils.factory import TypeFactory

SDKManagerFactory: TypeFactory[BaseSDKManager]
PythonLegacySDKManager: type[BaseSDKManager] | None
