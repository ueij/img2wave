# main.py

import os
import argparse
from image_processor import get_image_boundaries
from audio_generator import generate_wave

def main():
    parser = argparse.ArgumentParser(description="img2wave")
    
    parser.add_argument("--audio", type=str, required=True, help="Path to base audio file")
    parser.add_argument("--output", type=str, default="output.wav", help="Path to output WAV file")
    parser.add_argument("--normalize", action="store_true", help="Normalize the output audio peaks to 0 dBFS")
    parser.add_argument("--export-full", action=argparse.BooleanOptionalAction, default=True, help="Export full song or segment only")
    
    parser.add_argument("--image", type=str, required=True, help="Path to image file")
    parser.add_argument("--start", type=float, default=2.0, help="Segment start time in seconds")
    parser.add_argument("--end", type=float, default=5.0, help="Segment end time in seconds")
    parser.add_argument("--threshold", type=int, default=128, help="Threshold value (0-255)")
    parser.add_argument(
        "--grayscale", 
        type=str, 
        choices=["luminance_601", "luminance_709", "average", "lightness"], 
        default="luminance_601", 
        help="Grayscale conversion algorithm"
    )
    parser.add_argument("--invert", action="store_true", help="Invert colors")
    
    parser.add_argument("--width", type=int, default=2048, help="Processing width for the image analysis")
    parser.add_argument("--height", type=int, default=512, help="Processing height for the image analysis")
    parser.add_argument("--smooth", action=argparse.BooleanOptionalAction, default=True, help="Use linear interpolation or step/blocky interpolation")
    parser.add_argument("--debug", action="store_true", help="Export debug binarized and filled images")
        
    args = parser.parse_args()

    if not os.path.exists(args.audio):
        print(f"Error: Base audio file '{args.audio}' does not exist.")
        return
    if not os.path.exists(args.image):
        print(f"Error: Image '{args.image}' does not exist.")
        return

    debug_path = "debug.png" if args.debug else None

    print(f"Processing image...")
    top_env, bottom_env = get_image_boundaries(
        args.image, 
        width=args.width,
        height=args.height,
        threshold=args.threshold,
        grayscale_method=args.grayscale,
        invert=args.invert,
        debug_path=debug_path
    )

    generate_wave(
        base_audio_path=args.audio,
        top_env=top_env, 
        bottom_env=bottom_env, 
        start_sec=args.start, 
        end_sec=args.end,
        export_full=args.export_full,
        output_path=args.output,
        smooth=args.smooth,
        normalize=args.normalize
    )

if __name__ == "__main__":
    main()