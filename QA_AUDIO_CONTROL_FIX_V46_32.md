# PET Quest V46.32 - Audio Controls Safe Fix

## Objective
Correct audible distortion/transients when changing Listening volume or playback speed, while preserving exam-mode behavior and the PostgreSQL master-content architecture.

## Changes
- Added `v46_32_audio_safe_engine.js` as the single audio-control layer.
- Volume is capped at 0.85; default media volume is 0.72.
- Volume changes use a short smooth ramp instead of abrupt jumps.
- Speed changes during playback fade out, switch rate, resume, and fade in.
- At rates other than 1.00x, browser pitch-preservation is disabled to avoid metallic/warbling time-stretch artifacts on synthetic speech.
- At 1.00x, normal pitch preservation remains enabled.
- Fidelity Listening now exposes safe speed presets 0.75x / 0.85x / 1.00x / 1.10x in learning mode.
- Strict exam mode forces 1.00x.
- Full Mock Listening remains fixed at 1.00x and uses the shared safe-volume behavior.
- PET Audio Bank uses the shared safe speed/volume engine.
- SpeechSynthesis output is limited to a controlled volume and safe rate range.
- Service Worker cache bumped to `petquest-v46-32-audiofix-1` to prevent stale audio-control JavaScript.

## Validation results
- Audio control engine unit QA: 10/10 PASS.
- Chromium HTMLMediaElement functional QA: 6/6 PASS.
  - packaged MP3 loaded without media error;
  - volume changed from 0.72 to 0.35 while playing;
  - 0.75x, 0.85x, 1.00x, 1.10x applied while playback continued;
  - pitch-preservation disabled at non-1x and restored at 1x.
- Audio control static/inventory QA: 30/30 PASS.
- PET Audio Bank: 28/28 PASS.
- Full Mock current regression: 46/46 PASS.
- PostgreSQL master-content QA: 40/40 PASS.
- Windows/login current regression: 27/27 PASS.
- Registration/recovery: PASS.
- JavaScript syntax: 64/64 PASS.
- Service Worker runtime assets: 167/167 present.
- Audio inventory: 877 files.
  - 875 MP3 headers parse successfully.
  - 2 WAV headers parse successfully.
  - all active MP3 masters (excluding 15 unused files under `reference_original`) are 48 kHz, mono, bitrate >= 120 kbps.

## Historical QA note
`qa_v46_11_mock_audio.py` is a historical V46.11 gate. It expects exactly 3 mocks, a 44.1 kHz mastering standard, and old cache/script version strings. The current release has 20 school mocks and 48 kHz active audio, so that historical validator is not an applicable release gate for V46.32.

## Production note
The current Listening files remain synthetic reference audio unless explicitly marked human-studio approved. This fix addresses playback/control quality; it does not change the truthfulness of studio-audio readiness flags.
