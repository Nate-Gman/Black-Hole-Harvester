# BHH - Black Hole Energy Harvester

A real-time 3D simulation of a black hole energy harvesting system built in pure Python. A constellation of spinning graphene flywheel spheres orbits a black hole in highly eccentric ellipses, harvesting gravitational tidal energy into rotational kinetic energy, then transferring it to a space station via magnetic inductive coupling. The simulation tracks total energy harvested across all spheres and monitors black hole stability as harvests accumulate toward a critical threshold.

## Quick Start

```bash
pip install numpy pygame
python BHH.py
```

## How It Works

1. **6 spheres** orbit the black hole simultaneously at evenly-spaced phase offsets
2. At periastron (EP), a graphene composite string unreels into the tidal gravity gradient
3. The string's tension drives a pull-to-rotation gear system, spinning each sphere to ~4,035 RPM
4. Each sphere stores ~163 GWh (5.86e14 J) of rotational kinetic energy
5. The sphere coasts to apastron (AP) where a space station harvests the spin energy
6. Magnetic inductive coupling (Halbach array + superconducting coils) extracts the energy
7. A gravity laser corrects orbital drift caused by the string tension
8. The cycle repeats every orbital period (~14 hours for Gaia BH1)
9. After **100 total harvests**, the BH goes **critical** — cumulative orbital energy extraction destabilizes the system

## Multi-Sphere Constellation

The simulation renders 6 spheres orbiting in unison at different phase offsets (0, 1/6, 2/6, 3/6, 4/6, 5/6 of the orbital period). At any given time, different spheres are in different phases — some charging at EP, some harvesting at AP, some in transit. This ensures continuous energy output and visual richness.

The full conceptual constellation has 1,095 spheres (one harvest per day), but 6 are rendered for visual clarity. The simulation tracks:
- **Total harvests** across all spheres (counts toward BH critical threshold)
- **Total energy harvested** (cumulative, all spheres)
- **BH instability** (0% → 100% as harvests approach 100)
- **Stability status**: STABLE → WARNING → UNSTABLE → CRITICAL

## Preset Systems

- **Gaia BH1** - 9.62 M_sun stellar BH at 1,560 ly (reference design, ~14 hr orbit)
- **Cygnus X-1** - 21.8 M_sun stellar BH at 7,200 ly
- **Sagittarius A*** - 4.15M M_sun supermassive BH at galactic center (scale demo)
- **Primordial BH** - 5e11 kg primordial BH (miniature, fast-depleting)
- **M87*** - 6.5B M_sun ultramassive BH in Virgo A (scale demo)

## Controls

| Key | Action |
|---|---|
| TAB | Cycle modes: PREVIEW -> MODEL -> SIMULATE -> DEPLETION -> SYSTEMS -> CUSTOM |
| [ / ] | MODEL mode: cycle focused component (BH / sphere / station / string / system) |
| 1-5 | Quick-select preset system |
| S | Systems selection screen |
| C | Custom system builder |
| Mouse L-drag | Orbit camera |
| Mouse R-drag | Pan camera |
| Mouse wheel | Zoom |
| R | Reset camera |
| L | Toggle labels |
| E | Exploded view |
| X | Section cut |
| P | Pause/resume |
| SPACE | Advance to next phase / reset depletion |
| +/- | Speed up / slow down |
| I | System information panel |
| H | Help panel |
| ESC | Close panel / quit |

## Modes

### PREVIEW
Whole-system map: black hole (with accretion disk, jets, lensing), orbit path, 6-sphere constellation, strings, station, and gravity laser, all animated. Orbit is to scale (1 AP = 1 unit); bodies are enlarged for legibility. The black hole is capped so the eccentric orbit clearly clears it.

### MODEL (to scale)
To-scale digital-twin inspector. Press `[` / `]` to cycle the focused component — black hole, energy sphere, station, string, mechanism, or the whole system. Each component is framed at a comfortable size and shown with its real dimensions and a true scale bar.

