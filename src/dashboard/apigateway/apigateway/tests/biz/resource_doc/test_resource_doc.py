from apigateway.biz.resource_doc.resource_doc import ResourceDocHandler


class TestResourceDocHandler:
    def test_get_resource_doc_tmpl(self):
        result = ResourceDocHandler.get_resource_doc_tmpl("bk-user", "zh")
        assert result != ""

        result = ResourceDocHandler.get_resource_doc_tmpl("bk-user", "en")
        assert result != ""

        result = ResourceDocHandler.get_resource_doc_tmpl("bk-user", "unknown")
        assert result == ""
