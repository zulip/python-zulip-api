import os
import unittest
from unittest.mock import patch

import zulip


class TestConfigHelpers(unittest.TestCase):
    def test_zulip_env_vars_are_present(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(zulip.zulip_env_vars_are_present())

        with patch.dict(os.environ, {"ZULIP_EMAIL": "bot@example.com"}, clear=True):
            self.assertFalse(zulip.zulip_env_vars_are_present())

        with patch.dict(
            os.environ,
            {"ZULIP_EMAIL": "bot@example.com", "ZULIP_API_KEY": "secret_key"},
            clear=True,
        ):
            self.assertFalse(zulip.zulip_env_vars_are_present())

        with patch.dict(
            os.environ,
            {
                "ZULIP_EMAIL": "bot@example.com",
                "ZULIP_API_KEY": "secret_key",
                "ZULIP_SITE": "https://zulip.example.com",
            },
            clear=True,
        ):
            self.assertTrue(zulip.zulip_env_vars_are_present())

    def test_exit_gracefully_existing_file(self) -> None:
        # Should return cleanly without exiting
        zulip.exit_gracefully_if_zulip_config_is_missing(__file__)

    def test_exit_gracefully_nonexistent_file(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            zulip.exit_gracefully_if_zulip_config_is_missing("/nonexistent/path/to/zuliprc")
        self.assertEqual(cm.exception.code, 1)

    def test_exit_gracefully_with_env_vars(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ZULIP_EMAIL": "bot@example.com",
                "ZULIP_API_KEY": "secret_key",
                "ZULIP_SITE": "https://zulip.example.com",
            },
            clear=True,
        ):
            zulip.exit_gracefully_if_zulip_config_is_missing(None)

    def test_exit_gracefully_default_config_exists(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch("zulip.get_default_config_filename", return_value=__file__):
                zulip.exit_gracefully_if_zulip_config_is_missing(None, allow_default_config=True)

    def test_exit_gracefully_missing_all(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch("zulip.get_default_config_filename", return_value="/nonexistent/zuliprc"):
                with self.assertRaises(SystemExit) as cm:
                    zulip.exit_gracefully_if_zulip_config_is_missing(
                        None, allow_default_config=True
                    )
                self.assertEqual(cm.exception.code, 1)

    def test_exit_gracefully_disallow_default_config(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch("zulip.get_default_config_filename", return_value=__file__):
                with self.assertRaises(SystemExit) as cm:
                    zulip.exit_gracefully_if_zulip_config_is_missing(
                        None, allow_default_config=False
                    )
                self.assertEqual(cm.exception.code, 1)
