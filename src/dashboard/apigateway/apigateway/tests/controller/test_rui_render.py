"""
Unit tests for the URI renderer implementation.
Tests the Python implementation to ensure it matches the Go behavior.
"""

import unittest

from apigateway.controller.uri_render import UpstreamURIRender, URIRender


class TestURIRender(unittest.TestCase):
    """Test cases for URIRender class."""

    def setUp(self):
        self.renderer = URIRender()
        self.vars = {"stage": "prod", "version": "v1", "region": "us-west"}

    def test_basic_env_replacement(self):
        """Test basic environment variable replacement."""
        source = "/api/{env.stage}/users"
        expected = "/api/prod/users"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)

    def test_basic_param_replacement(self):
        """Test basic path parameter replacement."""
        source = "/api/users/{userId}"
        expected = "/api/users/:userId"
        result = self.renderer.render(source, {})
        self.assertEqual(result, expected)

    def test_mixed_replacement(self):
        """Test mixed environment variables and path parameters."""
        source = "/api/{env.stage}/{env.version}/users/{userId}/posts/{postId}"
        expected = "/api/prod/v1/users/:userId/posts/:postId"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)

    def test_missing_env_var(self):
        """Test behavior when environment variable is missing."""
        source = "/api/{env.missing}/users/{userId}"
        expected = "/api/{env.missing}/users/:userId"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)

    def test_no_variables(self):
        """Test when no variables are present."""
        source = "/api/users/list"
        expected = "/api/users/list"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)

    def test_empty_vars_dict(self):
        """Test with empty variables dictionary."""
        source = "/api/{env.stage}/users/{userId}"
        expected = "/api/{env.stage}/users/:userId"
        result = self.renderer.render(source, {})
        self.assertEqual(result, expected)


class TestUpstreamURIRender(unittest.TestCase):
    """Test cases for UpstreamURIRender class."""

    def setUp(self):
        self.renderer = UpstreamURIRender()
        self.vars = {"stage": "prod", "version": "v1", "region": "us-west"}

    def test_basic_env_replacement(self):
        """Test basic environment variable replacement."""
        source = "/api/{env.stage}/users"
        expected = "/api/prod/users"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)

    def test_basic_param_replacement(self):
        """Test basic path parameter replacement with $ syntax."""
        source = "/api/users/{userId}"
        expected = "/api/users/${userId}"
        result = self.renderer.render(source, {})
        self.assertEqual(result, expected)

    def test_mixed_replacement(self):
        """Test mixed environment variables and path parameters."""
        source = "/api/{env.stage}/{env.version}/users/{userId}/posts/{postId}"
        expected = "/api/prod/v1/users/${userId}/posts/${postId}"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)

    def test_missing_env_var(self):
        """Test behavior when environment variable is missing."""
        source = "/api/{env.missing}/users/{userId}"
        expected = "/api/{env.missing}/users/${userId}"
        result = self.renderer.render(source, self.vars)
        self.assertEqual(result, expected)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_multiple_same_env_vars(self):
        """Test multiple occurrences of the same environment variable."""
        renderer = URIRender()
        vars_dict = {"stage": "dev"}
        source = "/api/{env.stage}/users/{env.stage}/list"
        expected = "/api/dev/users/dev/list"
        result = renderer.render(source, vars_dict)
        self.assertEqual(result, expected)

    def test_multiple_same_params(self):
        """Test multiple occurrences of the same parameter."""
        renderer = URIRender()
        source = "/api/{userId}/profile/{userId}/settings"
        expected = "/api/:userId/profile/:userId/settings"
        result = renderer.render(source, {})
        self.assertEqual(result, expected)

    def test_nested_braces_not_supported(self):
        """Test that nested braces are not processed (should remain as-is)."""
        renderer = URIRender()
        source = "/api/{env.{stage}}/users"
        # Should not process nested braces
        expected = "/api/{env.{stage}}/users"
        result = renderer.render(source, {"stage": "prod"})
        self.assertEqual(result, expected)

    def test_empty_string(self):
        """Test with empty string input."""
        renderer = URIRender()
        result = renderer.render("", {})
        self.assertEqual(result, "")

    def test_malformed_env_syntax(self):
        """Test malformed environment variable syntax."""
        renderer = URIRender()
        vars_dict = {"stage": "prod"}

        # Missing closing brace
        source1 = "/api/{env.stage/users"
        result1 = renderer.render(source1, vars_dict)
        self.assertEqual(result1, "/api/{env.stage/users")

        # Missing env prefix
        source2 = "/api/{stage}/users"
        expected2 = "/api/:stage/users"  # Should be treated as parameter
        result2 = renderer.render(source2, vars_dict)
        self.assertEqual(result2, expected2)


if __name__ == "__main__":
    unittest.main()
