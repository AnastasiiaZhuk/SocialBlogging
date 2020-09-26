import unittest
import time

from app import create_app, db
from app.models import User, AnonymousUser, Role, Permissions


class UserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_password(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='dog')
        self.assertTrue(u.verify_password('dog'))
        self.assertFalse(u.verify_password('cat'))

    def test_passwords_random_hash(self):
        user1 = User(password='wine')
        user2 = User(password='beer')
        self.assertTrue(user1.password_hash != user2.password_hash)

    def test_valid_confirm_token(self):
        u = User(password='ale')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirm_token(self):
        u1 = User(password='ale')
        u2 = User(password='ale')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expiration(self):
        u = User(password='ale')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_user_role(self):
        Role.insert_role()
        u = User(email='loh@gmail.com', password='ale')
        self.assertTrue(u.can(Permissions.FOLLOW))
        self.assertFalse(u.can(Permissions.MODERATE_COMMENTS))
        self.assertTrue(u.can(Permissions.WRITE_ARTICLES))
        self.assertTrue(u.can(Permissions.COMMENT))
        self.assertFalse(u.can(Permissions.ADMINISTER))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permissions.FOLLOW))



