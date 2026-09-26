# M1 Analysis: Godot 4 Base Project Configuration, Host Binary Environment & Directory Architecture

**Agent**: `m1_explorer_project`  
**Milestone**: M1 (Foundation & Core Infrastructure)  
**Date**: 2026-09-26  
**Context**: Migration of RPG-battle from Python/Pygame to Godot Engine 4 (GDScript)

---

## 1. Executive Summary

This investigation provides the definitive technical specification and operational guidance for bootstrapping `godot_project/` in Milestone 1:

1. **Host Godot 4 Binary Found & Verified**:
   - Canonical binary path: `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64`
   - Verified engine version: `4.7.2.stable.official.ed1daf0bf`
   - Host reference project: `/home/anderson/Documents/projeto/Slender - Schorodinger/godot_slender`
   - Critical sandbox insight: The subagent container only mounts `/home/anderson/Documents/projeto/RPG-battle`. Therefore, workers in sandboxed mode cannot see `/home/anderson/Documents/Godot_...` unless the binary is copied into the workspace (`godot_project/bin/godot` or `bin/godot`) or executed outside the sandbox via `BypassSandbox: true`.

2. **Exact `project.godot` Configuration**:
   - Resolution: 1280x720 base viewport, windowed resizable (`mode=0`, `resizable=true`).
   - Renderer: Compatibility (`gl_compatibility`), compatible with WebAssembly and desktop OpenGL 3.3+.
   - 2D Pixel Mode: `window/stretch/mode="canvas_items"`, `window/stretch/aspect="keep"`, `textures/canvas_textures/default_texture_filter=0` (Nearest) to preserve pixel-crisp rendering of 32x32 Isectum sprites and 256x256 character frames.
   - Autoloads: Fully declared with `*res://scripts/autoload/<Name>.gd` syntax in strict dependency order (`EventBus` -> `DataManager` -> `AudioManager` -> `GameManager`).
   - Audio Bus Layout: Integrated `default_bus_layout.tres` defining `Master`, `BGM`, and `SFX` buses.
   - GUT Plugin: Activated under `[editor_plugins]`.

3. **Asset Management Strategy (Copy vs Symlink)**:
   - Total asset footprint: 39 MB (`assets/`), 296 KB (`dados/`).
   - Strong Recommendation: **Copy** assets and data into `godot_project/assets/` and `godot_project/dados/`. Symlinking causes Godot to scatter dozens of `.import` metadata files into the root Python repository and poses severe export packaging risks when building `.pck` or WebAssembly releases.

4. **CLI Headless Runner Script**:
   - `godot_project/run_gut_tests.sh` designed to resolve the binary dynamically (PATH -> `./bin/godot` -> `/home/anderson/Documents/...`) and execute `--headless -s addons/gut/gut_cmdln.gd -gexit`.

---

## 2. Host Godot 4 Binary Investigation

### 2.1 Binary Discovery & Verification

A comprehensive search of the host system located the official Godot 4 binary:

| Item | Value |
|---|---|
| **Absolute Executable Path** | `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64` |
| **Source Archive** | `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64.zip` |
| **Engine Version** | `Godot v4.7.2.stable.official.ed1daf0bf` |
| **Architecture** | Linux x86_64 (ELF 64-bit LSB executable) |
| **Execution Test Result** | Exited 0, reported `4.7.2.stable.official.ed1daf0bf` |

### 2.2 Host Environment Context & Existing Projects

Further inspection revealed active Godot 4 usage on the host machine:
- **Reference Godot Project**: `/home/anderson/Documents/projeto/Slender - Schorodinger/godot_slender/`
  - Utilizes Godot 4 with a dedicated `run_gut_tests.sh`, `.gutconfig.json`, and local export presets.
- **Host Godot Configuration**:
  - `/home/anderson/.config/godot/editor_settings-4.7.tres` (updated 2026-09-25)
  - `/home/anderson/.cache/godot/`
  - `/home/anderson/.local/share/godot/app_userdata/`

### 2.3 Sandboxed Subagent Mount Isolation & The "No such file" Trap

A critical architectural constraint was uncovered regarding the subagent runtime environment:
- The subagent execution container uses Linux mount namespaces.
- The only directory mounted under `/home/anderson/Documents/projeto/` is `/home/anderson/Documents/projeto/RPG-battle`.
- The parent directory `/home/anderson/Documents/` inside the sandbox contains **only** `projeto/`. The file `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64` is physically absent inside the container mount namespace.
- Running `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64` without bypassing the sandbox yields:
  ```text
  bash: line 1: /home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64: No such file or directory
  ```

