from dataclasses import dataclass

from .pov_reaction import POV_REACTION, POV_REACTION_NEGATIVE


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    prompt: str
    negative_prompt: str | None = None


PRESETS: dict[str, Preset] = {
    "pov-reaction": Preset(
        name="pov-reaction",
        description="Gen Z girl reacting to something on her phone — silent, casual, front-camera POV",
        prompt=POV_REACTION,
        negative_prompt=POV_REACTION_NEGATIVE,
    ),
}


def get_preset(name: str) -> Preset:
    if name not in PRESETS:
        available = ", ".join(PRESETS)
        raise ValueError(f"Unknown preset '{name}'. Available: {available}")
    return PRESETS[name]


def list_presets() -> list[Preset]:
    return list(PRESETS.values())
