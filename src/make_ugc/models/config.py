from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class VeoModel(StrEnum):
    VEO_3_1 = "veo-3.1-generate-preview"
    VEO_3_1_FAST = "veo-3.1-fast-generate-preview"
    VEO_3_1_LITE = "veo-3.1-lite-generate-preview"
    VEO_3 = "veo-3.0-generate-001"
    VEO_2 = "veo-2.0-generate-001"


class AspectRatio(StrEnum):
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"


class Resolution(StrEnum):
    HD = "720p"
    FULL_HD = "1080p"
    UHD = "4k"


class PersonGeneration(StrEnum):
    ALLOW_ALL = "allow_all"
    ALLOW_ADULT = "allow_adult"
    DONT_ALLOW = "dont_allow"


@dataclass
class VideoConfig:
    prompt: str
    model: VeoModel = VeoModel.VEO_3_1
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    resolution: Resolution = Resolution.HD
    duration: int = 8
    output_dir: Path = field(default_factory=lambda: Path("output"))
    negative_prompt: str | None = None
    poll_interval: int = 10

    def __post_init__(self) -> None:
        if self.duration not in (4, 6, 8):
            raise ValueError(f"Duration must be 4, 6, or 8 seconds, got {self.duration}")

        if self.resolution in (Resolution.FULL_HD, Resolution.UHD) and self.duration != 8:
            raise ValueError(f"{self.resolution} requires duration=8")

        if self.resolution == Resolution.UHD and self.model not in (
            VeoModel.VEO_3_1,
            VeoModel.VEO_3_1_FAST,
        ):
            raise ValueError(f"4K is only supported by Veo 3.1 and Veo 3.1 Fast")

        self.output_dir.mkdir(parents=True, exist_ok=True)
