class TestResourceDocImportByArchiveApi:
    def test_post(self, request_view, mocker, fake_tgz_file, ignore_related_app_permission, fake_gateway):
        mocker.patch("apigateway.apis.open.resource_doc.views.ArchiveParser.parse", return_value=[])
        mocker.patch("apigateway.apis.open.resource_doc.views.ResourceDocImporter.import_docs")

        resp = request_view(
            method="POST",
            view_name="openapi.resource_doc.import.by_archive",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "file": fake_tgz_file,
            },
            format="multipart",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0


class TestResourceDocImportBySwaggerApi:
    def test_post(self, request_view, mocker, faker, ignore_related_app_permission, fake_gateway):
        mocker.patch("apigateway.apis.web.resource_doc.views.SwaggerParser.parse", return_value=[])
        mocker.patch("apigateway.apis.web.resource_doc.views.ResourceDocImporter.import_docs")

        resp = request_view(
            method="POST",
            view_name="openapi.resource_doc.import.by_swagger",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "swagger": faker.pystr(),
                "language": "zh",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
