# Image to Sound (v0.2.2)

A desktop utility that modulates the amplitude of an existing audio file using the top and bottom boundaries of an image.

> **Note:** The GUI is currently really simple (v0.2.2) right now because I'm learning (づ_ど); while the underlying Python engine supports advanced settings (like stereo splitting and custom thresholds), the GUI uses defaults for simple single-image audio modulation.

![Image to Sound GUI](images/gui.png)

## Features Available in the GUI
* **Base Audio Selection:** Works with `.mp3`, `.wav`, and `.ogg` files.
* **Image Source Selection:** Supports `.png`, `.jpg`, `.jpeg`, and `.webp` images.
* **Segment Timing:** Choose exactly when (in seconds) the image modulation starts and ends within your base audio.
* **Stereo Processing:** Generates a 24-bit stereo `.wav` file (`output.wav`) with the modulation applied to your selected segment.

## How to Use the Windows App (.exe)

1. Go to the **Releases** tab on the right side of this GitHub repository.
2. Download `image-to-sound-v0.2.2-windows-x64.exe`.
3. Run the executable.
4. **Select Base Audio:** Click "Browse..." and select your base audio track.
5. **Select Image Source:** Click "Browse..." and select the image you want to extract contours from.
6. **Set Segment Timing:** Input the start time and end time (in seconds) where you want the visual shape to affect the audio.
7. **Generate:** Click **Generate Audio**. The processed file will be saved as `output.wav` in the directory where the application is running.

> [!IMPORTANT]
> The program only tracks **black pixels** to define the shape, discarding white pixels as empty space. If your source image features a white shape/text on a black background, make sure to invert the colors before uploading it to the GUI.

> [!WARNING]
> The processed file is automatically saved as `output.wav` in the same directory where the application is running. **If a file named `output.wav` already exists in that folder, it will be overwritten without warning.** Be sure to rename or move your previous outputs if you want to keep them.

*The GUI currently applies a binarization threshold of 128, a standard luminance grayscale filter (ITU-R BT.601 Luma), and mirrors the images per stereo channel.*

## Preview and Examples

Below is an example of how the text silhouette 'domino' is modulated on an audio track.

### Image Previews

<table>
  <tr>
    <th width="33.33%">Source Image</th>
    <th width="33.33%">Base Audio</th>
    <th width="33.33%">Output</th>
  </tr>
  <tr>
    <td>
       <img src="images/domino.png" alt="domino Image Source" width="100%">
       <p align="center">'domino' text</p>
    </td>
    <td>
       <img src="images/audacity_domino.png" alt="Base Audio Waveform" width="100%">
       <p align="center">The original track's waveforms</p>
    </td>
    <td>
       <img src="images/audacity_output.png" alt="Output Waveform" width="100%">
       <p align="center">The word 'domino' visible on waveforms</p>
    </td>
  </tr>
</table>

### Audio Comparison

You can download and listen to how the shape of the text squeezes and shapes the volume of the track:

* **Original Base Audio:** 
  [Listen to domino.wav](audios/audio_domino.wav)
* **Modulated Output:** 
  [Listen to output.wav](audios/audio_output.wav)

## Running from Source (Advanced Users)

If you want to use the full feature set (such as independent stereo channels, custom image resolutions, color inversion, or threshold adjustments), you can run the command-line interface (`main.py`) directly using Python.

### Prerequisites
Make sure you have Python 3.10+ installed. Install the dependencies:
```bash
pip install PySide6 pillow numpy soundfile
