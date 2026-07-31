"""Create an optimized documentation GIF from a real PyWorldAtlas 3D map."""

from __future__ import annotations

import argparse
import asyncio
from io import BytesIO
import math
from pathlib import Path


def _positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def _camera_eyes(
    *, frames: int, start_x: float, start_y: float, height: float, zoom: float
) -> tuple[dict[str, float], ...]:
    radius = math.hypot(start_x, start_y) / zoom
    start_angle = math.atan2(start_y, start_x)
    return tuple(
        {
            "x": radius * math.cos(start_angle + math.tau * index / frames),
            "y": radius * math.sin(start_angle + math.tau * index / frames),
            "z": height / zoom,
        }
        for index in range(frames)
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render one smooth 360-degree PyWorldAtlas map rotation as an "
            "optimized GIF for documentation and project pages."
        )
    )
    parser.add_argument("country", help="country name or code accepted by Atlas.map()")
    parser.add_argument("--quality", choices=("auto", "overview", "standard"), default="auto")
    parser.add_argument("--output", type=Path, required=True, help="destination .gif path")
    parser.add_argument("--seconds", type=_positive_float, default=6.0)
    parser.add_argument("--fps", type=_positive_int, default=10)
    parser.add_argument("--width", type=_positive_int, default=960)
    parser.add_argument("--height", type=_positive_int, default=600)
    parser.add_argument("--scale", type=_positive_float, default=1.0)
    parser.add_argument(
        "--projection",
        choices=("perspective", "orthographic"),
        default="perspective",
        help="3D camera projection used by the animation (default: perspective)",
    )
    parser.add_argument(
        "--zoom",
        type=_positive_float,
        default=1.0,
        help="camera magnification; values above 1 move closer (default: 1)",
    )
    parser.add_argument("--colors", type=_positive_int, choices=range(32, 257), default=128)
    return parser


async def _render_frames(
    *, figure: object, eyes: tuple[dict[str, float], ...], args: argparse.Namespace
) -> list[object]:
    from kaleido import Kaleido
    from PIL import Image

    rendered: list[object] = []
    async with Kaleido(n=1, timeout=120) as renderer:
        for number, eye in enumerate(eyes, 1):
            print(f"Rendering frame {number}/{len(eyes)}", end="\r", flush=True)
            figure.update_layout(scene_camera={"eye": eye})
            png = await renderer.calc_fig(
                figure,
                opts={
                    "format": "png",
                    "width": args.width,
                    "height": args.height,
                    "scale": args.scale,
                },
            )
            with Image.open(BytesIO(png)) as image:
                rendered.append(
                    image.convert("RGB").quantize(
                        colors=args.colors,
                        method=Image.Quantize.MEDIANCUT,
                        dither=Image.Dither.FLOYDSTEINBERG,
                    )
                )
    return rendered


def main() -> int:
    args = _parser().parse_args()
    if args.output.suffix.casefold() != ".gif":
        raise SystemExit("--output must end in .gif")

    try:
        from PIL import Image
        from pyworldatlas import Atlas
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Install the project, Pillow, and Kaleido first: "
            "python -m pip install -e . -e packages/mapview "
            "-e packages/mapdata-standard Pillow kaleido"
        ) from error

    with Atlas() as atlas:
        map_view = atlas.map(args.country, quality=args.quality)
        figure = map_view.figure()

    camera = figure.layout.scene.camera.eye
    if args.projection == "perspective":
        start_x, start_y, camera_height = 0.55, -0.85, 0.55
    else:
        start_x, start_y, camera_height = (
            float(camera.x),
            float(camera.y),
            float(camera.z),
        )
    frame_count = max(2, round(args.seconds * args.fps))
    eyes = _camera_eyes(
        frames=frame_count,
        start_x=start_x,
        start_y=start_y,
        height=camera_height,
        zoom=args.zoom,
    )
    figure.update_layout(
        width=args.width,
        height=args.height,
        autosize=False,
        scene_camera={"projection": {"type": args.projection}},
        scene_xaxis_title="",
        scene_yaxis_title="",
    )

    try:
        rendered = asyncio.run(_render_frames(figure=figure, eyes=eyes, args=args))
    except Exception as error:
        raise SystemExit(
            "GIF rendering requires Pillow, Kaleido, and a browser supported "
            "by Kaleido. Install them with: python -m pip install Pillow kaleido"
        ) from error

    args.output.parent.mkdir(parents=True, exist_ok=True)
    first, *remaining = rendered
    first.save(
        args.output,
        save_all=True,
        append_images=remaining,
        duration=round(1000 / args.fps),
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(" " * 60, end="\r")
    print(f"Wrote {args.output.resolve()} ({args.output.stat().st_size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
