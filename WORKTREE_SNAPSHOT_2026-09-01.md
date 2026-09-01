# Worktree Snapshot — September 1, 2026

Repository: asabaal-utils
Branch: feature/image_transcription

Purpose: repository-hygiene preservation checkpoint.

Preserves the current audio-transcription package reorganization, packaging changes, and lyric-sync tooling while removing generated Python packaging metadata from version control.

This commit records meaningful work present in the local working tree during
the September 1, 2026 repository cleanup.

It does not assert that every preserved component is complete, tested,
validated, production-ready, or architecturally final. Experimental and
unfinished material is intentionally preserved rather than discarded.

Pre-cleanup Git status:

D audio_transcription/README.md
 D audio_transcription/__init__.py
 D audio_transcription/__main__.py
 D audio_transcription/cli.py
 D audio_transcription/config.py
 D audio_transcription/lyrics_alignment_spec.txt
 D audio_transcription/main.py
 D audio_transcription/models.py
 D audio_transcription/transcribe.py
 D audio_transcription/transcriber.py
 M pyproject.toml
 M src/asabaal_utils.egg-info/PKG-INFO
 M src/asabaal_utils.egg-info/SOURCES.txt
 M src/asabaal_utils.egg-info/entry_points.txt
 M src/asabaal_utils.egg-info/requires.txt
 M src/asabaal_utils.egg-info/top_level.txt
?? src/asabaal_utils/audio_transcription/
?? src/asabaal_utils/video_processing/sync_lyrics_cli.py
