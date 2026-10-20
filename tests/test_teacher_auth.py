import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

from src import teacher_auth
from src.app import app


class TeacherAuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.teachers_file = Path(self.temporary_directory.name) / "teachers.json"
        self.teachers_file.write_text(
            json.dumps({"teachers": {"coach": teacher_auth.hash_password("correct horse")}}),
            encoding="utf-8",
        )
        self.teachers_file_patch = patch.object(teacher_auth, "TEACHERS_FILE", self.teachers_file)
        self.teachers_file_patch.start()
        self.addCleanup(self.teachers_file_patch.stop)
        self.addCleanup(self.temporary_directory.cleanup)

    def test_password_hash_is_salted_and_verifiable(self):
        first_hash = teacher_auth.hash_password("correct horse")
        second_hash = teacher_auth.hash_password("correct horse")

        self.assertNotEqual(first_hash["salt"], second_hash["salt"])
        self.assertTrue(teacher_auth.verify_password("correct horse", first_hash))
        self.assertFalse(teacher_auth.verify_password("wrong password", first_hash))

    def test_session_token_expires_and_detects_tampering(self):
        token = teacher_auth.create_session_token("coach", now=100)

        self.assertEqual(teacher_auth.get_session_username(token, now=101), "coach")
        self.assertIsNone(
            teacher_auth.get_session_username(
                token, now=100 + teacher_auth.SESSION_DURATION_SECONDS
            )
        )
        self.assertIsNone(teacher_auth.get_session_username(token + "x", now=101))

    def test_teacher_dependency_rejects_anonymous_request(self):
        request = Request({"type": "http", "headers": [], "method": "GET", "path": "/"})

        with self.assertRaises(HTTPException) as raised:
            teacher_auth.require_teacher(request)

        self.assertEqual(raised.exception.status_code, 401)

    def test_teacher_dependency_accepts_valid_session(self):
        token = teacher_auth.create_session_token("coach")
        request = Request({
            "type": "http",
            "headers": [(b"cookie", f"{teacher_auth.SESSION_COOKIE_NAME}={token}".encode())],
            "method": "GET",
            "path": "/",
        })

        self.assertEqual(teacher_auth.require_teacher(request), "coach")

    def test_only_activity_mutations_require_teacher_authentication(self):
        routes = {route.path: route for route in app.routes if hasattr(route, "dependant")}

        for path in (
            "/activities/{activity_name}/signup",
            "/activities/{activity_name}/unregister",
        ):
            dependencies = routes[path].dependant.dependencies
            self.assertIn(teacher_auth.require_teacher, [dependency.call for dependency in dependencies])

        self.assertEqual(routes["/activities"].dependant.dependencies, [])


if __name__ == "__main__":
    unittest.main()