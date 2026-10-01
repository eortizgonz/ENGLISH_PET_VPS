"""Integration checks using PostgreSQL TEMP tables; no real accounts or email."""
import unittest
from unittest.mock import patch
import api_server as app
import password_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.db = app.PgCompatConnection()
        self.real_close = self.db.close
        self.db.close = lambda: None
        for sql in [
            'CREATE TEMP TABLE users(id bigint PRIMARY KEY,email text,username text,disabled integer,password_hash text)',
            'CREATE TEMP TABLE account_tokens(token text PRIMARY KEY,user_id bigint,kind text,created_at text,expires_at text,used_at text)',
            'CREATE TEMP TABLE sessions(token text,user_id bigint)',
            'CREATE TEMP TABLE login_attempts(email text)',
        ]:
            self.db.execute(sql)
        self.db.raw.execute("INSERT INTO users VALUES(1,'learner@example.com','learner',0,'old'),(2,'disabled@example.com','disabled',1,'old')")
        self.db.commit()
        self.clock = app.now()
        self.expiry = app.iso_after(minutes=30)
        self.audit = lambda *args: None

    def tearDown(self):
        self.real_close()

    def issue(self, email='learner@example.com'):
        return recovery.issue_token(lambda: self.db, email, self.clock, self.expiry, self.audit)

    def redeem(self, token):
        return recovery.redeem_token(lambda: self.db, token, 'new-hash', self.clock, self.audit)

    def test_single_use_hash_sessions_and_lockout(self):
        token = self.issue()
        self.assertNotEqual(token, self.db.execute('SELECT token FROM account_tokens').fetchone()['token'])
        self.db.execute("INSERT INTO sessions VALUES('old-session',1)")
        self.db.execute("INSERT INTO login_attempts VALUES('learner')")
        self.assertIsNone(self.redeem(token))
        self.assertEqual(self.redeem(token), 'invalid_token')
        self.assertEqual(self.db.execute('SELECT password_hash FROM users WHERE id=1').fetchone()['password_hash'], 'new-hash')
        self.assertFalse(self.db.execute('SELECT * FROM sessions').fetchall())
        self.assertFalse(self.db.execute('SELECT * FROM login_attempts').fetchall())

    def test_expired_invalid_and_disabled(self):
        self.assertIsNone(self.issue('absent@example.com'))
        self.assertIsNone(self.issue('disabled@example.com'))
        self.assertEqual(self.redeem('invalid'), 'invalid_token')
        token = self.issue()
        self.db.execute('UPDATE account_tokens SET expires_at=?', (app.iso_after(minutes=-1),))
        self.assertEqual(self.redeem(token), 'expired_token')
        self.db.execute('UPDATE account_tokens SET expires_at=?', (self.expiry,))
        self.db.execute('UPDATE users SET disabled=1 WHERE id=1')
        self.assertEqual(self.redeem(token), 'invalid_token')

    def test_throttle_and_replacement(self):
        old = self.issue()
        self.assertIsNone(self.issue())
        self.db.execute('UPDATE account_tokens SET created_at=?', (app.iso_after(minutes=-2),))
        new = self.issue()
        self.assertEqual(self.redeem(old), 'invalid_token')
        self.assertIsNone(self.redeem(new))

    def test_public_response_does_not_disclose_token_or_account(self):
        handler = object.__new__(app.Handler)
        handler.path = '/api/forgot-password'
        handler.client_address = ('127.0.0.1', 1)
        handler.json = lambda obj, status=200: (obj, status)
        with patch.object(app, 'conn', lambda: self.db), patch.object(app, 'audit', self.audit), patch.object(app, 'rate_ok', return_value=True), patch.object(app, 'email_configured', return_value=True), patch.object(app, 'send_email', return_value=True) as mail:
            handler.body = lambda: {'email': 'learner@example.com'}
            known = handler.do_POST()
            handler.body = lambda: {'email': 'absent@example.com'}
            self.assertEqual(known, handler.do_POST())
            self.assertEqual(set(known[0]), {'ok', 'message'})
            self.assertEqual(mail.call_count, 1)
            self.assertIn('?reset_token=', mail.call_args.args[2])

    def test_smtp_uses_tls_and_authentication(self):
        with patch.object(app, 'SMTP_HOST', 'smtp.gmail.com'), patch.object(app, 'SMTP_FROM', 'sender@gmail.com'), patch.object(app, 'SMTP_USER', 'sender@gmail.com'), patch.object(app, 'SMTP_PASSWORD', 'test-only'), patch.object(app, 'SMTP_TLS', True), patch.object(app.smtplib, 'SMTP') as smtp:
            self.assertTrue(app.send_email('recipient@example.com', 'Test', 'Test message'))
            client = smtp.return_value.__enter__.return_value
            client.starttls.assert_called_once()
            client.login.assert_called_once_with('sender@gmail.com', 'test-only')
            client.send_message.assert_called_once()


if __name__ == '__main__':
    unittest.main()