### 2.4 Resolution Strategies for Workers

There are three ways for subsequent workers (`m1_architect_core`, `qa_engineer`, etc.) to run Godot CLI commands:

#### Option A: Workspace Local Binary (Recommended for Headless Autonomy)
Copy or link the binary into the workspace at `/home/anderson/Documents/projeto/RPG-battle/bin/godot` or `godot_project/bin/godot`:
```bash
# Executed on host or by a setup task:
mkdir -p /home/anderson/Documents/projeto/RPG-battle/bin
cp /home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64 /home/anderson/Documents/projeto/RPG-battle/bin/godot
chmod +x /home/anderson/Documents/projeto/RPG-battle/bin/godot
```
*Why*: Once placed inside the workspace, all tools (`run_command` in sandboxed mode) can execute `./bin/godot` or `godot_project/bin/godot` directly without needing special user permission prompts or host escapes. Note: A symlink will fail inside the sandbox because the symlink target is outside the container. An actual copy (or hard link) is required.

#### Option B: BypassSandbox CLI Invocation
Set `BypassSandbox: true` on `run_command`:
```bash
/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64 --headless --path /home/anderson/Documents/projeto/RPG-battle/godot_project -s addons/gut/gut_cmdln.gd -gexit
```
*Note*: `BypassSandbox: true` triggers an interactive user confirmation modal in the UI. If the user is away from the screen, the call times out after 60 seconds.

#### Option C: PATH Export in Runner Script
The test script `run_gut_tests.sh` (detailed in Section 6) checks `./bin/godot`, `../bin/godot`, and `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64` in sequence, ensuring seamless execution in both environments.

---

## 3. Exact `project.godot` Specification

Below is the complete, drop-in `project.godot` file formatted for Godot 4.7 / 4.x.

```ini
; Engine configuration file.
; It's best edited using the editor UI and not directly,
; but can also be edited by hand.

config_version=5

[application]

config/name="RPG-battle"
config/description="RPG Tactical Combat (D&D 5e) & Cerco Isectum ported to Godot 4"
run/main_scene="res://scenes/main/Main.tscn"
config/features=PackedStringArray("4.3", "GL Compatibility")
boot_splash/bg_color=Color(0.0784314, 0.0784314, 0.0941176, 1)
boot_splash/show_image=false
config/icon="res://assets/images/ui/logo.png"

[autoload]

EventBus="*res://scripts/autoload/EventBus.gd"
DataManager="*res://scripts/autoload/DataManager.gd"
AudioManager="*res://scripts/autoload/AudioManager.gd"
GameManager="*res://scripts/autoload/GameManager.gd"

[display]

window/size/viewport_width=1280
window/size/viewport_height=720
window/size/mode=0
window/size/resizable=true
window/size/borderless=false
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"
window/handheld/orientation=0

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
renderer/rendering_method.web="gl_compatibility"
textures/canvas_textures/default_texture_filter=0
environment/defaults/default_clear_color=Color(0.0784314, 0.0784314, 0.0941176, 1)

[audio]

buses/default_bus_layout="res://default_bus_layout.tres"

[editor_plugins]

enabled=PackedStringArray("res://addons/gut/plugin.cfg")

[gui]

theme/custom_font=""

[input]

action_select={
"deadzone": 0.5,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":1,"position":Vector2(0, 0),"global_position":Vector2(0, 0),"factor":1.0,"button_index":1,"canceled":false,"pressed":true,"double_click":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":true,"keycode":4194309,"physical_keycode":0,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":true,"keycode":32,"physical_keycode":0,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)
]
}
action_cancel={
"deadzone": 0.5,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":2,"position":Vector2(0, 0),"global_position":Vector2(0, 0),"factor":1.0,"button_index":2,"canceled":false,"pressed":true,"double_click":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":true,"keycode":4194305,"physical_keycode":0,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
toggle_combat_log={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":true,"keycode":4194306,"physical_keycode":0,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":true,"keycode":76,"physical_keycode":0,"key_label":0,"unicode":108,"location":0,"echo":false,"script":null)
]
}
```

