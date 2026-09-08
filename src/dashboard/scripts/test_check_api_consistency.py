"""The active edition's route extension is part of the published API contract."""

from check_api_consistency import APIConsistencyChecker


def test_collect_edition_routes(tmp_path):
    routes = tmp_path / "src/dashboard/apigateway/apigateway/apis/v2/inner"
    routes.mkdir(parents=True)
    (routes / "urls.py").write_text("urlpatterns = []\n")
    (routes / "edition_urls.py").write_text(
        'urlpatterns = [path("esb/systems/", views.EsbSystemListApi.as_view(), name="esb.list")]\n'
    )
    checker = APIConsistencyChecker(str(tmp_path))
    checker.collect_code("v2_inner")
    assert checker.code_routes["/api/v2/inner/esb/systems/"]["view_class"] == "EsbSystemListApi"
