import os
import unittest
from unittest import mock

from copilot import config


class HostResolutionTest(unittest.TestCase):
    def test_auto_is_loopback_outside_the_container(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("APP_HOME", None)
            self.assertEqual(config.resolve_host("auto"), "127.0.0.1")
            self.assertEqual(config.resolve_host(""), "127.0.0.1")

    def test_auto_is_the_host_gateway_alias_inside_app_lab(self):
        with mock.patch.dict(os.environ, {"APP_HOME": "/home/arduino/ArduinoApps/math-copilot"}), \
                mock.patch("os.path.isdir", return_value=True):
            self.assertEqual(config.resolve_host("auto"), config.APP_LAB_HOST_ALIAS)

    def test_explicit_value_wins(self):
        self.assertEqual(config.resolve_host("172.17.0.1"), "172.17.0.1")

    def test_config_has_resolved_hosts(self):
        self.assertIn(config.CONFIG["LLM_HOST"], ("127.0.0.1", config.APP_LAB_HOST_ALIAS))
        self.assertEqual(config.CONFIG["EMBED_HOST"], config.CONFIG["LLM_HOST"])


if __name__ == "__main__":
    unittest.main()
