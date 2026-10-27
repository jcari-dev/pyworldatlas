"""Standalone HTML pages for 3D maps: a full-window viewer with its own controls.

The page draws the figure with the plotly.js file from the installed map pack.
Plotly's in-figure buttons and slider are replaced by an accessible control
panel (view, terrain height, labels, motion, and export) that adapts to small
screens and to the reader's light or dark color scheme.
"""

from __future__ import annotations

import copy
from html import escape
import json
import math
from pathlib import Path
from typing import Any


def rotation_options(auto_rotate: bool, rotation_speed: float) -> tuple[bool, float]:
    """Validate the initial motion settings."""
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


KEYBOARD_HINT = (
    "Keyboard: select the map, then use the left and right arrow keys to turn it, "
    "the up and down arrow keys to tilt it, plus and minus to zoom, and 0 to reset "
    "the view."
)

PAGE_SCALE = 1.45
"""How much larger the scene is drawn on the standalone page than in ``to_dict()``."""


def page_figure(figure: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split a full figure into a control-free figure and the page's control data."""
    figure = copy.deepcopy(figure)
    layout = figure["layout"]
    menus = layout.pop("updatemenus")
    slider = layout.pop("sliders")[0]
    sources = layout.pop("annotations")[0]["text"]
    title = layout.pop("title")["text"]
    surfaces = {button["label"]: button["args"][0] for button in menus[0]["buttons"]}
    annotations = layout["scene"].get("annotations", [])
    controls = {
        "title": title,
        "sources": sources,
        "surfaces": surfaces,
        "heights": [
            {"label": step["label"], "value": step["args"][0]["scene.aspectratio.z"]}
            for step in slider["steps"]
        ],
        "activeHeight": slider["active"],
        "capitalLabels": [i for i, item in enumerate(annotations) if item.get("showarrow")],
        "riverLabels": [i for i, item in enumerate(annotations) if not item.get("showarrow")],
        "hasRivers": any(trace.get("name") == "Rivers" for trace in figure["data"]),
        "placeLayers": [trace["name"] for trace in figure["data"] if trace.get("meta") == "places"],
        "camera": copy.deepcopy(layout["scene"]["camera"]),
        "aspect": copy.deepcopy(layout["scene"]["aspectratio"]),
        "pageScale": PAGE_SCALE,
    }
    # A wide window gives the scene much more room than a notebook cell, so the
    # page draws it larger. The script repeats this scaling for every window size.
    ratio = layout["scene"]["aspectratio"]
    layout["scene"]["aspectratio"] = {axis: value * PAGE_SCALE for axis, value in ratio.items()}
    layout["margin"] = {"l": 0, "r": 0, "t": 0, "b": 0}
    layout["showlegend"] = False
    layout["paper_bgcolor"] = "rgba(0,0,0,0)"
    layout["plot_bgcolor"] = "rgba(0,0,0,0)"
    return figure, controls


def _script_json(value: Any) -> str:
    """Serialize ``value`` for an inline script without closing the tag early."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/")


_STYLE = """
:root {
  color-scheme: light dark;
  --bg: #f4f7fa; --panel: #ffffff; --text: #17293d; --muted: #5b6b7c;
  --line: #dbe3eb; --control: #7a8a9b; --accent: #287aa3; --accent-text: #ffffff; --soft: #eef4f8;
  --shadow: 0 10px 30px rgba(22, 48, 74, 0.10);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0e1620; --panel: #16212d; --text: #e6edf4; --muted: #9db0c2;
    --line: #2a3a4b; --control: #66798d; --accent: #5bb3db; --accent-text: #0b1a26; --soft: #1d2b39;
    --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  }
}
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
body {
  background: var(--bg); color: var(--text);
  font: 15px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  display: grid; grid-template-rows: auto 1fr auto; overflow: hidden;
}
header { display: flex; align-items: center; gap: 14px; padding: 16px 24px 8px; }
.badge {
  display: grid; place-items: center; min-width: 46px; height: 36px; padding: 0 8px;
  border-radius: 9px; background: var(--accent); color: var(--accent-text);
  font-weight: 700; font-size: 15px; letter-spacing: 0.06em;
}
h1 { font-size: 22px; font-weight: 650; margin: 0; letter-spacing: -0.01em; }
.subtitle { color: var(--muted); font-size: 13.5px; margin: 2px 0 0; }
main { position: relative; min-height: 0; }
.map-frame { position: absolute; inset: 0; border-radius: 12px; }
.map-frame:focus-visible { outline: 3px solid var(--accent); outline-offset: -3px; }
#pyworldatlas-map { position: absolute; inset: 0; }
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}
.about summary {
  cursor: pointer; color: var(--text); font-weight: 600; font-size: 13.5px;
  padding: 4px 0; list-style-position: inside;
}
.about p, .about ul { color: var(--text); font-size: 13.5px; margin: 6px 0; }
.about ul { padding-left: 18px; }
.about .hint { color: var(--muted); }
.panel {
  position: absolute; top: 12px; left: 24px; width: 248px; z-index: 5;
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  box-shadow: var(--shadow); padding: 6px 16px 16px;
  max-height: calc(100% - 24px); overflow-y: auto;
}
.panel-toggle { display: none; }
.group { margin-top: 12px; }
.group-label {
  color: var(--muted); font-size: 11.5px; font-weight: 650;
  letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 6px;
}
.segmented {
  display: flex; background: var(--soft); border: 1px solid var(--control);
  border-radius: 9px; padding: 3px; gap: 3px;
}
.segmented button {
  flex: 1; border: 0; border-radius: 7px; background: transparent; color: var(--text);
  font: inherit; font-size: 13.5px; padding: 6px 4px; cursor: pointer;
}
.segmented button[aria-pressed="true"] {
  background: var(--accent); color: var(--accent-text); font-weight: 600;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip, .action {
  border: 1px solid var(--control); background: var(--panel); color: var(--text);
  border-radius: 999px; font: inherit; font-size: 13.5px; padding: 5px 12px; cursor: pointer;
}
.chip[aria-pressed="true"] {
  background: var(--soft); border-color: var(--accent); color: var(--text); font-weight: 600;
}
.chip[aria-pressed="true"]::before { content: "\\2713  "; color: var(--accent); }
.motion { display: flex; align-items: center; gap: 10px; }
.motion input { flex: 1; accent-color: var(--accent); min-width: 0; }
.motion output { min-width: 34px; text-align: right; font-variant-numeric: tabular-nums; }
.actions { display: flex; gap: 8px; }
.action { flex: 1; border-radius: 9px; padding: 7px 8px; }
.action.primary { background: var(--accent); border-color: var(--accent); color: var(--accent-text); font-weight: 600; }
button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
button:hover { filter: brightness(0.97); }
footer { color: var(--muted); font-size: 12px; padding: 6px 24px 12px; text-align: center; }
@media (max-width: 760px) {
  header { padding: 12px 16px 4px; }
  .badge { min-width: 40px; height: 32px; }
  h1 { font-size: 19px; }
  .panel {
    top: auto; bottom: 0; left: 0; right: 0; width: auto; border-radius: 16px 16px 0 0;
    max-height: 62%; padding: 4px 16px 16px;
  }
  .panel[data-open="false"] .group { display: none; }
  .panel-toggle {
    display: block; width: 100%; border: 0; background: transparent; color: var(--text);
    font: inherit; font-weight: 600; padding: 10px 0 4px; cursor: pointer;
  }
  footer { display: none; }
}
"""

_CONTROLS_SCRIPT = r"""
(function () {
  const plot = document.getElementById('pyworldatlas-map');
  const controls = __CONTROLS__;
  const data = __DATA__;
  const layout = __LAYOUT__;
  const panel = document.querySelector('.panel');
  const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const reducedMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const NARROW_SCALE = 0.82;
  let terrainHeight = controls.aspect.z;
  let zoom = 1;
  const status = document.getElementById('map-status');
  function announce(message) {
    status.textContent = '';
    window.setTimeout(function () { status.textContent = message; }, 60);
  }
  function screenScale() { return (isWide() ? controls.pageScale : NARROW_SCALE) * zoom; }
  function isWide() { return window.innerWidth > 760; }

  let surface = Object.keys(controls.surfaces)[0];
  function colorbarFor() {
    // A vertical legend on wide screens; a thin bar across the top on phones.
    const base = controls.surfaces[surface].colorbar[0];
    const fitted = Object.assign({}, base);
    if (!isWide()) {
      Object.assign(fitted, {
        orientation: 'h', x: 0.5, xanchor: 'center', y: 1, yanchor: 'top',
        len: 0.86, thickness: 9,
        title: Object.assign({}, base.title || {}, {side: 'top'})
      });
    }
    return fitted;
  }

  function sceneFor() {
    const wide = isWide();
    const scale = screenScale();
    const start = wide
      ? Math.min(0.4, (panel.offsetLeft + panel.offsetWidth + 16) / Math.max(plot.clientWidth, 1))
      : 0;
    return {
      domain: {x: [start, 1], y: wide ? [0, 1] : [0.06, 0.88]},
      aspectratio: {
        x: controls.aspect.x * scale, y: controls.aspect.y * scale, z: terrainHeight * scale
      }
    };
  }

  function fitFigure(traces, figureLayout) {
    Object.assign(figureLayout.scene, sceneFor());
    traces[0].colorbar = colorbarFor();
  }

  if (dark) {
    const axis = {color: '#9db0c2', gridcolor: '#2a3a4b'};
    layout.font = Object.assign({}, layout.font, {color: '#e6edf4'});
    ['xaxis', 'yaxis', 'zaxis'].forEach(function (name) {
      layout.scene[name] = Object.assign({}, layout.scene[name], axis);
    });
  }

  fitFigure(data, layout);
  const config = __CONFIG__;
  Plotly.newPlot(plot, data, layout, config).then(wire);

  function wire() {
    let resizeTimer = null;
    window.addEventListener('resize', function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () {
        fitFigure(plot.data, plot.layout);
        Plotly.react(plot, plot.data, plot.layout);
      }, 150);
    });

    function choose(group, button) {
      group.querySelectorAll('button').forEach(function (item) {
        item.setAttribute('aria-pressed', String(item === button));
      });
    }

    document.querySelectorAll('[data-surface]').forEach(function (button) {
      button.addEventListener('click', function () {
        choose(button.parentElement, button);
        surface = button.dataset.surface;
        const update = Object.assign({}, controls.surfaces[surface]);
        update.colorbar = [colorbarFor()];
        Plotly.restyle(plot, update, [0]);
        announce('Colored by ' + surface.toLowerCase() + '.');
      });
    });

    document.querySelectorAll('[data-height]').forEach(function (button) {
      button.addEventListener('click', function () {
        choose(button.parentElement, button);
        terrainHeight = Number(button.dataset.height);
        Plotly.relayout(plot, {'scene.aspectratio.z': terrainHeight * screenScale()});
        announce('Terrain height ' + button.textContent + '.');
      });
    });

    function toggleLabels(button, indexes) {
      const visible = button.getAttribute('aria-pressed') !== 'true';
      button.setAttribute('aria-pressed', String(visible));
      const update = {};
      indexes.forEach(function (index) {
        update['scene.annotations[' + index + '].visible'] = visible;
      });
      Plotly.relayout(plot, update);
      announce(button.textContent + (visible ? ' shown.' : ' hidden.'));
    }
    const capitalChip = document.querySelector('[data-labels="capital"]');
    if (capitalChip) {
      capitalChip.addEventListener('click', function () {
        toggleLabels(capitalChip, controls.capitalLabels);
      });
    }
    const riverChip = document.querySelector('[data-labels="rivers"]');
    if (riverChip) {
      riverChip.addEventListener('click', function () {
        toggleLabels(riverChip, controls.riverLabels);
      });
    }
    document.querySelectorAll('[data-trace]').forEach(function (chip) {
      chip.addEventListener('click', function () {
        const visible = chip.getAttribute('aria-pressed') !== 'true';
        chip.setAttribute('aria-pressed', String(visible));
        const name = chip.getAttribute('data-trace');
        const index = plot.data.findIndex(function (trace) { return trace.name === name; });
        Plotly.restyle(plot, {visible: visible}, [index]);
        announce(name + (visible ? ' shown.' : ' hidden.'));
      });
    });
    const riverLines = document.querySelector('[data-layer="rivers"]');
    if (riverLines) {
      riverLines.addEventListener('click', function () {
        const visible = riverLines.getAttribute('aria-pressed') !== 'true';
        riverLines.setAttribute('aria-pressed', String(visible));
        const index = plot.data.findIndex(function (trace) { return trace.name === 'Rivers'; });
        Plotly.restyle(plot, {visible: visible}, [index]);
        announce('Rivers ' + (visible ? 'shown.' : 'hidden.'));
      });
    }

    const rotateButton = document.getElementById('rotate');
    const speedInput = document.getElementById('speed');
    const speedOutput = document.getElementById('speed-value');
    speedInput.value = String(__ROTATION_SPEED__);
    function formatSpeed(value) {
      return Number(value).toFixed(2).replace(/\.?0+$/, '') + '×';
    }
    speedOutput.textContent = formatSpeed(speedInput.value);
    speedInput.addEventListener('input', function () {
      speedOutput.textContent = formatSpeed(speedInput.value);
    });

    let rotating = false;
    let frameHandle = null;
    let lastFrameTime = 0;
    let applyingCamera = false;
    const degreesPerSecond = 18;

    function setRotating(value) {
      rotating = Boolean(value);
      lastFrameTime = 0;
      rotateButton.textContent = rotating ? 'Pause' : 'Rotate';
      rotateButton.setAttribute('aria-pressed', String(rotating));
      if (!rotating && frameHandle !== null) {
        window.cancelAnimationFrame(frameHandle);
        frameHandle = null;
      }
      if (rotating && frameHandle === null) {
        frameHandle = window.requestAnimationFrame(rotateFrame);
      }
    }

    function rotateFrame(timestamp) {
      frameHandle = null;
      if (!rotating) {
        return;
      }
      const elapsed = lastFrameTime ? Math.min((timestamp - lastFrameTime) / 1000, 0.05) : 0;
      lastFrameTime = timestamp;
      const camera = (plot.layout.scene && plot.layout.scene.camera) || {};
      const eye = camera.eye || controls.camera.eye;
      const eyeX = Number(eye.x) || 0.35;
      const eyeY = Number(eye.y) || -0.55;
      const radius = Math.hypot(eyeX, eyeY) || 0.65;
      const angle = Math.atan2(eyeY, eyeX) +
        elapsed * degreesPerSecond * Number(speedInput.value) * Math.PI / 180;
      applyingCamera = true;
      Promise.resolve(Plotly.relayout(plot, {
        'scene.camera.eye': {x: radius * Math.cos(angle), y: radius * Math.sin(angle), z: Number(eye.z) || 0.68}
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
      if (Object.keys(update).some(function (key) { return key.indexOf('scene.camera') === 0; })) {
        setRotating(false);
      }
    }

    rotateButton.addEventListener('click', function () {
      setRotating(!rotating);
      announce(rotating ? 'Rotating.' : 'Rotation paused.');
    });

    function resetView() {
      setRotating(false);
      zoom = 1;
      Plotly.relayout(plot, {
        'scene.camera': JSON.parse(JSON.stringify(controls.camera)),
        'scene.aspectratio': sceneFor().aspectratio
      });
      announce('View reset.');
    }
    document.getElementById('reset').addEventListener('click', resetView);

    // Keyboard: turn with left and right, tilt with up and down, zoom with + and -.
    const frame = document.getElementById('map-frame');
    function moveCamera(turnDegrees, tilt) {
      setRotating(false);
      const eye = (plot.layout.scene.camera && plot.layout.scene.camera.eye) || controls.camera.eye;
      const radius = Math.hypot(eye.x, eye.y) || 0.65;
      const angle = Math.atan2(eye.y, eye.x) + turnDegrees * Math.PI / 180;
      const height = Math.min(2.5, Math.max(0.1, eye.z + tilt));
      Plotly.relayout(plot, {
        'scene.camera.eye': {x: radius * Math.cos(angle), y: radius * Math.sin(angle), z: height}
      });
    }
    function changeZoom(factor) {
      zoom = Math.min(3, Math.max(0.5, zoom * factor));
      Plotly.relayout(plot, {'scene.aspectratio': sceneFor().aspectratio});
      announce('Zoom ' + Math.round(zoom * 100) + ' percent.');
    }
    frame.addEventListener('keydown', function (event) {
      const keys = {
        ArrowLeft: function () { moveCamera(-15, 0); },
        ArrowRight: function () { moveCamera(15, 0); },
        ArrowUp: function () { moveCamera(0, 0.12); },
        ArrowDown: function () { moveCamera(0, -0.12); },
        '+': function () { changeZoom(1.2); },
        '=': function () { changeZoom(1.2); },
        '-': function () { changeZoom(1 / 1.2); },
        '0': resetView,
        Home: resetView
      };
      const action = keys[event.key];
      if (action) {
        event.preventDefault();
        action();
      }
    });
    document.getElementById('download').addEventListener('click', function () {
      const resume = rotating;
      setRotating(false);
      Promise.resolve(Plotly.downloadImage(plot, {
        format: 'png',
        filename: __PNG_FILENAME__,
        width: 1600,
        height: 900,
        scale: 2
      })).finally(function () {
        if (resume) {
          setRotating(true);
        }
      });
    });
    plot.on('plotly_relayout', pauseForManualCameraChange);
    plot.on('plotly_relayouting', pauseForManualCameraChange);

    const toggle = document.querySelector('.panel-toggle');
    toggle.addEventListener('click', function () {
      const open = panel.dataset.open !== 'true';
      panel.dataset.open = String(open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Hide map controls' : 'Show map controls';
    });

    setRotating(false);
    if (__AUTO_ROTATE__ && !reducedMotion) {
      setRotating(true);
    }
  }
})();
"""


def _segmented(label: str, items: list[tuple[str, str, str, bool]]) -> str:
    buttons = "".join(
        f'<button type="button" {attribute}="{escape(value)}" '
        f'aria-pressed="{"true" if active else "false"}">{escape(text)}</button>'
        for attribute, value, text, active in items
    )
    return (
        f'<div class="group"><p class="group-label">{escape(label)}</p>'
        f'<div class="segmented" role="group" aria-label="{escape(label)}">{buttons}</div></div>'
    )


def document(
    figure: dict[str, Any],
    *,
    renderer: Path,
    country: str,
    code: str,
    subtitle: str,
    description: list[str],
    auto_rotate: bool,
    rotation_speed: float,
    png_filename: str,
) -> str:
    """Return a complete offline HTML page that draws ``figure`` with plotly.js."""
    auto_rotate, rotation_speed = rotation_options(auto_rotate, rotation_speed)
    plot_figure, controls = page_figure(figure)
    library = renderer.read_text(encoding="utf-8")
    config = {
        "responsive": True,
        "displaylogo": False,
        "scrollZoom": True,
        "displayModeBar": False,
    }
    surfaces = [
        ("data-surface", name, name, index == 0) for index, name in enumerate(controls["surfaces"])
    ]
    heights = [
        ("data-height", str(item["value"]), item["label"], index == controls["activeHeight"])
        for index, item in enumerate(controls["heights"])
    ]
    chips = []
    if controls["capitalLabels"]:
        chips.append('<button type="button" class="chip" data-labels="capital" aria-pressed="true">Capital name</button>')
    if controls["hasRivers"]:
        chips.append('<button type="button" class="chip" data-layer="rivers" aria-pressed="true">Rivers</button>')
    if controls["riverLabels"]:
        chips.append('<button type="button" class="chip" data-labels="rivers" aria-pressed="false">River names</button>')
    for layer in controls["placeLayers"]:
        chips.append(
            f'<button type="button" class="chip" data-trace="{escape(layer)}" aria-pressed="true">{escape(layer)}</button>'
        )
    labels = (
        '<div class="group"><p class="group-label">Show</p>'
        f'<div class="chips">{"".join(chips)}</div></div>'
        if chips
        else ""
    )
    script = (
        _CONTROLS_SCRIPT.replace("__CONTROLS__", _script_json(controls))
        .replace("__DATA__", _script_json(plot_figure["data"]))
        .replace("__LAYOUT__", _script_json(plot_figure["layout"]))
        .replace("__CONFIG__", _script_json(config))
        .replace("__AUTO_ROTATE__", json.dumps(auto_rotate))
        .replace("__ROTATION_SPEED__", json.dumps(rotation_speed))
        .replace("__PNG_FILENAME__", json.dumps(png_filename))
    )
    about = "".join(f"<p>{escape(sentence)}</p>" for sentence in description)
    title = f"{country} 3D map · PyWorldAtlas"
    badge = f'<span class="badge" aria-hidden="true">{escape(code)}</span>' 
    return "\n".join(
        (
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8" />',
            '<meta name="viewport" content="width=device-width, initial-scale=1" />',
            f"<title>{escape(title)}</title>",
            f"<style>{_STYLE}</style>",
            "</head>",
            "<body>",
            f'<header>{badge}<div><h1>{escape(country)}</h1>'
            f'<p class="subtitle">{escape(subtitle)}</p></div></header>',
            "<main>",
            '<div class="map-frame" id="map-frame" tabindex="0" role="img" '
            f'aria-label="3D terrain map of {escape(country)}" '
            'aria-describedby="map-description map-keys">',
            '<div id="pyworldatlas-map" aria-hidden="true"></div>',
            "</div>",
            '<p id="map-status" class="sr-only" role="status" aria-live="polite"></p>',
            '<aside class="panel" data-open="false" aria-label="Map controls">',
            '<button type="button" class="panel-toggle" aria-expanded="false">Show map controls</button>',
            _segmented("Color by", surfaces),
            _segmented("Terrain height", heights),
            labels,
            '<div class="group"><p class="group-label">Motion</p><div class="motion">'
            '<button type="button" class="action" id="rotate" aria-pressed="false">Rotate</button>'
            '<input id="speed" type="range" min="0.25" max="3" step="0.25" aria-label="Rotation speed" />'
            '<output id="speed-value" for="speed"></output></div></div>',
            '<div class="group"><p class="group-label">View</p><div class="actions">'
            '<button type="button" class="action" id="reset">Reset view</button>'
            '<button type="button" class="action primary" id="download">Save PNG</button>'
            "</div></div>",
            '<div class="group"><details class="about"><summary>About this map</summary>'
            f'<div id="map-description">{about}</div>'
            f'<p class="hint" id="map-keys">{escape(KEYBOARD_HINT)}</p>'
            "</details></div>",
            "</aside>",
            "</main>",
            f'<footer>{escape(controls["sources"])}</footer>',
            "<script>window.PlotlyConfig = {MathJaxConfig: 'local'};</script>",
            f'<script charset="utf-8">{library}</script>',
            f"<script>{script}</script>",
            "</body>",
            "</html>",
            "",
        )
    )
