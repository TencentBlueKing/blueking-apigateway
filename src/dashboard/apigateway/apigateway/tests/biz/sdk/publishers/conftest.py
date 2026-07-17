import pytest

from apigateway.biz.sdk.artifacts import create_built_artifact
from apigateway.biz.sdk.config import SDKLanguageConfig


@pytest.fixture
def built_artifact(tmp_path):
    def factory(artifact_type, filename, content=b"content"):
        path = tmp_path / filename
        path.write_bytes(content)
        return create_built_artifact(artifact_type, path, allowed_roots=(tmp_path,))

    return factory


@pytest.fixture
def python_config():
    return SDKLanguageConfig(
        language="python",
        generator_name="python",
        project_name="bkapi-demo",
        package_name="bkapi_demo",
        package_version="1.2.3",
        additional_properties={
            "packageName": "bkapi_demo",
            "packageVersion": "1.2.3",
            "projectName": "bkapi-demo",
            "buildSystem": "poetry",
        },
        native_distributor="pypi",
    )


@pytest.fixture
def java_config():
    return SDKLanguageConfig(
        language="java",
        generator_name="java",
        project_name="bkapi-demo",
        package_name="com.tencent.bkapi.demo",
        package_version="1.2.3",
        additional_properties={
            "groupId": "com.tencent.bkapi",
            "artifactId": "bkapi-demo",
            "artifactVersion": "1.2.3",
            "invokerPackage": "com.tencent.bkapi.demo",
            "apiPackage": "com.tencent.bkapi.demo.api",
            "modelPackage": "com.tencent.bkapi.demo.model",
            "library": "native",
        },
        native_distributor="maven",
    )