### SIMULATE
Animated orbital cycle with 6-sphere constellation. Live HUD displays per-sphere phase status, total harvests, total energy harvested, BH stability status, instability gauge, RPM, energy, and power flow. Phase bar shows all sphere positions. BH goes critical after 100 harvests.

### DEPLETION
Visualizes the black hole's energy depletion over astronomical timescales, including Hawking radiation, ergosphere growth, and final explosion with Planck remnant.

### SYSTEMS
Selection screen for the 5 preset systems with comparison data.

### CUSTOM
Build your own system by specifying black hole mass, orbit parameters, sphere properties, and string dimensions.

## Physics

### Orbital Mechanics
- Vis-viva equation for velocities: `v = sqrt(GM(2/r - 1/a))`
- Kepler's Third Law for period: `T = 2*pi*sqrt(a^3/GM)`
- Newton-Raphson solver for Kepler's equation (mean -> eccentric -> true anomaly)
- Phase bounds computed from true anomaly at 5x EP and 95% AP distances

### Black Hole Physics
- Schwarzschild radius: `Rs = 2GM/c^2`
- ISCO at 3*Rs
- Photon sphere at 1.5*Rs
- Hawking radiation power and temperature

### Materials (Realistic Values)
- **Graphene tensile strength**: 130 GPa (measured)
- **Osmium density**: 22,590 kg/m^3 (tip mass)
- **Sphere/string density**: 2,000 kg/m^3 (graphene composite)
- Centrifugal stress kept below 130 GPa for all systems
- Tidal force on string kept below max tension with safety factor of 2.0

### Energy Harvesting
- Spin energy: `E = 0.5 * I * omega^2` where `I = 0.4 * m * R^2`
- Harvest power = spin energy / harvest window (Kepler-derived)
- Harvest window = fraction of orbital period near AP (~28% for high eccentricity)
- 95% energy capture efficiency
- ~163 GWh per harvest per sphere

### BH Critical Instability
- After 100 total harvests across all spheres, BH is flagged critical
- Instability rises linearly: 0% at 0 harvests → 100% at 100 harvests
- Status thresholds: STABLE (<40%) → WARNING (40%) → UNSTABLE (70%) → CRITICAL (100%)
- The E=mc^2 mass loss per harvest (~6.5 kg) is negligible vs BH mass (~1.9e31 kg)
- "Critical" represents cumulative orbital mechanics destabilization, not mass depletion

### Station
- Circular orbit at AP distance (not fixed position)
- Relative flyby velocity = |v_circular - v_elliptical at AP|
- Gyroscopic flywheel for station-keeping
- Helium-3 fusion reactor for gravity laser power

## Mathematical Validation

All 5 preset systems pass verification:
- Angular momentum conservation (0% error)
- Energy conservation (0% error)
- ISCO clearance (all EP > 3x ISCO)
- String tension safety (tidal/tension < 1.0)
- Centrifugal stress below material limit
- Energy/power consistency (power * time = energy)

Run the verification script:
```bash
python audit_verify.py
```

## Files

| File | Description |
|---|---|
| `BHH.py` | Main simulation (single-file, ~5100 lines) |
| `Goal.md` | Original design specification and conversation history |
| `OverView.md` | Detailed system overview with parameters and physics |
| `audit_verify.py` | Final verification audit for all 5 preset systems |
| `optimal_harvesters.py` | Calculates optimal number of spheres for the orbit |
| `test_multi_sphere.py` | Headless test of multi-sphere SimState |

## Dependencies

- Python 3.x
- numpy
- pygame

## Architecture

BHH.py is a standalone monolith built on a pure-Python software 3D renderer (no OpenGL). It implements:
- Custom 3D mesh primitives (spheres, cylinders, cones, tori)
- Software rasterizer with face culling and depth sorting
- Camera system with orbit/pan/zoom
- Multi-sphere constellation with per-sphere phase tracking
- Particle system for energy flow effects
- HUD with phase bar, constellation status, BH instability gauge, and info panels
- Multiple visualization modes with smooth transitions
