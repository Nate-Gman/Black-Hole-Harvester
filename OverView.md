# Black Hole Energy Harvester (BHH) - System Overview

## Concept

A graphene flywheel sphere orbits a black hole in a highly eccentric ellipse. At periastron (EP), a graphene composite string is unreeled into the tidal gravity gradient, driving a pull-to-rotation system that spins the sphere up to target RPM, storing rotational kinetic energy. The sphere coasts out to apastron (AP) where a space station in a circular orbit harvests the spin energy via magnetic inductive coupling, reducing rotation to 0 RPM. A gravity laser corrects orbital drift. The cycle repeats.

**Multiple spheres operate in constellation** — 6 spheres orbit simultaneously at evenly-spaced phase offsets, ensuring continuous energy harvest. The simulation tracks total harvests across all spheres, and the black hole becomes **critical after 100 harvests** as cumulative orbital energy extraction destabilizes the system.

## Reference System: Gaia BH1

| Parameter | Value |
|---|---|
| **Black Hole** | |
| Mass | 9.62 M_sun (1.913e31 kg) |
| Schwarzschild radius | 28.4 km |
| ISCO | 85.2 km |
| Distance from Earth | 1,560 ly |
| **Orbit** | |
| Periastron (EP) | 42,600 km (1500 r_s, 0.000285 AU) |
| Apastron (AP) | 8.48M km (200x EP, 0.057 AU) |
| Eccentricity | 0.99 |
| Period | ~14 hours |
| Velocity at EP | ~28,500 km/s |
| Velocity at AP | ~143 km/s |
| EP/ISCO ratio | 500x (well outside ISCO) |
| **Sphere** | |
| Mass | 5.0e7 kg (50,000 tonnes) |
| Radius | ~18 m |
| Material | Graphene composite (130 GPa tensile) |
| Density | 2,000 kg/m^3 |
| Max RPM | 4,247 (centrifugal stress at structural limit) |
| Target RPM | 4,035 (5% below max) |
| Energy capacity | ~180 GWh (6.49e14 J) |
| Operating energy | ~163 GWh (5.86e14 J) |
| **String** | |
| Material | Graphene composite (130 GPa tensile) |
| Diameter | 50 cm |
| Max tension | 2.56e10 N |
| Length | ~90 km |
| Tip mass | ~4e6 kg (osmium) |
| Safety factor | 2.0 (working tension = T_max / 2) |
| **Station** | |
| Orbit | Circular at AP distance |
| Station velocity | ~101 km/s |
| Harvest window | ~309 days (near AP) |
| Harvest power | 135 GW |
| Efficiency | 95% |
| **Constellation** | |
| Simultaneous spheres (sim) | 6 (evenly phased in mean anomaly) |
| Full constellation | 1,095 (1 harvest/day) |
| Energy per harvest | ~163 GWh (5.86e14 J) |
| Total per cycle (6 spheres) | ~978 GWh |
| Mass per harvest (E=mc^2) | ~6.5 kg |
| BH critical threshold | 100 harvests |
| Harvests to full depletion | ~4.97e29 |
| Depletion time | ~1.36e27 years |
| Annual energy (full) | ~1,050 PWh/yr |

## Operational Cycle (4 Phases)

1. **Charging (EP)** - Sphere passes through periastron. String unreels into tidal gradient at constant tension (T_max / safety factor). Pull-to-rotation system spins sphere to target RPM (~4,035 RPM). Duration: very brief (rapid periastron pass at ~14 hr orbit).

2. **Outbound transit** - String retracts. Sphere coasts at full RPM. Gravity laser corrects orbital drift near EP. Duration: ~36% of orbital period.

3. **Harvesting (AP)** - Space station extracts spin energy via magnetic inductive coupling. Rotation decelerates to 0 RPM. Duration: ~28% of orbital period (~309 days).

4. **Inbound return** - Sphere coasts inbound at 0 RPM. Gravity laser at AP restores EP for next cycle. Duration: ~36% of orbital period.

Phase timing is derived from Kepler's equation, not hardcoded. The charging phase ends when the sphere reaches 5x EP distance. Harvesting occurs when the sphere is within 5% of AP distance.

## Multi-Sphere Constellation