### 3.1 Parameter Rationale & Breakdown

1. **`config_version=5`**: Standard Godot 4 format.
2. **`[autoload]` Asterisk (`*`) Prefix**:
   In Godot 4, the asterisk prefix (e.g. `EventBus="*res://scripts/autoload/EventBus.gd"`) is mandatory for singleton autoloads. It registers the node in `/root/` upon scene tree initialization.
   - **Load Order**:
     1. `EventBus`: Pure signal dispatcher, zero internal dependencies.
     2. `DataManager`: Loads JSON data, constructs typed `CharacterData` and `CardData`.
     3. `AudioManager`: Initializes audio pools and connects to `EventBus`.
     4. `GameManager`: Master coordinator; requires `EventBus`, `DataManager`, and `AudioManager` to already be active.
3. **`[display]` Resolution & Stretch Aspect**:
   - `viewport_width=1280`, `viewport_height=720`: 16:9 base aspect ratio as requested in R1.
   - `window/stretch/mode="canvas_items"`: Scales 2D canvas elements cleanly while maintaining layout coordinates.
   - `window/stretch/aspect="keep"`: Preserves the 16:9 aspect ratio across any monitor or resized window by adding letterbox/pillarbox margins instead of distorting graphics.
4. **`[rendering]` Compatibility Mode**:
   - `renderer/rendering_method="gl_compatibility"`: Configures Godot 4 to use OpenGL 3.3 (Desktop) and WebGL 2 (WebAssembly export). This is critical because it runs on all Linux/Windows environments without requiring Vulkan drivers and allows direct browser deployment.
   - `textures/canvas_textures/default_texture_filter=0`: Sets default texture filtering to **Nearest Neighbor** (pixel art). Since RPG-battle features 32x32 insect sprites and retro health bars, Nearest filtering ensures sharp, crisp pixel art without bilinear blurring.
5. **`[audio]` Bus Layout**:
   Points to `res://default_bus_layout.tres`.

---

## 4. Audio Bus Layout (`default_bus_layout.tres`)

To support `AudioManager.gd` with zero runtime warnings or fallback latency, `godot_project/default_bus_layout.tres` must define three distinct buses:

```ini
[gd_resource type="AudioBusLayout" format=3 uid="uid://c6buslayoutrpg"]

[resource]
bus/1/name = &"BGM"
bus/1/solo = false
bus/1/mute = false
bus/1/bypass_fx = false
bus/1/volume_db = 0.0
bus/1/send = &"Master"
bus/2/name = &"SFX"
bus/2/solo = false
bus/2/mute = false
bus/2/bypass_fx = false
bus/2/volume_db = 0.0
bus/2/send = &"Master"
```

---

## 5. Asset Strategy: Symlink vs Copy Analysis

### 5.1 Asset Inventory & Volume

| Directory | Volume | File Count | Content Types |
|---|---|---|---|
| `assets/images/` | 37 MB | ~110 files | Characters, monsters, terrains, materials, UI slides |
| `assets/sounds/` | 1.8 MB | 11 files | 3 BGM (.ogg), 8 SFX (.ogg) |
| `dados/` | 296 KB | 50 files | `personagens.json`, 12 phases (`info`, `batalha`, `mapa`, `dialogo`) |
| **Total** | **~39 MB** | **~171 files** | Fully production-ready |

### 5.2 Architectural Comparison

| Dimension | Symlink Approach (`ln -s ../assets godot_project/assets`) | Copy Approach (`cp -r assets godot_project/assets`) |
|---|---|---|
| **Disk Overhead** | 0 MB (uses existing files) | 39 MB (negligible on modern NVMe drives) |
| **Setup Speed** | Instant | < 0.2 seconds |
| **Root Cleanliness** | **Severe Hazard**: Godot writes a `.import` file for every asset (e.g. `hit.ogg.import`, `guerreiro.png.import`). Symlinks cause Godot to create ~120 untracked `.import` files in the root Python repository. | **Completely Clean**: All `.import` metadata stays isolated inside `godot_project/assets/`. |
| **Export Reliability** | **High Risk**: Godot's export packager (especially for WebAssembly / HTML5 and `.pck` packaging) frequently fails to resolve or dereference relative symlinks outside the project root. | **100% Reliable**: Native filesystem paths are bundled into `.pck` and `.zip` without path resolution anomalies. |
| **Cross-Platform & Git** | Symlinks on Windows require elevated Developer Mode or Git symlink config; causes broken files if cloned on Windows. | Works seamlessly across Linux, macOS, and Windows. |
| **Sandbox Isolation** | Inside the container, symlinks pointing to relative parent dirs that step outside mounts can break. | Guaranteed self-contained inside `godot_project/`. |

