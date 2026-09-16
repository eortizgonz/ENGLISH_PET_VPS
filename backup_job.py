#!/usr/bin/env python3
"""One-shot PET Quest backup job for cron/platform schedulers."""
import api_server as core
import api_server_v8 as v8
v8.init_v8_db()
p=core.create_backup()
deleted=v8.cleanup_retention()
print(f'backup={p} learning_events_retention_deleted={deleted}')
