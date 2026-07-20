# BHH - Black Hole Energy Harvester

A real-time 3D simulation of a black hole energy harvesting system built in pure Python. The system depicts a massive spinning sphere that orbits a black hole in a highly eccentric ellipse, harvesting gravitational tidal energy into rotational kinetic energy, then transferring it to a space station via magnetic inductive coupling.

## Quick Start

```bash
pip install numpy pygame
python BHH.py
```

## How It Works

1. A sphere orbits a black hole in a highly eccentric ellipse (e~0.997 for Gaia BH1)
2. At periastron (EP), a graphene composite string unreels into the tidal gravity gradient
3. The string's tension drives a pull-to-rotation gear system, spinning the sphere to ~223 RPM
4. The sphere stores ~1 PWh (3.46e18 J) of rotational kinetic energy
5. The sphere coasts to apastron (AP) where a space station harvests the spin energy
6. Magnetic inductive coupling (Halbach array + superconducting coils) extracts the energy
7. A gravity laser corrects orbital drift caused by the string tension
8. The cycle repeats every orbital period (~3 years for Gaia BH1)

## Preset Systems

- **Gaia BH1** - 9.62 M_sun stellar BH at 1,560 ly (reference design)
- **Cygnus X-1** - 21.8 M_sun stellar BH at 7,200 ly
- **Sagittarius A*** - 4.15M M_sun supermassive BH at galactic center
- **Primordial BH** - 5e11 kg primordial BH (miniature, fast-depleting)
- **M87*** - 6.5B M_sun ultramassive BH in Virgo A

## Controls

| Key | Action |
|---|---|
| TAB | Cycle modes: OVERVIEW -> SIMULATE -> DEPLETION -> SYSTEMS -> CUSTOM |
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

### OVERVIEW
Static 3D view of the complete system: black hole (with accretion disk, jets, lensing), orbit path, sphere, string, station, and gravity laser. All parts labeled with physical parameters. Orbit is to scale; BH/sphere/station are visually enlarged for visibility.

### SIMULATE
Animated orbital cycle showing all 4 phases (charging, outbound, harvesting, inbound) with live HUD displaying RPM, energy, orbital position, phase, and power flow. Phase timing is Kepler-derived from orbital mechanics.

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
- Tidal force on string kept below max tension with safety margin

### Energy Harvesting
- Spin energy: `E = 0.5 * I * omega^2` where `I = 0.4 * m * R^2`
- Harvest power = spin energy / harvest window (Kepler-derived)
- Harvest window = fraction of orbital period near AP (~28% for high eccentricity)
- 95% energy capture efficiency

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
- Roche limit clearance
- Centrifugal stress below material limit
- Energy/power consistency (power * time = energy)

Run the verification script:
```bash
python audit_verify.py
```

## Files

| File | Description |
|---|---|
| `BHH.py` | Main simulation (single-file, ~4400 lines) |
| `Goal.md` | Original design specification and conversation history |
| `OverView.md` | Detailed system overview with parameters and physics |
| `audit.py` | Initial mathematical audit script |
| `audit2.py` | Focused physics audit (tidal forces, GR, phase timing) |
| `audit3.py` | Energy/power consistency audit |
| `audit_verify.py` | Final verification audit for all 5 preset systems |

## Dependencies

- Python 3.x
- numpy
- pygame

## Architecture

BHH.py is a standalone monolith built on a pure-Python software 3D renderer (no OpenGL). It implements:
- Custom 3D mesh primitives (spheres, cylinders, cones, tori)
- Software rasterizer with face culling and depth sorting
- Camera system with orbit/pan/zoom
- Particle system for energy flow effects
- HUD with phase bar, telemetry, and info panels
- Multiple visualization modes with smooth transitions
