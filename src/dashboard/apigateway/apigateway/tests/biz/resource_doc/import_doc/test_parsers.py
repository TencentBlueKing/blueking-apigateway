import pytest

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc.exceptions import NoResourceDocError
from apigateway.biz.resource_doc.import_doc.models import ArchiveDoc
from apigateway.biz.resource_doc.import_doc.parsers import ArchiveParser, BaseParser, SwaggerParser
from apigateway.core.models import Resource


class TestBaseParser:
    def test_enrich_docs(self, fake_resource_doc, faker):
        fake_gateway = fake_resource_doc.api
        fake_resource = Resource.objects.get(id=fake_resource_doc.resource_id)
        parser = BaseParser(fake_gateway.id)

        docs = [
            ArchiveDoc(
                resource_name="no_exist",
                language=DocLanguageEnum.ZH,
                content=faker.pystr(),
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].resource is None
        assert docs[0].resource_doc is None
        assert docs[0].content_changed is True

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum.ZH,
                content="new content",
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].resource == fake_resource
        assert docs[0].resource_doc == fake_resource_doc
        assert docs[0].content_changed is True

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum.ZH,
                content=fake_resource_doc.content,
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].content_changed is False


class TestArchiveParser:
    @pytest.mark.parametrize(
        "files, expected",
        [
            (
                {
                    "zh/get_user.md": "/path/to/zh/get_user.md",
                    "en/get_user.md": "/path/to/en/get_user.md",
                    "zh/create_user.md.j2": "/path/to/zh/create_user.md.j2",
                    "zz/get_user.md": "/path/to/zz/get_user.md",
                    "zh/get_user.txt": "/path/to/zh/get_user.txt",
                },
                [
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="get_user",
                        filename="zh/get_user.md",
                        resource_doc_path="/path/to/zh/get_user.md",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("en"),
                        resource_name="get_user",
                        filename="en/get_user.md",
                        resource_doc_path="/path/to/en/get_user.md",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="create_user",
                        filename="zh/create_user.md.j2",
                        resource_doc_path="/path/to/zh/create_user.md.j2",
                    ),
                ],
            )
        ],
    )
    def test_parse(self, files, expected):
        result = ArchiveParser(1)._parse(files)
        assert result == expected

    def test_parse__error(self):
        with pytest.raises(NoResourceDocError):
            ArchiveParser(1)._parse({})

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("zh/get_user.md", "zh"),
            ("en/get_user.md", "en"),
            ("zz/get_user.md", "zz"),
        ],
    )
    def test_extract_language(self, filename, expected):
        result = ArchiveParser(1)._extract_language(filename)
        assert result == expected

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("zh/get_user.md", "get_user"),
            ("en/get_user.md", "get_user"),
            ("zh/get_user.md.j2", "get_user"),
            ("zz/get_user.txt", None),
        ],
    )
    def test_extract_resource_name(self, filename, expected):
        result = ArchiveParser(1)._extract_resource_name(filename)
        assert result == expected


class TestSwagger:
    def test_parse(self, mocker):
        mocker.patch("apigateway.biz.resource_doc.import_doc.parsers.SwaggerParser._expand_swagger", return_value="")
        mocker.patch(
            "apigateway.biz.resource_doc.import_doc.parsers.SwaggerManager.load_from_swagger",
            return_value=mocker.MagicMock(
                **{
                    "validate.return_value": None,
                    "get_paths.return_value": {
                        "/user": {
                            "get": {
                                "operationId": "get_user",
                            }
                        }
                    },
                }
            ),
        )

        docs = SwaggerParser(1)._parse("swagger", DocLanguageEnum.ZH)
        assert docs[0].resource_name == "get_user"
        assert docs[0].language == DocLanguageEnum.ZH
        assert docs[0].content != ""
        assert docs[0].swagger != ""
