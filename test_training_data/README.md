
# Church Service Audio Training Data

This directory contains training samples for the church service audio classifier.

## Directory Structure:
- `music/`: Instrumental music samples
- `speech/`: Spoken content (sermons, announcements)
- `singing/`: Vocal music (hymns, choir)
- `mixed/`: Content with multiple audio types
- `silence/`: Quiet/ambient audio

## Usage:
1. Place audio files in appropriate subdirectories
2. Use the ChurchAudioClassifier.train_from_directory() method
3. Save the trained model for future use

## Supported Formats:
- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- Other formats supported by librosa

Created: test_training_data
