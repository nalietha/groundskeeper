import json
import os
import tempfile
import unittest
from unittest import mock

from core.utils import load_json, get_local_ip


class LoadJsonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _path(self, name):
        return os.path.join(self.tmp, name)

    def test_loads_valid_json(self):
        path = self._path("data.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"a": 1, "b": [2, 3]}, f)
        self.assertEqual(load_json(path), {"a": 1, "b": [2, 3]})

    def test_missing_file_returns_default(self):
        self.assertEqual(load_json(self._path("nope.json"), default=[]), [])
        self.assertIsNone(load_json(self._path("nope.json")))

    def test_invalid_json_returns_default(self):
        path = self._path("bad.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not valid json,,,")
        self.assertEqual(load_json(path, default={"fallback": True}), {"fallback": True})

    def test_default_is_returned_by_identity(self):
        sentinel = ["shared"]
        result = load_json(self._path("missing.json"), default=sentinel)
        self.assertIs(result, sentinel)


class GetLocalIpTests(unittest.TestCase):
    def test_returns_string(self):
        ip = get_local_ip()
        self.assertIsInstance(ip, str)
        self.assertTrue(ip)

    def test_falls_back_when_socket_fails(self):
        with mock.patch("core.utils.socket.socket", side_effect=OSError("no network")):
            self.assertEqual(get_local_ip(), "127.0.0.1")
            self.assertEqual(get_local_ip(fallback="10.0.0.1"), "10.0.0.1")

    def test_uses_socket_result_when_available(self):
        fake_sock = mock.MagicMock()
        fake_sock.getsockname.return_value = ("192.168.1.42", 12345)
        with mock.patch("core.utils.socket.socket", return_value=fake_sock):
            self.assertEqual(get_local_ip(), "192.168.1.42")
        fake_sock.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
