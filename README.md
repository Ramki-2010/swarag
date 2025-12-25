# Swarag – Carnatic Raga Identification (Research Project)

Swarag is an early-stage research and learning project focused on identifying Carnatic ragas from audio recordings using signal processing and machine learning techniques.

The project explores how melodic patterns, pitch contours, and characteristic phrases (raga lakshanas) can be extracted from audio and used for raga identification.

## Project Status

This project is currently in the dataset collection and preprocessing phase.

The immediate goals are:
- Collect publicly available Carnatic music audio samples
- Organize them by raga with proper metadata
- Convert audio into spectrograms and pitch-based features
- Experiment with classical ML and deep learning approaches for raga classification

## Data Sources

Audio samples are collected from publicly available sources such as:
- Freesound.org (Carnatic varnam datasets and related recordings)
- Other openly licensed Carnatic music datasets

Only audio files with appropriate licenses are used.  
This project does not access private user data.

## Intended Use of APIs

The Freesound API is used only for:
- Searching public audio datasets
- Downloading openly licensed audio files
- Accessing metadata (tags, descriptions, licenses)

No OAuth login or user authentication is required.

## Non-Commercial Notice

This is a non-commercial, educational, and research-oriented project.

## Tech Stack (planned)

- Python
- Librosa (audio processing)
- NumPy / SciPy
- PyTorch or TensorFlow (later stages)

## License

This repository is intended for research and educational use.
