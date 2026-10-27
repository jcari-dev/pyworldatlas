"""Standalone HTML documents for 3D maps, with motion and export controls."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

VIEWER_CONTROLS_SCRIPT = r"""
(function () {
  const plot = document.getElementById('{plot_id}');
  if (!plot || plot.dataset.pyworldatlasControls === 'ready') {
    return;
  }
  plot.dataset.pyworldatlasControls = 'ready';

  const style = document.createElement('style');
  style.textContent = `
    .pyworldatlas-viewer-controls {
      align-items: center;
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid #b8c9dc;
      border-radius: 7px;
      box-shadow: 0 2px 8px rgba(24, 52, 82, 0.10);
      color: #243b5a;
      display: flex;
      font: 14px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      gap: 10px;
      padding: 7px 9px;
      position: absolute;
      right: 28px;
      top: 126px;
      z-index: 1000;
    }
    .pyworldatlas-viewer-controls button {
      background: #f7fbff;
      border: 1px solid #9fb6d0;
      border-radius: 5px;
      color: #243b5a;
      cursor: pointer;
      font: inherit;
      padding: 7px 11px;
    }
    .pyworldatlas-viewer-controls button:hover,
    .pyworldatlas-viewer-controls button:focus-visible {
      background: #eaf4fb;
      border-color: #4c83b6;
      outline: none;
    }
    .pyworldatlas-viewer-controls button[aria-pressed="true"] {
      background: #287aa3;
      border-color: #21698d;
      color: #ffffff;
    }
    .pyworldatlas-speed-control {
      align-items: center;
      display: flex;
      gap: 7px;
      white-space: nowrap;
    }
    .pyworldatlas-speed-control input {
      accent-color: #287aa3;
      cursor: pointer;
      width: 112px;
    }
    .pyworldatlas-speed-control output {
      min-width: 32px;
      text-align: right;
    }
    @media (max-width: 760px) {
      .pyworldatlas-viewer-controls {
        left: 12px;
        right: 12px;
        top: 164px;
      }
      .pyworldatlas-speed-control {
        flex: 1;
      }
      .pyworldatlas-speed-control input {
        min-width: 70px;
        width: 100%;
      }
    }
  `;
  document.head.appendChild(style);

  const controls = document.createElement('div');
  controls.className = 'pyworldatlas-viewer-controls';
  controls.setAttribute('role', 'group');
  controls.setAttribute('aria-label', 'Map motion and export controls');

  const rotateButton = document.createElement('button');
  rotateButton.type = 'button';
  rotateButton.textContent = 'Rotate';
  rotateButton.setAttribute('aria-pressed', 'false');

  const speedLabel = document.createElement('label');
  speedLabel.className = 'pyworldatlas-speed-control';
  speedLabel.append(document.createTextNode('Speed'));
  const speedInput = document.createElement('input');
  speedInput.type = 'range';
  speedInput.min = '0.25';
  speedInput.max = '3';
  speedInput.step = '0.25';
  speedInput.value = String(__ROTATION_SPEED__);
  speedInput.setAttribute('aria-label', 'Rotation speed');
  const speedOutput = document.createElement('output');
  function formatSpeed(value) {
    return `${Number(value).toFixed(2).replace(/\.?0+$/, '')}×`;
  }
  speedOutput.value = formatSpeed(speedInput.value);
  speedOutput.textContent = speedOutput.value;
  speedLabel.append(speedInput, speedOutput);

  const downloadButton = document.createElement('button');
  downloadButton.type = 'button';
  downloadButton.textContent = 'Download PNG';

  controls.append(rotateButton, speedLabel, downloadButton);
  const wrapper = plot.parentElement;
  if (wrapper) {
    wrapper.style.position = 'relative';
    wrapper.appendChild(controls);
  }

  let rotating = false;
  let frameHandle = null;
  let lastFrameTime = 0;
  let applyingCamera = false;
  const degreesPerSecond = 18;
  const reducedMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function updateButton() {
    rotateButton.textContent = rotating ? 'Pause' : 'Rotate';
    rotateButton.setAttribute('aria-pressed', String(rotating));
  }

  function setRotating(value) {
    rotating = Boolean(value);
    lastFrameTime = 0;
    if (!rotating && frameHandle !== null) {
      window.cancelAnimationFrame(frameHandle);
      frameHandle = null;
    }
    updateButton();
    if (rotating && frameHandle === null) {
      frameHandle = window.requestAnimationFrame(rotateFrame);
    }
  }

  function rotateFrame(timestamp) {
    frameHandle = null;
    if (!rotating) {
      return;
    }
    const elapsed = lastFrameTime
      ? Math.min((timestamp - lastFrameTime) / 1000, 0.05)
      : 0;
    lastFrameTime = timestamp;
    const camera = (plot.layout.scene && plot.layout.scene.camera) || {};
    const eye = camera.eye || {x: 0.35, y: -0.55, z: 0.68};
    const eyeX = Number(eye.x) || 0.35;
    const eyeY = Number(eye.y) || -0.55;
    const radius = Math.hypot(eyeX, eyeY) || 0.65;
    const speed = Number(speedInput.value);
    const angle = Math.atan2(eyeY, eyeX) +
      elapsed * degreesPerSecond * speed * Math.PI / 180;
    applyingCamera = true;
    Promise.resolve(Plotly.relayout(plot, {
      'scene.camera.eye': {
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
        z: Number(eye.z) || 0.68
      }
    })).finally(function () {
      applyingCamera = false;
      if (rotating) {
        frameHandle = window.requestAnimationFrame(rotateFrame);
      }
    });
  }

  function pauseForManualCameraChange(update) {
    if (!rotating || applyingCamera || !update) {
      return;
    }
    if (Object.keys(update).some(function (key) {
      return key.indexOf('scene.camera') === 0;
    })) {
      setRotating(false);
    }
  }

  rotateButton.addEventListener('click', function () {
    setRotating(!rotating);
  });
  speedInput.addEventListener('input', function () {
    speedOutput.value = formatSpeed(speedInput.value);
    speedOutput.textContent = speedOutput.value;
  });
  downloadButton.addEventListener('click', function () {
    const resumeAfterExport = rotating;
    setRotating(false);
    Promise.resolve(Plotly.downloadImage(plot, {
      format: 'png',
      filename: __PNG_FILENAME__,
      width: 1600,
      height: 900,
      scale: 2
    })).finally(function () {
      if (resumeAfterExport) {
        setRotating(true);
      }
    });
  });
  plot.on('plotly_relayout', pauseForManualCameraChange);
  plot.on('plotly_relayouting', pauseForManualCameraChange);

  updateButton();
  if (__AUTO_ROTATE__ && !reducedMotion) {
    setRotating(true);
  }
})();
"""


def rotation_options(auto_rotate: bool, rotation_speed: float) -> tuple[bool, float]:
    if not isinstance(auto_rotate, bool):
        raise TypeError("auto_rotate must be True or False")
    if isinstance(rotation_speed, bool):
        raise TypeError("rotation_speed must be a number from 0.25 through 3")
    try:
        speed = float(rotation_speed)
    except (TypeError, ValueError) as error:
        raise TypeError("rotation_speed must be a number from 0.25 through 3") from error
    if not math.isfinite(speed) or not 0.25 <= speed <= 3:
        raise ValueError("rotation_speed must be from 0.25 through 3")
    return auto_rotate, speed


def viewer_controls_script(
    *, auto_rotate: bool, rotation_speed: float, png_filename: str
) -> str:
    auto_rotate, rotation_speed = rotation_options(auto_rotate, rotation_speed)
    return (
        VIEWER_CONTROLS_SCRIPT.replace(
            "__AUTO_ROTATE__", json.dumps(auto_rotate)
        )
        .replace("__ROTATION_SPEED__", json.dumps(rotation_speed))
        .replace("__PNG_FILENAME__", json.dumps(png_filename))
    )


def _script_json(value: Any) -> str:
    """Serialize ``value`` for an inline script without closing the tag early."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/")


