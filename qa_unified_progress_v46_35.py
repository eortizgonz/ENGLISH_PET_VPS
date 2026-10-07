"""Regression tests for unified snapshot + learning-event progress."""
import json
import unittest
from unittest.mock import patch

import api_server as app


class UnifiedProgressTests(unittest.TestCase):
    def setUp(self):
        self.db = app.PgCompatConnection()
        self.real_close = self.db.close
        self.db.close = lambda: None
        for sql in [
            'CREATE TEMP TABLE users(id bigint PRIMARY KEY,name text,email text,role text,school_id bigint)',
            'CREATE TEMP TABLE snapshots(user_id bigint PRIMARY KEY,payload text,updated_at text)',
            'CREATE TEMP TABLE academic_error_events(id bigint,student_id bigint,error_code text,skill text,subcompetence text,occurred_at text)',
            'CREATE TEMP TABLE academic_remediation_attempts(id bigint,student_id bigint,error_code text,correct integer,attempted_at text)',
            'CREATE TEMP TABLE mock_attempts(id bigint,student_id bigint,pack_id text,skill text,total_items integer,correct_items integer,pct real,started_at text,finished_at text,source text)',
            'CREATE TEMP TABLE speaking_attempts(id bigint,student_id bigint,score_pct real,part integer,metrics_json text,created_at text)',
            'CREATE TEMP TABLE learning_events(id bigint PRIMARY KEY,user_id bigint,event_type text,skill text,item_id text,success integer,minutes real,meta_json text,created_at text)',
        ]:
            self.db.execute(sql)
        self.db.execute('SET search_path TO pg_temp')
        self.db.raw.execute("INSERT INTO users VALUES(1,'Learner','learner@example.com','student',10)")
        self.db.commit()

    def tearDown(self):
        self.real_close()

    def summary(self):
        with patch.object(app, 'conn', lambda: self.db):
            return app.student_preparation_summary(1, 10)

    def test_merges_modern_events_without_counting_snapshot_mirrors_twice(self):
        payload = {
            'profile': {'xp': 7, 'examProfile': 'schools'},
            'history': [{'qid': 'legacy-1', 'skill': 'reading', 'correct': True, 'date': '2026-10-01T10:00:00+00:00'}],
            'writing': [], 'speaking': [], 'mockAttempts': [],
        }
        self.db.execute('INSERT INTO snapshots VALUES(?,?,?)', (1, json.dumps(payload), '2026-10-01T10:00:00+00:00'))
        rows = [
            (1, 1, 'practice_answer', 'reading', 'legacy-1', 1, 0.5, '{}', '2026-10-01T10:01:00+00:00'),
            (2, 1, 'practice_bank_answer', 'reading', 'modern-1', 0, 0.5, '{}', '2026-10-01T10:02:00+00:00'),
            (3, 1, 'practice_remediation_answer', 'reading', 'modern-1', 1, 0.5, '{}', '2026-10-01T10:03:00+00:00'),
            (4, 1, 'audio_bank_answer', 'listening', 'audio-1', 1, 0.5, '{}', '2026-10-01T10:04:00+00:00'),
            (5, 1, 'mastery_goal_changed', 'readiness', 'goal', 1, 0, '{}', '2026-10-01T10:05:00+00:00'),
        ]
        with self.db.raw.cursor() as cursor:
            cursor.executemany('INSERT INTO learning_events VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)', rows)
        self.db.commit()

        out = self.summary()
        self.assertEqual(out['activity']['attempts'], 4)
        self.assertEqual(out['activity']['snapshot_attempts'], 1)
        self.assertEqual(out['activity']['event_attempts'], 3)
        self.assertEqual(out['activity']['correct_answers'], 3)
        self.assertEqual(out['activity']['accuracy'], 75.0)
        self.assertEqual(out['activity']['xp'], 30)
        self.assertEqual(out['skills']['reading'], 66.7)
        self.assertEqual(out['skills']['listening'], 100.0)
        self.assertEqual(out['preparation']['score'], 41.7)
        self.assertEqual(out['errors']['total_error_targets'], 1)
        self.assertEqual(out['errors']['corrected'], 1)
        self.assertEqual(out['errors']['pending'], 0)
        self.assertEqual(out['updated_at'], '2026-10-01T10:04:00+00:00')

    def test_empty_evidence_stays_zero(self):
        out = self.summary()
        self.assertEqual(out['activity']['attempts'], 0)
        self.assertEqual(out['activity']['xp'], 0)
        self.assertEqual(out['preparation']['score'], 0.0)
        self.assertEqual(out['skills'], {'reading': 0.0, 'writing': 0.0, 'listening': 0.0, 'speaking': 0.0})

    def test_snapshot_recalculates_all_four_skill_percentages(self):
        payload = {
            'profile': {'xp': 40},
            'history': [
                {'qid': 'r1', 'skill': 'reading', 'correct': True},
                {'qid': 'r2', 'skill': 'reading', 'correct': False},
                {'qid': 'l1', 'skill': 'listening', 'correct': True},
                {'qid': 'l2', 'skill': 'listening', 'correct': True},
            ],
            'writing': [{'score': 16}],
            'speaking': [{'score': 14, 'score_pct': 70}],
            'mockAttempts': [],
        }
        self.db.execute('INSERT INTO snapshots VALUES(?,?,?)', (1, json.dumps(payload), '2026-10-01T10:00:00+00:00'))
        self.db.commit()
        out = self.summary()
        self.assertEqual(out['skills'], {'reading': 50.0, 'writing': 80.0, 'listening': 100.0, 'speaking': 70.0})
        self.assertEqual(out['preparation']['score'], 75.0)

    def test_speaking_uses_highest_pronunciation_proxy(self):
        rows = [
            (1, 1, 91.0, 1, json.dumps({'pronunciation_proxy': 72}), '2026-10-01T10:00:00+00:00'),
            (2, 1, 68.0, 1, json.dumps({'pronunciation_proxy': 88}), '2026-10-01T10:01:00+00:00'),
            (3, 1, 95.0, 2, json.dumps({'pronunciation_proxy': 79}), '2026-10-01T10:02:00+00:00'),
        ]
        with self.db.raw.cursor() as cursor:
            cursor.executemany('INSERT INTO speaking_attempts VALUES(%s,%s,%s,%s,%s,%s)', rows)
        self.db.commit()
        self.assertEqual(self.summary()['skills']['speaking'], 88.0)

    def test_speaking_legacy_rows_keep_overall_score_fallback(self):
        with self.db.raw.cursor() as cursor:
            cursor.execute('INSERT INTO speaking_attempts VALUES(%s,%s,%s,%s,%s,%s)', (1, 1, 80.0, 1, '{}', '2026-10-01T10:00:00+00:00'))
        self.db.commit()
        self.assertEqual(self.summary()['skills']['speaking'], 80.0)


if __name__ == '__main__':
    unittest.main()
