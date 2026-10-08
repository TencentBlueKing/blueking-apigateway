# Dashboard Test Suite

Test paths mirror production ownership. Read the corresponding source module's
AGENTS.md when implementing its contract; source-layer guides are not ancestors
of this test tree. Runtime, EE activation and pytest commands come from the
Dashboard guide.

- Reuse `conftest.py` fixtures and `tests/utils/testing.py` helpers. Model fixtures
  commonly use `G()` from `django_dynamic_fixture`; version fixtures build
  snapshots through `ResourceVersionHandler.make_version()`.
- The shared `APIRequestFactory` gives requests a superuser and login cookie.
  Those defaults do not exercise permission denial or tenant isolation; override
  identity and context explicitly when that is the behavior under test.
- `pytest_sessionstart()` allows all Django databases for TestCase isolation.
  Preserve that setup when adding tests involving the default/bkcore databases.
- Fixture state is not interchangeable: editable Resource rows, ResourceVersion
  snapshots and ReleasedResource projections serve different consumers. Use
  the fixture matching the code's read path, especially for publish/MCP tests.
- Service package/export edits have an additional contract target:
  `tests/service/test_public_api_contract.py` (relative to the importable package).