def document(
    figure: dict[str, Any],
    *,
    renderer: Path,
    title: str,
    config: dict[str, Any],
    post_script: str,
    div_id: str = "pyworldatlas-map",
) -> str:
    """Return a complete offline HTML page that draws ``figure`` with plotly.js."""
    library = renderer.read_text(encoding="utf-8")
    script = post_script.replace("{plot_id}", div_id)
    plot = (
        f"Plotly.newPlot({json.dumps(div_id)}, {_script_json(figure['data'])}, "
        f"{_script_json(figure['layout'])}, {_script_json(config)})"
    )
    return "\n".join(
        (
            "<html>",
            f'<head><title>{title}</title><meta charset="utf-8" /></head>',
            "<body>",
            '    <div style="height:100%; width:100%;">',
            "        <script type=\"text/javascript\">"
            "window.PlotlyConfig = {MathJaxConfig: 'local'};</script>",
            f'        <script charset="utf-8" type="text/javascript">{library}</script>',
            f'        <div id="{div_id}" class="plotly-graph-div" '
            'style="height:100%; width:100%;"></div>',
            "        <script type=\"text/javascript\">",
            "window.PLOTLYENV = window.PLOTLYENV || {};",
            f"if (document.getElementById({json.dumps(div_id)})) {{",
            f"  {plot}.then(function () {{{script}}});",
            "}",
            "        </script>",
            "    </div>",
            "</body>",
            "</html>",
            "",
        )
    )
