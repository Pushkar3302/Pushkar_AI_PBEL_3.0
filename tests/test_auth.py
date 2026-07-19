"""
Unit Tests for Authentication Service.
"""

import time
import unittest
from authentication.auth_service import AuthService
from database.connection import get_db, init_db
from database.models import RoleEnum


class TestAuthService(unittest.TestCase):

    def test_password_hashing(self):
        password = "SuperSecretPassword123"
        hashed = AuthService.hash_password(password)
        self.assertNotEqual(hashed, password)
        self.assertTrue(AuthService.verify_password(password, hashed))
        self.assertFalse(AuthService.verify_password("WrongPassword", hashed))

    def test_user_registration_and_auth(self):
        init_db()
        unique_id = int(time.time() * 1000)
        username = f"test_student_{unique_id}"
        email = f"student_{unique_id}@test.edu"

        with get_db() as db:
            ok, msg, user = AuthService.register_user(
                db=db,
                username=username,
                email=email,
                password="Password123!",
                full_name="Test Student",
                role_name=RoleEnum.STUDENT.value,
                department_code="CS"
            )
            self.assertTrue(ok, msg)
            self.assertIsNotNone(user)

            # Authenticate
            auth_ok, auth_msg, auth_user = AuthService.authenticate_user(
                db, username, "Password123!"
            )
            self.assertTrue(auth_ok)
            self.assertEqual(auth_user.email, email)


if __name__ == "__main__":
    unittest.main()
