-- PET Quest: inventory after running setup_postgres_pet.py
SELECT * FROM public.v_content_inventory ORDER BY content_table;

SELECT profile, COUNT(*) AS practice_items
FROM public.practice_bank_items GROUP BY profile ORDER BY profile;

SELECT level, COUNT(*) AS lessons
FROM public.curriculum_lessons GROUP BY level ORDER BY level;

SELECT profile, COUNT(*) AS audio_assets,
       COUNT(*) FILTER (WHERE human_recording IS TRUE) AS human_audio,
       COUNT(*) FILTER (WHERE synthetic IS TRUE) AS synthetic_audio
FROM public.audio_assets GROUP BY profile ORDER BY profile;

SELECT profile, COUNT(*) AS mocks,
       SUM(reading_count) reading_items,
       SUM(listening_count) listening_items,
       SUM(writing_count) writing_tasks,
       SUM(speaking_count) speaking_parts
FROM public.exam_packs GROUP BY profile ORDER BY profile;

SELECT skill, COUNT(*) AS exam_items
FROM public.exam_items GROUP BY skill ORDER BY skill;

SELECT status, counts_json, errors_json, started_at, finished_at
FROM public.content_seed_runs ORDER BY id DESC LIMIT 10;
