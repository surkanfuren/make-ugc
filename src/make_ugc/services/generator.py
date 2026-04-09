import time
from pathlib import Path
from uuid import uuid4

from google import genai
from google.genai import types
from rich.console import Console

from ..models.config import PersonGeneration, VideoConfig

console = Console()


class VideoGenerator:
    def __init__(self, *, api_key: str) -> None:
        self.client = genai.Client(api_key=api_key)

    def generate_from_text(
        self,
        config: VideoConfig,
        *,
        reference_images: list[Path] | None = None,
    ) -> Path:
        has_refs = bool(reference_images)
        label = "with reference images" if has_refs else "from text prompt"
        console.print(f"[bold blue]Generating video {label}...[/]")
        console.print(f"  Model: {config.model}")
        console.print(f"  Resolution: {config.resolution} | Aspect: {config.aspect_ratio} | Duration: {config.duration}s")

        gen_config = types.GenerateVideosConfig(
            aspect_ratio=config.aspect_ratio,
            resolution=config.resolution,
            person_generation=PersonGeneration.ALLOW_ADULT if has_refs else PersonGeneration.ALLOW_ALL,
        )

        if has_refs:
            if len(reference_images) > 3:
                raise ValueError("Maximum 3 reference images allowed")
            console.print(f"  Reference images: {len(reference_images)}")
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
            refs = []
            for path in reference_images:
                mime = mime_map.get(path.suffix.lower(), "image/png")
                refs.append(
                    types.VideoGenerationReferenceImage(
                        image=types.Image(image_bytes=path.read_bytes(), mime_type=mime),
                        reference_type=types.VideoGenerationReferenceType.ASSET,
                    )
                )
            gen_config.reference_images = refs

        operation = self.client.models.generate_videos(
            model=config.model,
            prompt=config.prompt,
            config=gen_config,
        )

        return self._wait_and_save(operation, config)

    def generate_from_image(self, config: VideoConfig, *, image_path: Path) -> Path:
        console.print(f"[bold blue]Generating video from image...[/]")

        uploaded = self.client.files.upload(file=image_path)
        image = types.Image(file_uri=uploaded.uri, mime_type=uploaded.mime_type)

        operation = self.client.models.generate_videos(
            model=config.model,
            prompt=config.prompt,
            image=image,
            config=types.GenerateVideosConfig(
                aspect_ratio=config.aspect_ratio,
                resolution=config.resolution,
                person_generation=PersonGeneration.ALLOW_ADULT,
            ),
        )

        return self._wait_and_save(operation, config)

    def extend_video(self, config: VideoConfig, *, source_video_path: Path) -> Path:
        console.print(f"[bold blue]Extending video...[/]")

        uploaded = self.client.files.upload(file=source_video_path)

        operation = self.client.models.generate_videos(
            model=config.model,
            prompt=config.prompt,
            video=types.Video(file_uri=uploaded.uri, mime_type="video/mp4"),
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                resolution="720p",
                person_generation=PersonGeneration.ALLOW_ALL,
            ),
        )

        return self._wait_and_save(operation, config)

    def _wait_and_save(self, operation: object, config: VideoConfig) -> Path:
        with console.status("[yellow]Waiting for video generation...") as status:
            while not operation.done:
                time.sleep(config.poll_interval)
                operation = self.client.operations.get(operation)

        if not operation.response or not operation.response.generated_videos:
            console.print("[bold red]Generation failed — no video returned.[/]")
            console.print("[dim]This usually means the content was blocked by safety filters or audio processing failed.[/]")
            raise SystemExit(1)

        video = operation.response.generated_videos[0]
        self.client.files.download(file=video.video)

        output_path = config.output_dir / f"{uuid4().hex[:8]}.mp4"
        video.video.save(str(output_path))

        console.print(f"[bold green]Video saved to {output_path}[/]")
        return output_path
