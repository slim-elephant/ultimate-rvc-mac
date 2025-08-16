from typing import TypedDict

import logging

from ultimate_rvc.typing_extra import StrPath

class MDXParams(TypedDict):
    hop_length: int
    segment_size: int
    overlap: float
    batch_size: int
    enable_denoise: bool

class VRParams(TypedDict):
    batch_size: int
    window_size: int
    aggression: int
    enable_tta: bool
    enable_post_process: bool
    post_process_threshold: float
    high_end_process: bool

class DemucsParams(TypedDict):
    segment_size: str
    shifts: int
    overlap: float
    segments_enabled: bool

class MDXCParams(TypedDict):
    segment_size: int
    override_model_segment_size: bool
    batch_size: int
    overlap: int
    pitch_shift: int

class ArchSpecificParams(TypedDict):
    MDX: MDXParams
    VR: VRParams
    Demucs: DemucsParams
    MDXC: MDXCParams

class CommonSeparator:
    primary_stem_name: str
    secondary_stem_name: str

class MDXSeparator(CommonSeparator): ...
class MDXCSeparator(CommonSeparator): ...
class VRSeparator(CommonSeparator): ...
class DemucsSeparator(CommonSeparator): ...

class Separator:
    arch_specific_params: ArchSpecificParams
    model_instance: MDXSeparator | MDXCSeparator | VRSeparator | DemucsSeparator
    def __init__(
        self,
        log_level: int = ...,
        log_formatter: logging.Formatter | None = None,
        model_file_dir: StrPath = "/tmp/audio-separator-models/",  # noqa: S108
        output_dir: StrPath | None = None,
        output_format: str = "WAV",
        output_bitrate: str | None = None,
        normalization_threshold: float = 0.9,
        amplification_threshold: float = 0.0,
        output_single_stem: str | None = None,
        invert_using_spec: bool = False,
        sample_rate: int = 44100,
        use_soundfile: bool = False,
        use_autocast: bool = False,
        mdx_params: MDXParams = {
            "hop_length": 1024,
            "segment_size": 256,
            "overlap": 0.25,
            "batch_size": 1,
            "enable_denoise": False,
        },
        vr_params: VRParams = {
            "batch_size": 1,
            "window_size": 512,
            "aggression": 5,
            "enable_tta": False,
            "enable_post_process": False,
            "post_process_threshold": 0.2,
            "high_end_process": False,
        },
        demucs_params: DemucsParams = {
            "segment_size": "Default",
            "shifts": 2,
            "overlap": 0.25,
            "segments_enabled": True,
        },
        mdxc_params: MDXCParams = {
            "segment_size": 256,
            "override_model_segment_size": False,
            "batch_size": 1,
            "overlap": 8,
            "pitch_shift": 0,
        },
        info_only: bool = False,
    ) -> None: ...
    def download_model_files(
        self,
        model_filename: str,
    ) -> tuple[str, str, str, str, str | None]: ...
    def load_model(
        self,
        model_filename: str = "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt",
    ) -> None: ...
    def separate(
        self,
        audio_file_path: str,
        custom_output_names: dict[str, str] | None = None,
    ) -> list[str]: ...
