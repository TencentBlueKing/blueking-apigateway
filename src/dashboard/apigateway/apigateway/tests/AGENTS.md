# Dashboard Test Suite

Test paths mirror production ownership. Read the corresponding source module's
AGENTS.md when implementing its contract; source-layer guides are not ancestors
of this test tree. Runtime, EE activation and pytest commands come from the
Dashboard guide.

- Mark schema/data migration tests with `pytest.mark.migration` (module-level
  `pytestmark` is suitable for migration-only files). Preserve existing
  `django_db(transaction=True)` requirements. Run them through `test-migrations`
  or the full `test` gate; `test-fast` deliberately excludes this marker.
- Tests must remain isolated under `worksteal` scheduling. If a real shared
  resource requires tests to stay together, document the constraint and use an
  appropriate explicit scheduler/group for that target.
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
