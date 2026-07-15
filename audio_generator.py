# audio_generator.py

import numpy as np
import soundfile as sf

def load_base_audio(file_path: str):
    data, sample_rate = sf.read(file_path, dtype='float32')
    return sample_rate, data

def process_channel(
    channel_view: np.ndarray, 
    top_env_small: np.ndarray, 
    bottom_env_small: np.ndarray, 
    start_sec: float, 
    end_sec: float, 
    sample_rate: int,
    smooth: bool = True
):
    total_samples = len(channel_view)
    start_sample = max(0, min(int(start_sec * sample_rate), total_samples))
    end_sample = max(0, min(int(end_sec * sample_rate), total_samples))
    segment_length = end_sample - start_sample
    
    if segment_length <= 0:
        return start_sample, end_sample
        
    segment = channel_view[start_sample:end_sample]
    
    if smooth:
        if segment_length > 1:
            x_target = np.linspace(0, len(top_env_small) - 1, segment_length, dtype=np.float32)
        else:
            x_target = np.zeros(segment_length, dtype=np.float32)
            
        x_original = np.arange(len(top_env_small), dtype=np.float32)
        top_env = np.interp(x_target, x_original, top_env_small)
        bottom_env = np.interp(x_target, x_original, bottom_env_small)
    else:
        indices = (np.arange(segment_length) * (len(top_env_small) / segment_length)).astype(np.int32)
        indices = np.clip(indices, 0, len(top_env_small) - 1)
        top_env = top_env_small[indices]
        bottom_env = bottom_env_small[indices]

    """
    bottom_env -= top_env   | B - T                 | thickness         (B - T)
    bottom_env *= -0.5      | 0.5 * (T - B)         | amplitude         (0.5 * (T - B))
    top_env -= bottom_env   | T - [0.5 * (T - B)]   | DC offset center  (0.5 * (T + B))
    segment *= bottom_env   | segment * amplitude   | squeezed          (segment * amplitude)
    segment += top_env      | squeezed + center     | final             (squeezed + center)
    """

    bottom_env -= top_env
    bottom_env *= -0.5   
    top_env -= bottom_env
    segment *= bottom_env
    segment += top_env
    
    return start_sample, end_sample

def generate_wave(
    base_audio_path: str,
    top_env: np.ndarray, 
    bottom_env: np.ndarray, 
    start_sec: float, 
    end_sec: float,
    export_full: bool = True,
    output_path: str = "output.wav",
    smooth: bool = True,
    normalize: bool = False
):
    sample_rate, modulated_audio = load_base_audio(file_path=base_audio_path)
    
    is_stereo = len(modulated_audio.shape) > 1 and modulated_audio.shape[1] > 1
    
    if is_stereo:
        start_sample, end_sample = process_channel(
            modulated_audio[:, 0], top_env, bottom_env, start_sec, end_sec, sample_rate, smooth=smooth
        )
        process_channel(
            modulated_audio[:, 1], top_env, bottom_env, start_sec, end_sec, sample_rate, smooth=smooth
        )
    else:
        start_sample, end_sample = process_channel(
            modulated_audio, top_env, bottom_env, start_sec, end_sec, sample_rate, smooth=smooth
        )
    
    if export_full:
        final_audio = modulated_audio
    else:
        if end_sample <= start_sample:
            final_audio = modulated_audio
        else:
            final_audio = modulated_audio[start_sample:end_sample]
            
    max_val = max(np.max(final_audio), -np.min(final_audio))

    if max_val > 1.0 or (normalize and max_val > 0.0):
        final_audio /= max_val
        
    sf.write(output_path, final_audio, sample_rate, format='WAV', subtype='PCM_24')
    print(f"Saved output to {output_path}")