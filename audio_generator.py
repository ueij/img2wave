# audio_generator.py

import numpy as np
import soundfile as sf

def load_base_audio(file_path: str, force_stereo: bool = True):
    data, sample_rate = sf.read(file_path, dtype='float32')
    
    was_mono = len(data.shape) == 1
    if was_mono and force_stereo:
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
    total_samples = len(channel_view)
    start_sample = max(0, min(int(start_sec * sample_rate), total_samples))
    end_sample = max(0, min(int(end_sec * sample_rate), total_samples))
    segment_length = end_sample - start_sample
    
    if segment_length <= 0:
        return start_sample, end_sample
        
    segment = channel_view[start_sample:end_sample]
    
    if segment_length > 1:
        x_target = np.linspace(0, len(top_env_small) - 1, segment_length, dtype=np.float32)
    else:
        x_target = np.zeros(segment_length, dtype=np.float32)
        
    x_original = np.arange(len(top_env_small), dtype=np.float32)
    
    top_env = np.interp(x_target, x_original, top_env_small)
    bottom_env = np.interp(x_target, x_original, bottom_env_small)
    
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

def generate_wave_on_base_stereo(
    base_audio_path: str,
    top_env_L: np.ndarray, bottom_env_L: np.ndarray, start_L: float, end_L: float,
    top_env_R: np.ndarray, bottom_env_R: np.ndarray, start_R: float, end_R: float,
    export_full_song: bool = True,
    link_stereo: bool = True,
    output_path: str = "output.wav"
):
    force_stereo = not link_stereo
    sample_rate, modulated_audio, was_mono = load_base_audio(file_path=base_audio_path, force_stereo=force_stereo)
    
    is_mono_processing = (was_mono and link_stereo)
    
    if is_mono_processing:
        start_sample_L, end_sample_L = process_single_channel_inplace(
            modulated_audio, top_env_L, bottom_env_L, start_L, end_L, sample_rate
        )
        start_sample_R, end_sample_R = start_sample_L, end_sample_L
    else:
        start_sample_L, end_sample_L = process_single_channel_inplace(
            modulated_audio[:, 0], top_env_L, bottom_env_L, start_L, end_L, sample_rate
        )
        start_sample_R, end_sample_R = process_single_channel_inplace(
            modulated_audio[:, 1], top_env_R, bottom_env_R, start_R, end_R, sample_rate
        )
    
    if export_full_song:
        final_audio = modulated_audio
    else:
        export_start = max(0, min(start_sample_L, start_sample_R))
        export_end = min(len(modulated_audio), max(end_sample_L, end_sample_R))
        
        if export_end <= export_start:
            final_audio = modulated_audio
        else:
            final_audio = modulated_audio[export_start:export_end]
            
    max_val = max(np.max(final_audio), -np.min(final_audio))
    if max_val > 1:
        final_audio /= max_val
        
    sf.write(output_path, final_audio, sample_rate, format='WAV', subtype='PCM_24')
    print(f"Saved output to {output_path}")