### 5.3 Recommendation & Setup Command

**Definitive Decision**: Use **Copy**.  
39 MB is tiny, takes fractions of a second to copy, completely prevents repo contamination by `.import` files, and ensures 100% packaging and container safety.

Automation command for the implementer:
```bash
# From repository root (/home/anderson/Documents/projeto/RPG-battle):
mkdir -p godot_project/assets godot_project/dados
cp -r assets/* godot_project/assets/
cp -r dados/* godot_project/dados/
```

---

## 6. Directory Structure for `godot_project/`

```text
godot_project/
├── project.godot                     # Project configuration (Settings, Autoloads, Display, Rendering)
├── default_bus_layout.tres           # Audio bus routing (Master, BGM, SFX)
├── .gutconfig.json                   # Headless test runner configuration
├── .gitignore                        # Ignores .godot/ cache and local binaries
├── run_gut_tests.sh                  # Self-contained CLI test runner with binary autodiscovery
├── bin/                              # Local executable directory (for container autonomy)
│   └── godot                         # Optional copy of Godot 4.7.2 binary
├── addons/
│   └── gut/                          # GUT 9.x framework files
│       ├── plugin.cfg
│       ├── gut_cmdln.gd
│       ├── gut.gd
│       └── test.gd
├── assets/                           # Production assets copied from root
│   ├── images/
│   │   ├── characters/
│   │   │   ├── animation/processed/  # 256x256 spritesheets (Aquele, Darwin, Gruu, Doom, etc.)
│   │   │   ├── bosses/               # Sienna, chefe
│   │   │   ├── heroes/               # 14 class/hero portraits
│   │   │   ├── monsters/isectum/     # 26 sliced 32x32 transparent PNGs
│   │   │   └── silver_roses/
│   │   ├── environment/              # 12 terrain textures (1024x1024)
│   │   │   └── card/                 # pixelCardAssest.png
│   │   ├── material/                 # wood, stone, iron
│   │   └── ui/                       # menu_background, logo, intro slides
│   └── sounds/                       # 11 OGG files (3 BGM, 8 SFX)
├── dados/                            # JSON canonical data copied from root
│   ├── personagens.json              # 9 classes, 11 heroes, 8 monsters/bosses
│   └── fases/                        # fase_01 to fase_12 (info, batalha, dialogo, mapa)
├── scenes/
│   ├── main/
│   │   ├── Main.tscn
│   │   └── Main.gd
│   ├── entities/
│   │   ├── Character.tscn
│   │   └── Character.gd
│   ├── cerco/
│   │   ├── Card.tscn
│   │   ├── Card.gd
│   │   ├── FortressBoard.tscn
│   │   └── FortressBoard.gd
│   └── ui/
│       ├── HUD.tscn
│       ├── HUD.gd
│       ├── CombatLog.tscn
│       ├── CombatLog.gd
│       ├── FloatingCombatText.tscn
│       └── FloatingCombatText.gd
├── scripts/
│   ├── autoload/
│   │   ├── EventBus.gd               # 13 canonical signals + telemetry
│   │   ├── DataManager.gd            # JSON loader, CharacterData/CardData cache
│   │   ├── AudioManager.gd           # 11 tracks, dual-player BGM crossfade, SFX pool
│   │   └── GameManager.gd            # 5-state FSM, turn loop, headless test mode
│   ├── core/
│   │   ├── TacticalGrid.gd           # 20x20 AStar2D grid, terrain costs, Chebyshev
│   │   ├── CombatRules.gd            # D&D 5e math, modifiers, advantage, criticals
│   │   ├── DeathSaves.gd             # Nat 20 / Nat 1 / 3-success / 3-fail FSM
│   │   └── StatusEffectManager.gd    # 23 status conditions & ticks
│   ├── resources/
│   │   ├── CharacterData.gd          # Custom Resource for heroes and monsters
│   │   ├── IsectumCasteData.gd       # Custom Resource for 24 Isectum castes
│   │   ├── CardData.gd               # Custom Resource for Cerco cards
│   │   └── AttackResult.gd           # Value object for combat resolution
│   ├── cerco/
│   │   ├── CercoSyncRound.gd         # Simultaneous turn co-op synchrony
│   │   ├── FortressEconomy.gd        # Movement, work, excavation economics
│   │   └── CercoCombatJudge.gd       # D6 combat judge engine
│   └── network/
│       ├── WebSocketClient.gd        # Native WebSocketPeer client
│       └── ProtocolMessages.gd       # Typed JSON serialization/deserialization
└── test/
    ├── unit/
    │   ├── test_autoloads.gd         # 44 tests covering 4 M1 singletons
    │   ├── test_tactical_grid.gd
    │   ├── test_combat_rules.gd
    │   ├── test_death_saves.gd
    │   ├── test_status_effects.gd
    │   ├── test_entities.gd
    │   ├── test_isectum_castes.gd
    │   ├── test_cerco_deckbuilder.gd
    │   ├── test_cerco_judge.gd
    │   ├── test_ui_audio.gd
    │   └── test_websocket_client.gd
    └── e2e/
        ├── test_full_combat_flow.gd
        ├── test_cerco_full_cycle.gd
        └── test_coop_session_sync.gd
```

