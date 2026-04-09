import argparse
from pathlib import Path

from .models import VideoConfig, VeoModel, AspectRatio, Resolution
from .presets import get_preset, list_presets
from .services import VideoGenerator
from .utils import load_api_key


CHARACTERS_DIR = Path(__file__).resolve().parent.parent.parent / "characters"
DEFAULT_CHARACTER = CHARACTERS_DIR / "emma.png"


def _add_shared_options(*parsers: argparse.ArgumentParser) -> None:
    for p in parsers:
        p.add_argument("--model", type=VeoModel, default=VeoModel.VEO_3_1_FAST, choices=list(VeoModel))
        p.add_argument("--aspect", type=AspectRatio, default=AspectRatio.PORTRAIT, choices=list(AspectRatio))
        p.add_argument("--resolution", type=Resolution, default=Resolution.FULL_HD, choices=list(Resolution))
        p.add_argument("--duration", type=int, default=8, choices=[4, 6, 8])
        p.add_argument("--output-dir", type=Path, default=Path("output"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="make-ugc",
        description="Generate videos using Gemini Veo",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- preset ---
    preset = sub.add_parser("preset", help="Generate video from a hardcoded preset")
    preset.add_argument("name", help="Preset name (use 'list' to see all)")

    # --- text-to-video ---
    t2v = sub.add_parser("text", help="Generate video from a text prompt")
    t2v.add_argument("prompt", help="Text prompt describing the video")

    # --- image-to-video ---
    i2v = sub.add_parser("image", help="Generate video from an image")
    i2v.add_argument("prompt", help="Text prompt describing the video")
    i2v.add_argument("--image", type=Path, required=True, help="Path to source image")

    # --- extend ---
    ext = sub.add_parser("extend", help="Extend an existing video")
    ext.add_argument("prompt", help="Text prompt for the extension")
    ext.add_argument("--video", type=Path, required=True, help="Path to source video")

    # reference images (text & preset only, Veo 3.1)
    for p in (preset, t2v):
        p.add_argument("--ref", type=Path, action="append", default=[], help="Reference image path (up to 3, Veo 3.1 only)")
        p.add_argument("--no-ref", action="store_true", help="Disable default character reference")

    _add_shared_options(preset, t2v, i2v, ext)

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "preset" and args.name == "list":
        for p in list_presets():
            print(f"  {p.name:20s} {p.description}")
        return

    api_key = load_api_key()

    prompt = args.prompt if args.command != "preset" else get_preset(args.name).prompt

    config = VideoConfig(
        prompt=prompt,
        model=args.model,
        aspect_ratio=args.aspect,
        resolution=args.resolution,
        duration=args.duration,
        output_dir=args.output_dir,
    )

    generator = VideoGenerator(api_key=api_key)

    refs = getattr(args, "ref", []) or []
    no_ref = getattr(args, "no_ref", False)

    if not no_ref and not refs and hasattr(args, "ref"):
        if DEFAULT_CHARACTER.exists():
            refs = [DEFAULT_CHARACTER]

    match args.command:
        case "preset" | "text":
            generator.generate_from_text(config, reference_images=refs or None)
        case "image":
            generator.generate_from_image(config, image_path=args.image)
        case "extend":
            generator.extend_video(config, source_video_path=args.video)


if __name__ == "__main__":
    main()
