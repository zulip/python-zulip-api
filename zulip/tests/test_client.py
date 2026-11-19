import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from typing_extensions import override

import zulip
from zulip import ConfigNotFoundError


class TestCertBundle(TestCase):
    @override
    def setUp(self) -> None:
        # Avoid a real network request in Client.__init__, which calls
        # get_server_settings().
        patcher = patch.object(
            zulip.Client,
            "get_server_settings",
            return_value={"zulip_version": "10.0", "zulip_feature_level": 300},
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def make_client(self, cert_bundle: str) -> zulip.Client:
        return zulip.Client(
            email="bot@example.com",
            api_key="a" * 32,
            site="https://chat.zulip.org",
            cert_bundle=cert_bundle,
        )

    def test_cert_bundle_file(self) -> None:
        with tempfile.NamedTemporaryFile() as cert_file:
            client = self.make_client(cert_file.name)
            self.assertEqual(client.tls_verification, cert_file.name)

    def test_cert_bundle_directory(self) -> None:
        # The requests library also accepts a directory of CA certificates
        # (e.g. /etc/ssl/certs) as the verify parameter, so a directory
        # should be accepted as a cert bundle as well.
        with tempfile.TemporaryDirectory() as cert_dir:
            client = self.make_client(cert_dir)
            self.assertEqual(client.tls_verification, cert_dir)

    def test_cert_bundle_missing(self) -> None:
        missing = os.path.join(tempfile.gettempdir(), "zulip-nonexistent-cert-bundle")
        with self.assertRaises(ConfigNotFoundError) as cm:
            self.make_client(missing)
        self.assertEqual(str(cm.exception), f"tls bundle '{missing}' does not exist")