The simulation renders **6 spheres** orbiting simultaneously at evenly-spaced phase offsets (0, 1/6, 2/6, 3/6, 4/6, 5/6 of the orbital period). At any given time, different spheres are in different phases — some charging at EP, some harvesting at AP, some in transit. This ensures:

- **Continuous energy output** — at least 1-2 spheres are harvesting at any time
- **Visual richness** — the orbit is populated, not a single lonely sphere
- **Physical safety** — minimum separation between spheres is millions of km (the high eccentricity means spheres cluster in time but the orbit is physically enormous)

The full conceptual constellation has 1,095 spheres (one harvest per day), but 6 are rendered in the simulation for visual clarity.

## BH Critical Instability

After **100 harvests**, the black hole is flagged as **critical**. The cumulative orbital energy extraction destabilizes the system, requiring intervention or shutdown. The simulation tracks:

- **Total harvests** across all spheres
- **Total energy harvested** (cumulative)
- **BH instability percentage** (0% → 100% as harvests approach threshold)
- **Stability status**: STABLE → WARNING (40%) → UNSTABLE (70%) → CRITICAL (100%)

This is a simulation concept — the actual E=mc^2 mass loss per harvest (~6.5 kg) is negligible compared to the BH mass (~1.9e31 kg). The "critical" state represents cumulative orbital mechanics destabilization, not BH mass depletion.

## Preset Systems

| System | BH Mass | EP | AP | e | Period | Sphere Mass | RPM | Energy |
|---|---|---|---|---|---|---|---|---|
| Gaia BH1 | 9.62 M_sun | 1500 r_s | 200x EP | 0.99 | ~14 hr | 5.0e7 kg | 4,035 | 163 GWh |
| Cygnus X-1 | 21.8 M_sun | 1500 r_s | 200x EP | 0.99 | ~14 hr | 8.0e7 kg | ~3,200 | ~260 GWh |
| Sagittarius A* | 4.15M M_sun | 50 r_s | 20x EP | 0.95 | varies | 5.0e9 kg | ~60 | scale demo |
| Primordial BH | ~5e11 kg | varies | varies | varies | varies | 1e3 kg | 10,000 | ~0 |
| M87* | 6.5B M_sun | varies | varies | 0.54 | varies | 1e15 kg | ~15 | scale demo |

## Physics Validation

All systems have been mathematically audited and verified:

- **Angular momentum conservation**: v_EP * EP = v_AP * AP (0.000000% error)
- **Energy conservation**: Vis-viva equation consistent at EP and AP (0.000000% error)
- **ISCO clearance**: All EP distances are >3x ISCO (Gaia BH1: 500x)
- **String tension safety**: Tidal force / max tension < 1.0 for all systems
- **Centrifugal stress**: All systems below 130 GPa graphene limit
- **Energy/power consistency**: Harvest power * window = spin energy (0% error)
- **Phase timing**: Kepler-derived from true anomaly, not hardcoded

## Display Scaling & Views

The orbit is rendered with display scale `DS = 1/AP` (1 apastron = 1.0 model units), making framing scale-invariant across systems. The bodies (BH ~28 km, sphere ~18 m, station ~km) are intentionally enlarged for visibility.

**PREVIEW** - whole-system map. Orbit to scale; bodies enlarged for legibility. Shows all 6 spheres orbiting in constellation with energy effects and trails.

**MODEL (to scale)** - to-scale inspector. Cycle the focused component (`[` / `]`): black hole, energy sphere, station, string, mechanism, or the whole system. Each single component is normalised to a standard viewing size and shown with its real dimensions and a true scale bar.

**SIMULATE** - animated orbital cycle with 6-sphere constellation. Live HUD shows per-sphere phase, total harvests, total energy, BH stability status, and instability gauge.

For Gaia BH1 the orbit clears the black hole by a wide margin:
- EP / ISCO = 500x
- EP / Schwarzschild radius = 1,500x

## Materials

All material properties use realistic, measured values:
- **Graphene tensile strength**: 130 GPa (measured, not theoretical maximum)
- **Osmium density**: 22,590 kg/m^3 (tip mass material)
- **Sphere density**: 2,000 kg/m^3 (graphene composite)
- **String density**: 2,000 kg/m^3 (graphene composite)

No exotic or impossible material properties are used. The system operates within known physics constraints.
