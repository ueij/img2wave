# audio_generator.py

import numpy as np
import soundfile as sf

def load_base_audio(file_path: str):
    """Loads WAV, MP3, FLAC, or OGG and standardizes to float32 stereo [num_samples, 2]."""
    data, sample_rate = sf.read(file_path, dtype='float32')
    
    was_mono = len(data.shape) == 1
    if was_mono:
        print("Note: Base audio is Mono. Duplicating to Stereo for processing.")
        data = np.column_stack((data, data))
        
    return sample_rate, data, was_mono

def process_single_channel_inplace(
    channel_view: np.ndarray, 
    top_env_small: np.ndarray, 
    bottom_env_small: np.ndarray, 
    start_sec: float, 
    end_sec: float, 
    sample_rate: int
):
    """Modifies the segment of the channel view directly to avoid copying the entire track."""
    total_samples = len(channel_view)
    start_sample = max(0, min(int(start_sec * sample_rate), total_samples))
    end_sample = max(0, min(int(end_sec * sample_rate), total_samples))
    segment_length = end_sample - start_sample
    
    if segment_length <= 0:
        return start_sample, end_sample
        
    segment = channel_view[start_sample:end_sample]
    
    x_original = np.arange(len(top_env_small), dtype=np.float32)
    x_target = np.linspace(0, len(top_env_small) - 1, segment_length, dtype=np.float32)
    
    top_env = np.interp(x_target, x_original, top_env_small)
    bottom_env = np.interp(x_target, x_original, bottom_env_small)
    
    amplitude = (top_env - bottom_env) * 0.5
    midpoint = (top_env + bottom_env) * 0.5
    
    segment *= amplitude
    segment += midpoint
    
    return start_sample, end_sample

def generate_wave_on_base_stereo(
    base_audio_path: str,
    top_env_L: np.ndarray, bottom_env_L: np.ndarray, start_L: float, end_L: float,
    top_env_R: np.ndarray, bottom_env_R: np.ndarray, start_R: float, end_R: float,
    export_full_song: bool = True,
    link_stereo: bool = True,
    output_path: str = "output.wav"
):
    sample_rate, modulated_stereo, was_mono = load_base_audio(base_audio_path)
    
    start_sample_L, end_sample_L = process_single_channel_inplace(
        modulated_stereo[:, 0], top_env_L, bottom_env_L, start_L, end_L, sample_rate
    )
    
    start_sample_R, end_sample_R = process_single_channel_inplace(
        modulated_stereo[:, 1], top_env_R, bottom_env_R, start_R, end_R, sample_rate
    )
    
    if export_full_song:
        final_audio = modulated_stereo
    else:
        export_start = max(0, min(start_sample_L, start_sample_R))
        export_end = min(len(modulated_stereo), max(end_sample_L, end_sample_R))
        
        if export_end <= export_start:
            final_audio = modulated_stereo
        else:
            final_audio = modulated_stereo[export_start:export_end]
            
    if was_mono and link_stereo:
        print("Output configuration satisfies Mono rule. Collapsing output to Mono.")
        final_audio = final_audio[:, 0]
            
    max_val = np.max(np.abs(final_audio))
    if max_val > 1e-8 and not np.isclose(max_val, 1.0):
        final_audio /= max_val
        
    sf.write(output_path, final_audio, sample_rate, format='WAV', subtype='PCM_16')
    print(f"Saved output to {output_path} (Duration: {len(final_audio)/sample_rate:.2f}s)")