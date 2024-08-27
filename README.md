# Video Mashup Creator

## Description
Video Mashup Creator is a Python application that allows users to create video mashups from YouTube videos or local video files. It provides a simple graphical user interface for selecting videos, setting clip parameters, and applying effects.

## Features
- Download YouTube videos or use local video files
- Create mashups with randomly selected clips
- Apply VHS effect and frame interpolation
- Customizable clip duration and transition effects
- Easy-to-use graphical interface

## Requirements
- Python 3.6+
- FFmpeg (must be installed and accessible in the system PATH)
- Required Python packages (install via `pip install -r requirements.txt`):
  - tkinter
  - pytube
  - tqdm

## Installation
1. Clone this repository:
   ```
   git clone https://github.com/your-username/video-mashup-creator.git
   ```
2. Navigate to the project directory:
   ```
   cd video-mashup-creator
   ```
3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
4. Ensure FFmpeg is installed and accessible in your system PATH.

## Usage
1. Run the script:
   ```
   python video_mashup_creator.py
   ```
2. Enter a YouTube URL or select a local video file.
3. Set the desired parameters for your mashup (number of clips, clip length, etc.).
4. Click "Create Mashup" to generate your video.

## License
 MIT License

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements
- This project uses FFmpeg for video processing.
- YouTube video downloading is powered by pytube.