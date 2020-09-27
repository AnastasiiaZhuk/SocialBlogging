import hashlib
from datetime import datetime
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
        self.assertFalse(u.can(Permissions.MODERATE))
        self.assertTrue(u.can(Permissions.WRITE))
        self.assertTrue(u.can(Permissions.COMMENT))
        self.assertFalse(u.can(Permissions.ADMIN))

    def test_moderate_role(self):
        Role.insert_role()

        role = Role.query.filter_by(name='Moderator').first()
        u = User(email='loh@gmail.com', password='alee', role=role)

        self.assertTrue(u.can(Permissions.FOLLOW))
        self.assertTrue(u.can(Permissions.WRITE))
        self.assertTrue(u.can(Permissions.MODERATE))
        self.assertTrue(u.can(Permissions.COMMENT))
        self.assertFalse(u.can(Permissions.ADMIN))

    def test_admin_role(self):
        Role.insert_role()
        role = Role.query.filter_by(name='Administrator').first()
        user = User(email='loh1@gmail.com', password='ale', role=role)

        self.assertTrue(user.can(Permissions.FOLLOW))
        self.assertTrue(user.can(Permissions.WRITE))
        self.assertTrue(user.can(Permissions.MODERATE))
        self.assertTrue(user.can(Permissions.COMMENT))
        self.assertTrue(user.can(Permissions.ADMIN))

    def test_timestamp(self):
        u = User(password='ale')
        db.session.add(u)
        db.session.commit()

        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3)

    def test_ping(self):
        u = User(password='ale')
        db.session.add(u)
        db.session.commit()

        time.sleep(3)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_avatar(self):
        u = User(email='ale@gmail.com', password='ale')
        url = 'http://www.gravatar.com/avatar/' + str(hashlib.md5(u.email.encode('utf-8')).hexdigest())

        with self.app.test_request_context('/'):
            avatar = u.gravatar()
            avatar_size = u.gravatar(size=256)
            avatar_rated = u.gravatar(rating='pg')
            avatar_retro = u.gravatar(default='retro')

        self.assertTrue(url in avatar)
        self.assertTrue('s=256' in avatar_size)
        self.assertTrue('r=pg' in avatar_rated)
        self.assertTrue('d=retro' in avatar_retro)

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permissions.FOLLOW))

    def test_reset_token(self):
        u = User(email='loh@gmail.com', password='ale')
        db.session.add(u)
        db.session.commit()

        token = u.generate_reset_token()
        self.assertTrue(User.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_reset_invalid_token(self):
        u = User(password='ale')
        db.session.add(u)
        db.session.commit()

        token = u.generate_reset_token()
        self.assertFalse(User.reset_password(token + 'b', 'beer'))
        self.assertTrue(u.verify_password('ale'))