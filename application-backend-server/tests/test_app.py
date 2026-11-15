"""Run with: python -m unittest discover -s application-backend-server/tests -v.

Use real RS256 tokens with in-memory test keys. MariaDB and Keycloak network
calls are mocked; these tests do not require or change a running demo stack.
"""

import datetime
import importlib.util
import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import rsa
from jose import jwk, jwt


SERVER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("app", SERVER / "app.py")
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)
# Resolve templates independently of the directory used to launch unittest.
backend.app.template_folder = str(SERVER / "templates")


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public, cls.private = rsa.newkeys(2048)
        cls.jwks = {"keys": [jwk.construct(
            cls.public.save_pkcs1(), algorithm="RS256"
        ).to_dict()]}

    def setUp(self):
        self.client = backend.app.test_client()
        backend._JWKS = None
        backend._TS = 0

    def token(self, **overrides):
        claims = {
            "iss": f"http://localhost:8081/auth/realms/{backend.REALM}",
            "aud": backend.AUDIENCE,
            "exp": int(time.time()) + 300,
            "preferred_username": "sv01",
        }
        claims.update(overrides)
        return jwt.encode(claims, self.private.save_pkcs1(), algorithm="RS256")

    def secure(self, token):
        return self.client.get("/secure", headers={"Authorization": f"Bearer {token}"})

    def test_hello(self):
        response = self.client.get("/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Hello from App Server!"})

    def test_students_json(self):
        response = self.client.get("/student")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, json.loads((SERVER / "students.json").read_text()))

    def test_students_html_and_explicit_json(self):
        response = self.client.get("/student", headers={"Accept": "text/html"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student list (JSON)", response.data)
        response = self.client.get("/student?format=json", headers={"Accept": "text/html"})
        self.assertTrue(response.is_json)

    def test_missing_bearer(self):
        self.assertEqual(self.client.get("/secure").status_code, 401)
        response = self.client.get("/secure", headers={"Authorization": "Basic demo"})
        self.assertEqual(response.status_code, 401)

    def test_valid_token_and_jwks_cache(self):
        with patch.object(backend.requests, "get") as fetch:
            fetch.return_value.json.return_value = self.jwks
            for _ in range(2):
                response = self.secure(self.token())
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["preferred_username"], "sv01")
            fetch.assert_called_once_with(backend.JWKS_URL, timeout=5)

    def test_invalid_token_claims(self):
        with patch.object(backend.requests, "get") as fetch:
            fetch.return_value.json.return_value = self.jwks
            for claims in ({"aud": "other"}, {"exp": int(time.time()) - 60},
                           {"iss": "http://localhost/auth/realms/other"}):
                with self.subTest(claims=claims):
                    self.assertEqual(self.secure(self.token(**claims)).status_code, 401)

    def test_invalid_signature_and_malformed_token(self):
        token = self.token()
        header, payload, signature = token.split(".")
        signature = ("A" if signature[0] != "A" else "B") + signature[1:]
        with patch.object(backend.requests, "get") as fetch:
            fetch.return_value.json.return_value = self.jwks
            for invalid in (f"{header}.{payload}.{signature}", "invalid-token"):
                self.assertEqual(self.secure(invalid).status_code, 401)

    def test_jwks_refresh_after_key_rotation(self):
        backend._JWKS = {"keys": []}
        backend._TS = time.time()
        with patch.object(backend.requests, "get") as fetch:
            fetch.return_value.json.return_value = self.jwks
            self.assertEqual(self.secure(self.token()).status_code, 200)
            self.assertEqual(fetch.call_count, 1)

    def test_keycloak_unavailable(self):
        with patch.object(backend.requests, "get", side_effect=backend.requests.ConnectionError("offline")):
            self.assertEqual(self.secure(self.token()).status_code, 401)

    def test_database_json_and_html(self):
        with patch.object(backend.pymysql, "connect") as connect:
            connection = connect.return_value
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.fetchall.side_effect = lambda: [{
                "id": 1, "student_id": "523H0145", "fullname": "Nguyễn Nhựt Khang",
                "dob": datetime.date(2005, 3, 15), "major": "Computer Science",
            }]
            response = self.client.get("/students-db")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json[0]["dob"], "2005-03-15")
            response = self.client.get("/students-db?format=html")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Student list (MariaDB)", response.data)
            self.assertEqual(connection.close.call_count, 2)

    def test_database_unavailable(self):
        with patch.object(backend.pymysql, "connect", side_effect=RuntimeError("offline")):
            self.assertEqual(self.client.get("/students-db").status_code, 503)

    def test_database_connection_closed_after_query_error(self):
        with patch.object(backend.pymysql, "connect") as connect:
            connection = connect.return_value
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.execute.side_effect = RuntimeError("query failed")
            self.assertEqual(self.client.get("/students-db").status_code, 503)
            connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
