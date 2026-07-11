# main.py

import os
import argparse
from image_processor import get_image_boundaries
from audio_generator import generate_wave_on_base_stereo

def main():
    parser = argparse.ArgumentParser(description="Image to Sound")
    
    parser.add_argument("--audio", type=str, required=True, help="Path to base audio file")
    parser.add_argument("--output", type=str, default="output.wav", help="Path to output WAV file")
    parser.add_argument("--export-full", action=argparse.BooleanOptionalAction, default=True, help="Export full song or segment only")
    
    parser.add_argument("--link-stereo", action=argparse.BooleanOptionalAction, default=True, help="Link Left and Right stereo channels")
    parser.add_argument("--link-threshold", action=argparse.BooleanOptionalAction, default=True, help="Link Left and Right threshold values")
    parser.add_argument("--link-grayscale", action=argparse.BooleanOptionalAction, default=True, help="Link Left and Right grayscale methods")
    parser.add_argument("--link-invert", action=argparse.BooleanOptionalAction, default=True, help="Link Left and Right color inversion settings")
    
    parser.add_argument("--image", "--image-L", dest="image_L", type=str, required=True, help="Path to Left/Single image")
    parser.add_argument("--start", "--start-L", dest="start_L", type=float, default=2.0, help="Left segment start time in seconds")
    parser.add_argument("--end", "--end-L", dest="end_L", type=float, default=5.0, help="Left segment end time in seconds")
    parser.add_argument("--threshold", "--threshold-L", dest="threshold_L", type=int, default=128, help="Threshold value (0-255) for Left channel")
    parser.add_argument(
        "--grayscale", "--grayscale-L",
        dest="grayscale_L", 
        type=str, 
        choices=["luminance_601", "luminance_709", "average", "lightness"], 
        default="luminance_601", 
        help="Grayscale conversion algorithm for Left channel"
    )
    parser.add_argument("--invert", "--invert-L", dest="invert_L", action="store_true", help="Invert colors for Left channel")
    
    parser.add_argument("--image-R", type=str, default=None, help="Path to Right image")
    parser.add_argument("--start-R", type=float, default=None, help="Right segment start time in seconds")
    parser.add_argument("--end-R", type=float, default=None, help="Right segment end time in seconds")
    parser.add_argument("--threshold-R", type=int, default=None, help="Threshold value (0-255) for Right channel")
    parser.add_argument(
        "--grayscale-R", 
        type=str, 
        choices=["luminance_601", "luminance_709", "average", "lightness"], 
        default=None, 
        help="Grayscale conversion algorithm for Right channel"
    )
    parser.add_argument("--invert-R", action=argparse.BooleanOptionalAction, default=None, help="Invert colors for Right channel")
    
    parser.add_argument("--width", type=int, default=2048, help="Processing width for the image analysis")
    parser.add_argument("--height", type=int, default=512, help="Processing height for the image analysis")
    parser.add_argument("--debug", action="store_true", help="Export debug binarized and filled images")
    
    args = parser.parse_args()

    if not os.path.exists(args.audio):
        print(f"Error: Base audio file '{args.audio}' does not exist.")
        return
    if not os.path.exists(args.image_L):
        print(f"Error: Left image '{args.image_L}' does not exist.")
        return
    if not args.link_stereo and args.image_R is not None:
        if not os.path.exists(args.image_R):
            print(f"Error: Right image '{args.image_R}' does not exist.")
            return

    debug_path_L = "debug_L.png" if args.debug else None
    debug_path_R = "debug_R.png" if args.debug else None

    print(f"Processing Left image (Dimensions: {args.width}x{args.height}, Grayscale: {args.grayscale_L}, Threshold: {args.threshold_L}, Invert: {args.invert_L})...")
    top_env_L, bottom_env_L = get_image_boundaries(
        args.image_L, 
        width=args.width,
        height=args.height,
        threshold=args.threshold_L,
        grayscale_method=args.grayscale_L,
        invert=args.invert_L,
        debug_path=debug_path_L
    )

    if args.link_stereo:
        print("Mode: Linked Stereo. Duplicating Left channel processing and timing...")
        top_env_R, bottom_env_R = top_env_L, bottom_env_L
        start_R, end_R = args.start_L, args.end_L
    else:
        print("Mode: Independent Stereo. Resolving Right channel parameters...")
        
        start_R = args.start_R if args.start_R is not None else args.start_L
        end_R = args.end_R if args.end_R is not None else args.end_L
        
        if args.link_threshold:
            threshold_R = args.threshold_L
        else:
            if args.threshold_R is not None:
                threshold_R = args.threshold_R
            else:
                print(f"Note: --no-link-threshold active but --threshold-R was not specified. Falling back to Left threshold ({args.threshold_L}).")
                threshold_R = args.threshold_L

        if args.link_grayscale:
            grayscale_R = args.grayscale_L
        else:
            if args.grayscale_R is not None:
                grayscale_R = args.grayscale_R
            else:
                print(f"Note: --no-link-grayscale active but --grayscale-R was not specified. Falling back to Left grayscale method ({args.grayscale_L}).")
                grayscale_R = args.grayscale_L

        if args.link_invert:
            invert_R = args.invert_L
        else:
            if args.invert_R is not None:
                invert_R = args.invert_R
            else:
                print(f"Note: --no-link-invert active but --invert-R was not specified. Falling back to Left invert setting ({args.invert_L}).")
                invert_R = args.invert_L

        effective_image_R = args.image_R if args.image_R is not None else args.image_L
        
        same_processing = (
            threshold_R == args.threshold_L and
            grayscale_R == args.grayscale_L and
            invert_R == args.invert_L
        )
        
        if effective_image_R == args.image_L and same_processing:
            print("Right image and configuration parameters are identical. Reusing Left channel boundary data.")
            top_env_R, bottom_env_R = top_env_L, bottom_env_L
        else:
            print(f"Processing Right image (Dimensions: {args.width}x{args.height}, Grayscale: {grayscale_R}, Threshold: {threshold_R}, Invert: {invert_R})...")
            top_env_R, bottom_env_R = get_image_boundaries(
                effective_image_R, 
                width=args.width,
                height=args.height,
                threshold=threshold_R,
                grayscale_method=grayscale_R,
                invert=invert_R,
                debug_path=debug_path_R
            )

    generate_wave_on_base_stereo(
        base_audio_path=args.audio,
        top_env_L=top_env_L, bottom_env_L=bottom_env_L, start_L=args.start_L, end_L=args.end_L,
        top_env_R=top_env_R, bottom_env_R=bottom_env_R, start_R=start_R, end_R=end_R,
        export_full_song=args.export_full,
        link_stereo=args.link_stereo,
        output_path=args.output
    )

if __name__ == "__main__":
    main()