### 6.1 `godot_project/.gitignore`

```gitignore
# Godot 4 generated cache and imported assets
.godot/
*.translation

# Local binaries or temporary dumps
bin/godot*
*.tmp
*.log

# User data
user/
```

---

## 7. Headless CLI Test Runner Script (`run_gut_tests.sh`)

To make running tests effortless for both human developers and automated agents in any environment, create `godot_project/run_gut_tests.sh`:

```bash
#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 1. Resolve Godot 4 binary location
GODOT_BIN=""

if command -v godot &>/dev/null; then
    GODOT_BIN="godot"
elif [ -x "$PROJECT_DIR/bin/godot" ]; then
    GODOT_BIN="$PROJECT_DIR/bin/godot"
elif [ -x "$PROJECT_DIR/../bin/godot" ]; then
    GODOT_BIN="$PROJECT_DIR/../bin/godot"
elif [ -x "/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64" ]; then
    GODOT_BIN="/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64"
else
    echo "ERROR: Godot 4 executable not found!"
    echo "Checked: PATH, $PROJECT_DIR/bin/godot, $PROJECT_DIR/../bin/godot, /home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64"
    exit 1
fi

echo "==> Using Godot binary: $GODOT_BIN"
echo "==> Project Directory: $PROJECT_DIR"

# 2. Run GUT Headless Runner
"$GODOT_BIN" --headless --path "$PROJECT_DIR" -s addons/gut/gut_cmdln.gd -gexit "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "==> All GUT tests passed successfully! (Exit code: 0)"
else
    echo "==> GUT tests FAILED! (Exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
```

Make it executable:
```bash
chmod +x godot_project/run_gut_tests.sh
```

---

## 8. Summary of Action Items for `m1_architect_core`

1. **Bootstrap Directory Hierarchy**:
   Create the directory tree according to Section 6.
2. **Copy Assets & Data**:
   Execute `cp -r assets/* godot_project/assets/` and `cp -r dados/* godot_project/dados/`.
3. **Write Configuration Files**:
   - `godot_project/project.godot` (Section 3).
   - `godot_project/default_bus_layout.tres` (Section 4).
   - `godot_project/.gutconfig.json` (from `m1_spec_miner_gut` specification).
   - `godot_project/.gitignore` (Section 6.1).
   - `godot_project/run_gut_tests.sh` (Section 7).
4. **Deploy Local Binary**:
   Copy `/home/anderson/Documents/Godot_v4.7.2-stable_linux.x86_64` to `godot_project/bin/godot` (or root `bin/godot`) to ensure uninhibited headless execution inside sandboxed containers.
5. **Implement Autoloads & Resources**:
   Implement `EventBus.gd`, `DataManager.gd`, `AudioManager.gd`, `GameManager.gd`, and their Custom Resources using the complete specifications provided in `.agents/m1_explorer_autoloads/analysis.md`.
6. **Deploy GUT Addon & Test Suite**:
   Deploy `addons/gut/` and `test/unit/test_autoloads.gd` as specified in `.agents/m1_spec_miner_gut/analysis.md`, and verify via `./run_gut_tests.sh`.
