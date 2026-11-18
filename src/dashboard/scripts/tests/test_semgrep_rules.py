"""Exercise project rules with real Semgrep scans, including path filtering."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parents[2]
RULE_ID = "001-no-legacy-response"
LEGACY_RESPONSE = """\
from apigateway.utils.responses import V1OKJsonResponse
response = V1OKJsonResponse(data={})
"""


class TestSemgrepRules(unittest.TestCase):
    def scan(self, files):
        with tempfile.TemporaryDirectory(prefix="dashboard-semgrep-") as directory:
            root = Path(directory)
            for name, source in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
            result = subprocess.run(
                [
                    shutil.which("semgrep") or "semgrep",
                    "scan",
                    "--config",
                    str(DASHBOARD / ".semgrep/rules"),
                    "--error",
                    "--strict",
                    "--metrics=off",
                    "--disable-version-check",
                    "--disable-nosem",
                    "--no-rewrite-rule-ids",
                    "--json",
                    ".",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertIn(result.returncode, (0, 1), result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["errors"], [], result.stderr)
            return result.returncode, output["results"]

    def test_blocks_calls_aliases_and_other_class_references(self):
        sources = {
            "direct": LEGACY_RESPONSE,
            "alias": "from apigateway.utils.responses import V1FailJsonResponse as Fail\nresponse = Fail('bad')\n",
            "module_alias": "from apigateway.utils import responses as r\nresponse = r.V1OKJsonResponse()\n",
            "qualified": "import apigateway.utils.responses\nresponse = apigateway.utils.responses.V1FailJsonResponse('bad')\n",
            "callback": "from apigateway.utils.responses import V1OKJsonResponse\nresponse_class = V1OKJsonResponse\n",
            "subclass": "from apigateway.utils.responses import V1OKJsonResponse\nclass Response(V1OKJsonResponse):\n    pass\n",
            "nosemgrep": LEGACY_RESPONSE.rstrip() + "  # nosemgrep: 001-no-legacy-response\n",
        }
        files = {f"apigateway/apigateway/apis/web/demo/{name}.py": source for name, source in sources.items()}
        status, findings = self.scan(files)
        self.assertEqual(status, 1)
        self.assertCountEqual([finding["path"] for finding in findings], files)
        self.assertEqual({finding["check_id"] for finding in findings}, {RULE_ID})

    def test_limits_rule_to_modern_apis_including_editions(self):
        blocked = [
            "apis/web/demo/views.py",
            "apis/v2/open/views.py",
            "apis/v2/inner/views.py",
            "apis/v2/sync/views.py",
            "editions/ee/apis/web/demo/views.py",
            "editions/te/apis/v2/open/views.py",
        ]
        allowed = [
            "apis/open/demo/views.py",
            "editions/ee/apis/open/demo/views.py",
            "utils/responses.py",
            "tests/apis/web/demo/test_views.py",
            "apis/web/demo/migrations/0001_initial.py",
        ]
        prefix = "apigateway/apigateway/"
        status, findings = self.scan({prefix + name: LEGACY_RESPONSE for name in blocked + allowed})
        self.assertEqual(status, 1)
        self.assertCountEqual([finding["path"] for finding in findings], [prefix + name for name in blocked])

    def test_allows_standard_responses_and_unrelated_class_names(self):
        source = """\
from apigateway.utils.responses import OKJsonResponse, FailJsonResponse
from rest_framework.response import Response
from another_package import V1OKJsonResponse

ok = OKJsonResponse(data={})
failed = FailJsonResponse(status=400, code='bad', message='bad')
drf = Response({})
unrelated = V1OKJsonResponse()
"""
        status, findings = self.scan({"apigateway/apigateway/apis/web/demo/views.py": source})
        self.assertEqual(status, 0)
        self.assertEqual(findings, [])
