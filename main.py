# main.py

import os
import argparse
from image_processor import get_image_boundaries
from audio_generator import generate_wave_on_base_stereo

def str2bool(v) -> bool:
    """Helper to convert string arguments to boolean in CLI."""
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    parser = argparse.ArgumentParser(description="Image to Waveform Modulator Engine")
    
    parser.add_argument("--audio", type=str, required=True, help="Path to base audio file (WAV, MP3, FLAC, OGG)")
    parser.add_argument("--output", type=str, default="output.wav", help="Path to output modulated WAV file")
    parser.add_argument("--export_full", type=str2bool, default=True, help="Export full song or segment only")
    parser.add_argument("--link", type=str2bool, default=True, help="Link Left and Right stereo channels")
    
    parser.add_argument("--image_L", type=str, required=True, help="Path to Left/Single image")
    parser.add_argument("--start_L", type=float, default=2.0, help="Left segment start time in seconds")
    parser.add_argument("--end_L", type=float, default=5.0, help="Left segment end time in seconds")
    
    parser.add_argument("--image_R", type=str, default=None, help="Path to Right image")
    parser.add_argument("--start_R", type=float, default=2.0, help="Right segment start time in seconds")
    parser.add_argument("--end_R", type=float, default=5.0, help="Right segment end time in seconds")
    
    args = parser.parse_args()

    if not os.path.exists(args.audio):
        print(f"Error: Base audio file '{args.audio}' does not exist.")
        return
    if not os.path.exists(args.image_L):
        print(f"Error: Left image '{args.image_L}' does not exist.")
        return
    if not args.link and args.image_R and not os.path.exists(args.image_R):
        print(f"Error: Right image '{args.image_R}' does not exist.")
        return

    print("Processing Left image...")
    top_env_L, bottom_env_L = get_image_boundaries(args.image_L, vertical_resolution=512)

    if args.link:
        print("Mode: Linked Stereo. Processing Left image for both channels...")
        top_env_R, bottom_env_R = top_env_L, bottom_env_L
        start_R, end_R = args.start_L, args.end_L
    else:
        print("Mode: Independent Stereo. Processing Left and Right images...")
        if args.image_R is None or args.image_R == args.image_L:
            print("Right image is identical or omitted. Reusing Left image data.")
            top_env_R, bottom_env_R = top_env_L, bottom_env_L
        else:
            print("Processing Right image...")
            top_env_R, bottom_env_R = get_image_boundaries(args.image_R, vertical_resolution=512)
            
        start_R, end_R = args.start_R, args.end_R

    generate_wave_on_base_stereo(
        base_audio_path=args.audio,
        top_env_L=top_env_L, bottom_env_L=bottom_env_L, start_L=args.start_L, end_L=args.end_L,
        top_env_R=top_env_R, bottom_env_R=bottom_env_R, start_R=start_R, end_R=end_R,
        export_full_song=args.export_full,
        link_stereo=args.link,
        output_path=args.output
    )

if __name__ == "__main__":
    main()