"""Single-use recovery tokens, using the existing account_tokens table."""
import datetime
import hashlib
import secrets


def token_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def issue_token(connect, email, now, expires, audit):
    c = connect()
    try:
        user = c.execute('SELECT id FROM users WHERE lower(email)=? AND COALESCE(disabled,0)=0 FOR UPDATE', (email,)).fetchone()
        if not user:
            return None
        recent = c.execute("SELECT created_at FROM account_tokens WHERE user_id=? AND kind='reset' ORDER BY created_at DESC LIMIT 1", (user['id'],)).fetchone()
        if recent and (datetime.datetime.fromisoformat(now) - datetime.datetime.fromisoformat(recent['created_at'])).total_seconds() < 60:
            return None
        token = secrets.token_urlsafe(40)
        c.execute("DELETE FROM account_tokens WHERE user_id=? AND kind='reset'", (user['id'],))
        c.execute('INSERT INTO account_tokens(token,user_id,kind,created_at,expires_at) VALUES(?,?,?,?,?)',
                  (token_hash(token), user['id'], 'reset', now, expires))
        audit(c, user['id'], 'password_reset_requested')
        c.commit()
        return token
    finally:
        c.close()


def redeem_token(connect, token, password_hash, now, audit):
    c = connect()
    try:
        digest = token_hash(token)
        candidate = c.execute("SELECT user_id FROM account_tokens WHERE token=? AND kind='reset'", (digest,)).fetchone()
        if not candidate:
            return 'invalid_token'
        # Use the same lock order as issuance to serialize simultaneous requests.
        user = c.execute('SELECT id,email,username FROM users WHERE id=? AND COALESCE(disabled,0)=0 FOR UPDATE', (candidate['user_id'],)).fetchone()
        if not user:
            return 'invalid_token'
        row = c.execute("SELECT expires_at FROM account_tokens WHERE token=? AND kind='reset' AND used_at IS NULL FOR UPDATE", (digest,)).fetchone()
        if not row:
            return 'invalid_token'
        try:
            expired = datetime.datetime.fromisoformat(row['expires_at']) <= datetime.datetime.fromisoformat(now)
        except (ValueError, TypeError):
            expired = True
        if expired:
            return 'expired_token'
        c.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash, user['id']))
        c.execute("UPDATE account_tokens SET used_at=? WHERE user_id=? AND kind='reset' AND used_at IS NULL", (now, user['id']))
        c.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
        c.execute('DELETE FROM login_attempts WHERE lower(email) IN (?,?)', (user['email'].lower(), (user['username'] or '').lower()))
        audit(c, user['id'], 'password_reset_completed', 'user', user['id'], {'auth_store': 'postgres'})
        c.commit()
        return None
    finally:
        c.close()
