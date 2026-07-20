#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 BHH.py  --  Black Hole Energy Harvester :: Digital Twin & Simulation
================================================================================

A 100% standalone monolith that builds, animates and *drives* the complete
Black Hole Energy Harvester (BHH) system in real time, mechanically, to scale,
in a single Python file — built on the same pure-Python software renderer
architecture as GmansRunV1.17.py, SE.py, and flysuit.py.

THE SYSTEM (from goal.md):
  A massive spinning sphere orbits Gaia BH1 in a highly eccentric ellipse.
  At periastron (EP), a string is unreeled into the tidal gravity gradient,
  driving a pull-to-rotation system that spins the sphere up to ~228 RPM,
  storing 1 PWh (3.6e18 J) of rotational kinetic energy. The sphere coasts
  out to apastron (AP) where a space station harvests the spin via magnetic
  inductive coupling, reducing rotation to 0 RPM. A gravity laser corrects
  orbital drift. The cycle repeats every 3 years.

  BLACK HOLE      Gaia BH1, ~9.62 solar masses, Schwarzschild metric
  SPHERE          2.77e11 kg, R~321 m, graphene composite
                  (rho~2000 kg/m3, sigma~130 GPa), stores 1 PWh at ~228 RPM
  ORBIT           EP=0.014 AU, AP=8.83 AU, e~0.997, T=3 yr
  STRING          Graphene composite, 1.5 m dia, tip mass 3.50e10 kg
  PULL-TO-ROT     4-stage planetary gears (625:1), constant-tension clutch,
                  electromagnetic disengagement, rotary swivel, ratchet freewheel
  STATION         Circular orbit at AP, gyroscopic flywheel station-keeping,
                  superconducting coil array for inductive harvesting
  GRAVITY LASER   Orbital correction near EP and at AP
  HARVESTING      Halbach array (NdFeB, ~2 T) -> inductive coupling -> 135 GW
  CONSTELLATION   1095 spheres, one harvest per day

Two modes (toggle with TAB):
  1. OVERVIEW   Orbit the whole system: black hole, orbit path, sphere,
                string, station, gravity laser beams. Orbit is to scale;
                BH/sphere/station are visually enlarged for visibility.
  2. SIMULATE   Animate one full orbital cycle: charging at EP, outbound
                transit, harvesting at AP, inbound return. Live HUD shows
                RPM, energy, orbital position, phase, power flow.

Dependencies:  numpy, pygame
Run:           python BHH.py

Controls:  TAB mode switch ; mouse orbit/zoom/pan ; R reset ; L labels
           I info ; H help ; P pause ; SPACE advance phase ; ESC quit
================================================================================
"""

import math
import os
import sys
import warnings
from operator import itemgetter

warnings.filterwarnings("ignore")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np

try:
    import pygame
except Exception:
    pygame = None

try:
    import pygame.gfxdraw as gfx
except Exception:
    gfx = None


# =============================================================================
# SECTION 1 -- PHYSICAL CONSTANTS & ENGINEERING SPECIFICATION
# =============================================================================

G       = 6.67430e-11       # gravitational constant (m^3 kg^-1 s^-2)
C       = 2.99792458e8      # speed of light (m/s)
M_SUN   = 1.98892e30        # solar mass (kg)
AU_M    = 1.495978707e11    # 1 AU in metres
LY_M    = 9.4607e15         # light-year in metres
SIGMA_SB = 5.670374e-8      # Stefan-Boltzmann constant
PI      = math.pi

# -- Black hole: Gaia BH1 --
BH_MASS_KG     = 9.62 * M_SUN              # ~1.913e31 kg
BH_RS          = 2.0 * G * BH_MASS_KG / C**2   # Schwarzschild radius (~28.4 km)
BH_RPH         = 1.5 * BH_RS               # photon sphere
BH_RISCO       = 3.0 * BH_RS               # innermost stable circular orbit
BH_DIST_LY     = 1560.0                    # distance from Earth

# -- Sphere: graphene composite --
SPHERE_MASS_KG    = 2.77e11
SPHERE_DENSITY    = 2000.0                 # kg/m^3
SPHERE_RADIUS_M   = (3.0 * SPHERE_MASS_KG / (4.0 * PI * SPHERE_DENSITY)) ** (1.0/3.0)  # ~321 m
SPHERE_TENSILE_PA = 1.30e11                # 130 GPa (graphene, measured tensile strength)
SPHERE_RPM_MAX    = 235.0                  # max RPM before structural failure
SPHERE_RPM_TARGET = 223.0                  # 5% below max
SPHERE_OMEGA_MAX  = SPHERE_RPM_MAX * 2.0 * PI / 60.0
SPHERE_OMEGA_TGT  = SPHERE_RPM_TARGET * 2.0 * PI / 60.0
SPHERE_I          = 0.4 * SPHERE_MASS_KG * SPHERE_RADIUS_M**2   # moment of inertia (solid sphere)
SPHERE_E_PWH      = 0.5 * SPHERE_I * SPHERE_OMEGA_MAX**2   # energy at max RPM (~1 PWh)

# -- Orbit --
ORBIT_EP_AU    = 0.014                     # periastron (close approach for tidal gradient)
ORBIT_AP_AU    = 8.83                      # apastron (station position, safe distance)
ORBIT_EP_M     = ORBIT_EP_AU * AU_M
ORBIT_AP_M     = ORBIT_AP_AU * AU_M
ORBIT_A_M      = 0.5 * (ORBIT_EP_M + ORBIT_AP_M)     # semi-major axis
ORBIT_E        = (ORBIT_AP_M - ORBIT_EP_M) / (ORBIT_AP_M + ORBIT_EP_M)  # eccentricity
ORBIT_B_M      = ORBIT_A_M * math.sqrt(1.0 - ORBIT_E**2)   # semi-minor axis
ORBIT_PERIOD_S = 2.0 * PI * math.sqrt(ORBIT_A_M**3 / (G * BH_MASS_KG))
ORBIT_PERIOD_YR = ORBIT_PERIOD_S / (365.25 * 86400.0)
ORBIT_V_EP     = math.sqrt(G * BH_MASS_KG * (2.0/ORBIT_EP_M - 1.0/ORBIT_A_M))
ORBIT_V_AP     = math.sqrt(G * BH_MASS_KG * (2.0/ORBIT_AP_M - 1.0/ORBIT_A_M))

# -- String: carbon graphene hybrid --
STRING_DIAM_M    = 1.50                    # 1.5 m cable (graphene-reinforced composite)
STRING_R_M       = STRING_DIAM_M / 2.0
STRING_TENSILE   = 1.30e11                 # 130 GPa (graphene, measured tensile strength)
STRING_DENSITY   = 2000.0                  # kg/m^3
STRING_T_MAX     = STRING_TENSILE * PI * STRING_R_M**2   # max tension ~2.30e11 N
STRING_LENGTH_M  = SPHERE_E_PWH / STRING_T_MAX           # ~1.57e7 m with constant tension
STRING_LENGTH_MI = STRING_LENGTH_M / 1609.344
STRING_TIP_MASS  = 3.50e10                 # tip mass (kg, reduced for tidal force safety)
STRING_TIP_R_M   = (3.0 * STRING_TIP_MASS / (4.0 * PI * 22590.0))**(1.0/3.0)  # osmium density

# -- Pull-to-rotation system --
GEAR_STAGES     = 4                        # 4 stages (reduced from 7 to stiffen system)
GEAR_RATIO_PER  = 5.0
GEAR_RATIO_TOTAL = GEAR_RATIO_PER ** GEAR_STAGES   # 625:1
GEAR_EFFICIENCY = 0.93                     # ~93% (goal.md spec)
DRUM_RADIUS_M   = SPHERE_RADIUS_M * 0.3    # internal drum
CLUTCH_TENSION  = STRING_T_MAX             # constant-tension clutch at T_max

# -- Space station --
STATION_MASS_KG    = 1.0e9
STATION_GYRO_MASS  = 1.0e6
STATION_GYRO_R     = 10.0
STATION_GYRO_RPM   = 10000.0
STATION_COIL_LEN   = 50.0e3                # 50 km coil array
STATION_B_FIELD    = 2.0                   # Tesla (Halbach array)
STATION_POWER_GW   = 135.0                  # GW harvest power during AP flyby (E_spin / harvest_window)
STATION_HARVEST_S  = 2.67e7                 # harvest window duration (~309 days near AP)
STATION_EFFICIENCY = 0.95                   # 95% energy capture efficiency

# -- Energy harvesting --
HARVEST_ENERGY_J  = SPHERE_E_PWH * STATION_EFFICIENCY   # 3.42e18 J per harvest
HARVEST_POWER_W   = STATION_POWER_GW * 1e9              # 135 GW harvest rate during AP flyby

# -- Orbital correction --
EP_DRIFT_KM       = 0.0001                 # EP reduction per cycle (km, goal.md spec)
LASER_POWER_GW    = 10.0                   # gravity laser power (goal.md spec)
LASER_FORCE_N     = 1.0e4                  # correction force (goal.md spec)

# -- Safety systems (goal.md) --
SAFETY_MARGIN     = 0.20                   # 20% excess impact parameter for escape trajectory
SPHERE_RTG_W      = 100000.0               # RTG power on sphere (Pu-238, ~100 kW total)
SPHERE_DELTA_V    = 10.0                   # escape thruster delta-v reserve (m/s)
STATION_FUSION_TW = 10.0                   # station fusion reactor power (TW scale for laser)
LASER_EFFICIENCY  = 0.80                   # gravity laser efficiency (~80%)
GYRO_EFFICIENCY   = 0.85                   # gyro station-keeping efficiency (~85%)
HALBACH_FREQ_HZ   = SPHERE_RPM_TARGET / 60.0  # rotating field frequency (~3.8 Hz)

# -- Constellation --
N_SPHERES         = 1095
HARVEST_INTERVAL_D = 1                     # one per day
MASS_PER_HARVEST   = SPHERE_E_PWH / C**2   # E=mc^2 equivalent mass (40 kg)
HARVESTS_TO_DEPLETE = int(BH_MASS_KG / MASS_PER_HARVEST)
DEPLETE_YEARS      = HARVESTS_TO_DEPLETE / 365.25
HOMES_POWERED     = int(N_SPHERES * SPHERE_E_PWH / 3.6e10)  # annual energy / 10,000 kWh per home

# -- Derived energy values --
SPHERE_E_MAX      = 0.5 * SPHERE_I * SPHERE_OMEGA_MAX**2   # max energy at 240 RPM = 1 PWh
SPHERE_E_OPER     = 0.5 * SPHERE_I * SPHERE_OMEGA_TGT**2    # operating energy at 228 RPM ~0.90 PWh

# -- Display scaling --
DS = 1.0 / AU_M   # display scale: 1 AU = 1.0 model units

# -- Scene scale: all components sized relative to orbit for visibility --
# Computed from orbit extent so BH, sphere, station are always visible
ORBIT_MAX_DS = max(ORBIT_EP_M, ORBIT_AP_M) * DS   # largest orbit radius in display units
SCENE_R = max(ORBIT_MAX_DS, 0.1)                    # scene radius for scaling
BH_DISP_R = SCENE_R * 0.04                          # BH visible at 4% of orbit
SPHERE_DISP_R = SCENE_R * 0.015                    # sphere visible at 1.5% of orbit
STATION_DISP_S = SCENE_R * 0.025                   # station size at 2.5% of orbit
STRING_DISP_SCALE = SCENE_R * 0.08 / max(STRING_LENGTH_M * DS, 1e-12)  # string visible
CAMERA_HOME_DIST = SCENE_R * 1.5                    # camera distance to fit orbit

# -- Current system name (updated by _apply_system) --
CURRENT_SYSTEM_NAME = "Gaia BH1"


# =============================================================================
# SECTION 1b -- SYSTEM CONFIGURATIONS (multi-system support)
# =============================================================================

class SystemConfig:
    """Configuration for a BH harvesting system. Encapsulates all physical
    parameters so multiple systems at different scales can coexist."""

    def __init__(self, name, desc,
                 bh_mass_msun, bh_dist_ly,
                 orbit_ep_au, orbit_ap_au,
                 sphere_mass_kg, sphere_density,
                 sphere_rpm_max, sphere_rpm_target,
                 string_diam_m, string_tip_mass_kg,
                 n_spheres, station_mass_kg,
                 color_bh=(40, 0, 60), color_accent=(0, 200, 255)):
        self.name = name
        self.desc = desc
        self.bh_mass_msun = bh_mass_msun
        self.bh_dist_ly = bh_dist_ly
        self.orbit_ep_au = orbit_ep_au
        self.orbit_ap_au = orbit_ap_au
        self.sphere_mass_kg = sphere_mass_kg
        self.sphere_density = sphere_density
        self.sphere_rpm_max = sphere_rpm_max
        self.sphere_rpm_target = sphere_rpm_target
        self.string_diam_m = string_diam_m
        self.string_tip_mass_kg = string_tip_mass_kg
        self.n_spheres = n_spheres
        self.station_mass_kg = station_mass_kg
        self.color_bh = color_bh
        self.color_accent = color_accent

        # Derived values
        self.bh_mass_kg = bh_mass_msun * M_SUN
        self.bh_rs = 2.0 * G * self.bh_mass_kg / C**2
        self.bh_rph = 1.5 * self.bh_rs
        self.bh_risco = 3.0 * self.bh_rs
        self.orbit_ep_m = orbit_ep_au * AU_M
        self.orbit_ap_m = orbit_ap_au * AU_M
        self.orbit_a_m = 0.5 * (self.orbit_ep_m + self.orbit_ap_m)
        self.orbit_e = (self.orbit_ap_m - self.orbit_ep_m) / (self.orbit_ap_m + self.orbit_ep_m)
        self.orbit_b_m = self.orbit_a_m * math.sqrt(1.0 - self.orbit_e**2)
        self.orbit_period_s = 2.0 * PI * math.sqrt(self.orbit_a_m**3 / (G * self.bh_mass_kg))
        self.orbit_period_yr = self.orbit_period_s / (365.25 * 86400.0)
        self.orbit_v_ep = math.sqrt(G * self.bh_mass_kg * (2.0/self.orbit_ep_m - 1.0/self.orbit_a_m))
        self.orbit_v_ap = math.sqrt(G * self.bh_mass_kg * (2.0/self.orbit_ap_m - 1.0/self.orbit_a_m))

        self.sphere_radius_m = (3.0 * sphere_mass_kg / (4.0 * PI * sphere_density)) ** (1.0/3.0)
        self.sphere_omega_max = sphere_rpm_max * 2.0 * PI / 60.0
        self.sphere_omega_tgt = sphere_rpm_target * 2.0 * PI / 60.0
        self.sphere_i = 0.4 * sphere_mass_kg * self.sphere_radius_m**2
        self.sphere_e_max = 0.5 * self.sphere_i * self.sphere_omega_max**2
        self.sphere_e_oper = 0.5 * self.sphere_i * self.sphere_omega_tgt**2
        self.sphere_e_pwh = self.sphere_e_max  # energy at max RPM (sphere spins to max at EP)

        self.string_r_m = string_diam_m / 2.0
        self.string_t_max = 1.30e11 * PI * self.string_r_m**2
        self.string_length_m = self.sphere_e_pwh / self.string_t_max
        self.string_tip_r_m = (3.0 * string_tip_mass_kg / (4.0 * PI * 22590.0))**(1.0/3.0)

        self.mass_per_harvest = self.sphere_e_pwh / C**2
        self.harvests_to_deplete = int(self.bh_mass_kg / self.mass_per_harvest) if self.mass_per_harvest > 0 else 0
        self.deplete_years = self.harvests_to_deplete / 365.25 if self.harvests_to_deplete > 0 else 0

        self.ds = 1.0 / AU_M  # display scale

    def true_anomaly(self, t_frac):
        """True anomaly from time fraction for this system's orbit."""
        M = 2.0 * PI * t_frac
        E = M + self.orbit_e * math.sin(M)
        for _ in range(8):
            dE = (E - self.orbit_e * math.sin(E) - M) / (1.0 - self.orbit_e * math.cos(E))
            E -= dE
            if abs(dE) < 1e-10:
                break
        return 2.0 * math.atan2(math.sqrt(1.0+self.orbit_e) * math.sin(E/2.0),
                                math.sqrt(1.0-self.orbit_e) * math.cos(E/2.0))

    def orbital_position(self, t_frac):
        """Position (x, z, r) on orbit at time fraction."""
        nu = self.true_anomaly(t_frac)
        r = self.orbit_a_m * (1.0 - self.orbit_e**2) / (1.0 + self.orbit_e * math.cos(nu))
        x = r * math.cos(nu) * self.ds
        z = r * math.sin(nu) * self.ds
        return x, z, r

    def orbital_velocity(self, t_frac):
        nu = self.true_anomaly(t_frac)
        r = self.orbit_a_m * (1.0 - self.orbit_e**2) / (1.0 + self.orbit_e * math.cos(nu))
        return math.sqrt(G * self.bh_mass_kg * (2.0/r - 1.0/self.orbit_a_m))

    def gravity_at(self, r_m):
        return G * self.bh_mass_kg / r_m**2

    def hawking_temperature(self):
        return 6.169e-8 * M_SUN / self.bh_mass_kg

    def summary(self):
        return [
            f"Name: {self.name}",
            f"BH mass: {self.bh_mass_msun:.2f} M_sun ({self.bh_mass_kg:.3e} kg)",
            f"Schwarzschild R: {self.bh_rs/1000:.1f} km",
            f"Orbit EP: {self.orbit_ep_au:.2f} AU, AP: {self.orbit_ap_au:.2f} AU",
            f"Eccentricity: {self.orbit_e:.3f}",
            f"Period: {self.orbit_period_yr:.1f} yr",
            f"Sphere: {self.sphere_mass_kg:.2e} kg, R={self.sphere_radius_m:.0f} m",
            f"Sphere RPM: {self.sphere_rpm_target:.0f} (max {self.sphere_rpm_max:.0f})",
            f"Energy/harvest: {self.sphere_e_pwh:.2e} J ({self.sphere_e_pwh/3.6e18:.2f} PWh)",
            f"Spheres: {self.n_spheres}, Rate: 1/day",
            f"Depletion: {self.deplete_years:.2e} yr ({self.harvests_to_deplete:.2e} harvests)",
        ]


# -- Preset system configurations --
PRESET_SYSTEMS = [
    SystemConfig(
        "Gaia BH1", "Stellar-mass BH at 1560 ly - the reference design",
        bh_mass_msun=9.62, bh_dist_ly=1560,
        orbit_ep_au=0.014, orbit_ap_au=8.83,
        sphere_mass_kg=2.77e11, sphere_density=2000.0,
        sphere_rpm_max=235, sphere_rpm_target=223,
        string_diam_m=1.50, string_tip_mass_kg=3.50e10,
        n_spheres=1095, station_mass_kg=1e9,
        color_bh=(40, 0, 60), color_accent=(0, 200, 255),
    ),
    SystemConfig(
        "Cygnus X-1", "21.8 M_sun stellar BH at 7200 ly - high-energy system",
        bh_mass_msun=21.8, bh_dist_ly=7200,
        orbit_ep_au=0.022, orbit_ap_au=11.6,
        sphere_mass_kg=5.5e11, sphere_density=2000.0,
        sphere_rpm_max=180, sphere_rpm_target=165,
        string_diam_m=1.80, string_tip_mass_kg=7.0e10,
        n_spheres=1095, station_mass_kg=2e9,
        color_bh=(20, 10, 80), color_accent=(100, 200, 255),
    ),
    SystemConfig(
        "Sagittarius A*", "4.15M M_sun supermassive BH - galactic-scale harvesting",
        bh_mass_msun=4.15e6, bh_dist_ly=26000,
        orbit_ep_au=1.45, orbit_ap_au=1490.0,
        sphere_mass_kg=1e13, sphere_density=1500.0,
        sphere_rpm_max=60, sphere_rpm_target=54,
        string_diam_m=4.50, string_tip_mass_kg=2.0e11,
        n_spheres=3650, station_mass_kg=1e11,
        color_bh=(60, 20, 0), color_accent=(255, 180, 80),
    ),
    SystemConfig(
        "Primordial BH", "5e11 kg primordial BH - miniature, fast-depleting system",
        bh_mass_msun=2.5e-19, bh_dist_ly=0.001,
        orbit_ep_au=0.0001, orbit_ap_au=0.001,
        sphere_mass_kg=1e3, sphere_density=8000.0,
        sphere_rpm_max=10000, sphere_rpm_target=9500,
        string_diam_m=0.03, string_tip_mass_kg=0.05,
        n_spheres=100, station_mass_kg=1e3,
        color_bh=(80, 0, 40), color_accent=(255, 100, 200),
    ),
    SystemConfig(
        "M87*", "6.5B M_sun ultramassive BH - extreme scale",
        bh_mass_msun=6.5e9, bh_dist_ly=5.3e7,
        orbit_ep_au=3000, orbit_ap_au=10000,
        sphere_mass_kg=1e15, sphere_density=1500.0,
        sphere_rpm_max=15, sphere_rpm_target=14,
        string_diam_m=15.0, string_tip_mass_kg=5e12,
        n_spheres=10000, station_mass_kg=1e13,
        color_bh=(40, 40, 0), color_accent=(255, 255, 100),
    ),
]


def create_custom_config(bh_mass_msun, orbit_ep_au, orbit_ap_au,
                         sphere_mass_kg, sphere_rpm_target,
                         string_diam_m, n_spheres):
    """Create a custom SystemConfig from user parameters."""
    sphere_density = 2000.0
    sphere_radius = (3.0 * sphere_mass_kg / (4.0 * PI * sphere_density)) ** (1.0/3.0)
    sphere_i = 0.4 * sphere_mass_kg * sphere_radius**2
    omega_tgt = sphere_rpm_target * 2.0 * PI / 60.0
    e_oper = 0.5 * sphere_i * omega_tgt**2
    rpm_max = sphere_rpm_target * 1.05  # 5% margin
    string_tip_mass = sphere_mass_kg * 0.28
    station_mass = max(1e6, sphere_mass_kg * 1e-2)

    return SystemConfig(
        "Custom", "User-configured system",
        bh_mass_msun=bh_mass_msun, bh_dist_ly=1000,
        orbit_ep_au=orbit_ep_au, orbit_ap_au=orbit_ap_au,
        sphere_mass_kg=sphere_mass_kg, sphere_density=sphere_density,
        sphere_rpm_max=rpm_max, sphere_rpm_target=sphere_rpm_target,
        string_diam_m=string_diam_m, string_tip_mass_kg=string_tip_mass,
        n_spheres=n_spheres, station_mass_kg=station_mass,
        color_bh=(0, 60, 40), color_accent=(100, 255, 150),
    )


# =============================================================================
# SECTION 2 -- PHYSICS CALCULATIONS
# =============================================================================

def sphere_rotational_energy(rpm):
    """Rotational kinetic energy of the sphere at given RPM."""
    omega = rpm * 2.0 * PI / 60.0
    return 0.5 * SPHERE_I * omega**2

def sphere_rpm_from_energy(energy_j):
    """RPM needed to store a given rotational energy."""
    if energy_j <= 0:
        return 0.0
    omega = math.sqrt(2.0 * energy_j / SPHERE_I)
    return omega * 60.0 / (2.0 * PI)

def tidal_acceleration(r_sphere, r_string_tip):
    """Tidal differential acceleration across the string length."""
    a_near = G * BH_MASS_KG / r_string_tip**2
    a_far  = G * BH_MASS_KG / r_sphere**2
    return a_near - a_far

def string_tension(r_sphere, extension_m):
    """Tension in the string at a given extension (tidal gradient model)."""
    r_tip = r_sphere - extension_m
    if r_tip <= BH_RS:
        return 0.0
    delta_a = tidal_acceleration(r_sphere, r_tip)
    # Approximate tension from tidal gradient on tip mass
    return STRING_TIP_MASS * delta_a

def energy_extracted(extension_m, r_sphere=ORBIT_EP_M):
    """Energy extracted by unreeling string to a given extension (constant tension)."""
    return STRING_T_MAX * extension_m

def extension_for_target_energy():
    """String extension needed to reach target rotational energy (constant tension)."""
    return SPHERE_E_PWH / STRING_T_MAX

def gravity_at_distance(r_m):
    """Gravitational acceleration at distance r from the black hole."""
    return G * BH_MASS_KG / r_m**2

def orbital_speed(r_m):
    """Orbital speed at distance r in the elliptical orbit (vis-viva)."""
    return math.sqrt(G * BH_MASS_KG * (2.0/r_m - 1.0/ORBIT_A_M))

def true_anomaly_from_time(t_frac):
    """Approximate true anomaly from fraction of orbital period (0=EP, 0.5=AP)."""
    M = 2.0 * PI * t_frac  # mean anomaly
    E = M + ORBIT_E * math.sin(M)  # initial guess
    # Newton-Raphson: solve E - e*sin(E) = M
    for _ in range(8):
        dE = (E - ORBIT_E * math.sin(E) - M) / (1.0 - ORBIT_E * math.cos(E))
        E -= dE
        if abs(dE) < 1e-10:
            break
    nu = 2.0 * math.atan2(math.sqrt(1.0+ORBIT_E) * math.sin(E/2.0),
                          math.sqrt(1.0-ORBIT_E) * math.cos(E/2.0))
    return nu

def time_fraction_from_true_anomaly(nu):
    """Inverse: compute time fraction from true anomaly using Kepler's equation.
    nu=0 -> t=0 (EP), nu=pi -> t=0.5 (AP)."""
    E = 2.0 * math.atan2(math.sqrt(1.0-ORBIT_E) * math.sin(nu/2.0),
                         math.sqrt(1.0+ORBIT_E) * math.cos(nu/2.0))
    M = E - ORBIT_E * math.sin(E)
    return M / (2.0 * PI)

def compute_phase_bounds():
    """Compute physically accurate phase bounds from orbital mechanics.
    Returns [0, t_charge_end, t_harvest_start, t_harvest_end, 1.0].
    Charging: sphere within 5x EP distance (rapid periastron pass).
    Harvesting: sphere within 5% of AP distance (slow apastron pass)."""
    r_charge_end = min(5.0 * ORBIT_EP_M, 0.8 * ORBIT_AP_M)
    cos_nu_charge = (ORBIT_A_M * (1.0 - ORBIT_E**2) / r_charge_end - 1.0) / ORBIT_E
    cos_nu_charge = max(-1.0, min(1.0, cos_nu_charge))
    nu_charge_end = math.acos(cos_nu_charge)
    t_charge_end = time_fraction_from_true_anomaly(nu_charge_end)

    r_harvest = 0.95 * ORBIT_AP_M
    cos_nu_harvest = (ORBIT_A_M * (1.0 - ORBIT_E**2) / r_harvest - 1.0) / ORBIT_E
    cos_nu_harvest = max(-1.0, min(1.0, cos_nu_harvest))
    nu_harvest_start = math.acos(cos_nu_harvest)
    t_harvest_start = time_fraction_from_true_anomaly(nu_harvest_start)

    nu_harvest_end = 2.0 * PI - nu_harvest_start
    t_harvest_end = time_fraction_from_true_anomaly(nu_harvest_end)

    t_charge_end = max(t_charge_end, 0.002)
    t_harvest_start = min(t_harvest_start, 0.498)
    t_harvest_end = max(t_harvest_end, 0.502)
    if t_harvest_start < t_charge_end:
        t_harvest_start = t_charge_end + 0.01
    if t_harvest_end < t_harvest_start:
        t_harvest_end = t_harvest_start + 0.01

    return [0.0, t_charge_end, t_harvest_start, t_harvest_end, 1.0]

def orbital_position(t_frac):
    """Position (x, z) on the orbit at time fraction t_frac."""
    nu = true_anomaly_from_time(t_frac)
    r = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu))
    x = r * math.cos(nu) * DS
    z = r * math.sin(nu) * DS
    return x, z, r

def orbital_velocity(t_frac):
    """Orbital speed at time fraction."""
    nu = true_anomaly_from_time(t_frac)
    r = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu))
    return orbital_speed(r)

def bh_density():
    """Average density of the black hole (mass / Schwarzschild volume)."""
    vol = (4.0/3.0) * PI * BH_RS**3
    return BH_MASS_KG / vol

def harvest_power():
    """Harvest power during AP flyby (E_spin / harvest_window)."""
    return HARVEST_POWER_W

def relative_flyby_velocity():
    """Relative velocity between sphere at AP and station in circular orbit at AP.
    Sphere at AP has v_AP = sqrt(GM(2/AP - 1/a)) (vis-viva, elliptical).
    Station in circular orbit at AP has v_circ = sqrt(GM/AP).
    Relative speed = |v_circ - v_AP|."""
    v_circ = math.sqrt(G * BH_MASS_KG / ORBIT_AP_M)
    return abs(v_circ - ORBIT_V_AP)

def number_of_harvests_to_deplete():
    """How many harvests until the black hole is depleted (E=mc^2 model)."""
    return int(BH_MASS_KG / MASS_PER_HARVEST)

def deplete_years():
    """Years to deplete at 1 harvest/day."""
    return number_of_harvests_to_deplete() / 365.25


# =============================================================================
# SECTION 3 -- MATH HELPERS (rotation matrices)
# =============================================================================

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)

def rot_z_T(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], dtype=float)

def _mix(c1, c2, t):
    return (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))


# =============================================================================
# SECTION 4 -- GEOMETRY PRIMITIVES (to scale)
# =============================================================================

def _seg(s):
    return max(6, int(round(s)))

def _cyl(r, z0, z1, seg=32):
    seg = _seg(seg); verts, faces = [], []
    ang = np.linspace(0, 2*PI, seg, endpoint=False)
    for z in (z0, z1):
        for a in ang:
            verts.append((r*math.cos(a), r*math.sin(a), z))
    c0 = len(verts); verts.append((0, 0, z0))
    c1 = len(verts); verts.append((0, 0, z1))
    for i in range(seg):
        a, b = i, (i+1) % seg
        faces.append((a, b, seg+b, seg+a))
        faces.append((c0, b, a))
        faces.append((c1, seg+a, seg+b))
    return verts, faces

def _ann(r_out, r_in, z0, z1, seg=32):
    seg = _seg(seg); verts, faces = [], []
    ang = np.linspace(0, 2*PI, seg, endpoint=False)
    for z in (z0, z1):
        for a in ang:
            verts.append((r_out*math.cos(a), r_out*math.sin(a), z))
        for a in ang:
            verts.append((r_in*math.cos(a), r_in*math.sin(a), z))
    def oo(l, i): return l*(2*seg) + (i % seg)
    def ii(l, i): return l*(2*seg) + seg + (i % seg)
    for i in range(seg):
        faces.append((oo(0,i), oo(0,i+1), oo(1,i+1), oo(1,i)))
        faces.append((ii(0,i), ii(1,i), ii(1,i+1), ii(0,i+1)))
        faces.append((oo(0,i), ii(0,i), ii(0,i+1), oo(0,i+1)))
        faces.append((oo(1,i), oo(1,i+1), ii(1,i+1), ii(1,i)))
    return verts, faces

def _box(cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx/2, sy/2, sz/2
    v = [(cx-hx,cy-hy,cz-hz),(cx+hx,cy-hy,cz-hz),(cx+hx,cy+hy,cz-hz),(cx-hx,cy+hy,cz-hz),
         (cx-hx,cy-hy,cz+hz),(cx+hx,cy-hy,cz+hz),(cx+hx,cy+hy,cz+hz),(cx-hx,cy+hy,cz+hz)]
    f = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    return v, f

def _sph(r, seg_u=20, seg_v=12):
    seg_u = _seg(seg_u); seg_v = _seg(seg_v)
    verts, faces = [], []
    for j in range(seg_v + 1):
        va = PI * j / seg_v - PI/2
        for i in range(seg_u):
            ua = 2*PI * i / seg_u
            verts.append((r*math.cos(va)*math.cos(ua), r*math.cos(va)*math.sin(ua), r*math.sin(va)))
    for j in range(seg_v):
        for i in range(seg_u):
            a = j*seg_u + i
            b = j*seg_u + (i+1) % seg_u
            c = (j+1)*seg_u + (i+1) % seg_u
            d = (j+1)*seg_u + i
            faces.append((a, b, c, d))
    return verts, faces

def _cone(rb, z0, z1, seg=24):
    seg = _seg(seg); verts, faces = [], []
    ang = np.linspace(0, 2*PI, seg, endpoint=False)
    for a in ang:
        verts.append((rb*math.cos(a), rb*math.sin(a), z0))
    apex = len(verts); verts.append((0, 0, z1))
    for i in range(seg):
        faces.append((i, (i+1) % seg, apex))
    return verts, faces

def _ring(ro, ri, z, seg=48):
    seg = _seg(seg); verts = []
    ang = np.linspace(0, 2*PI, seg, endpoint=False)
    for a in ang:
        verts.append((ro*math.cos(a), ro*math.sin(a), z))
    for a in ang:
        verts.append((ri*math.cos(a), ri*math.sin(a), z))
    faces = []
    for i in range(seg):
        a, b = i, (i+1) % seg
        faces.append((a, b, seg+b, seg+a))
    return verts, faces

def _torus(R, r, seg_major=32, seg_minor=16):
    seg_major = _seg(seg_major); seg_minor = _seg(seg_minor)
    verts, faces = [], []
    for i in range(seg_major):
        a = 2*PI * i / seg_major
        for j in range(seg_minor):
            b = 2*PI * j / seg_minor
            verts.append(((R + r*math.cos(b)) * math.cos(a),
                          (R + r*math.cos(b)) * math.sin(a),
                          r * math.sin(b)))
    for i in range(seg_major):
        for j in range(seg_minor):
            a = i * seg_minor + j
            b = i * seg_minor + (j+1) % seg_minor
            c = (i+1) % seg_major * seg_minor + (j+1) % seg_minor
            d = (i+1) % seg_major * seg_minor + j
            faces.append((a, b, c, d))
    return verts, faces


# =============================================================================
# SECTION 5 -- MESH & PART CLASSES
# =============================================================================

class Mesh:
    __slots__ = ("verts", "faces", "color", "name", "spin", "group",
                 "pivot", "tilt", "_tilt_RT", "emissive", "alpha",
                 "idx3", "idx4", "_static_wv", "_emissive_col", "_highlight_col")

    def __init__(self, verts, faces, color, name="", spin=0.0, group="default",
                 pivot=(0.,0.,0.), tilt=(0.,0.), emissive=False, alpha=255):
        self.verts = np.asarray(verts, dtype=float)
        self.faces = faces
        self.color = color
        self.name = name
        self.spin = spin
        self.group = group
        self.pivot = np.asarray(pivot, dtype=float)
        self.tilt = tilt
        self.emissive = emissive
        self.alpha = alpha
        rx, ry = tilt
        self._tilt_RT = (rot_x(rx) @ rot_y(ry)).T if (rx or ry) else None
        f3 = [f for f in faces if len(f) == 3]
        f4 = [f for f in faces if len(f) == 4]
        self.idx3 = np.array(f3, dtype=np.intp) if f3 else np.zeros((0,3), dtype=np.intp)
        self.idx4 = np.array(f4, dtype=np.intp) if f4 else np.zeros((0,4), dtype=np.intp)
        # Cache for static meshes (no spin, no tilt)
        self._static_wv = None
        if not self.spin and self._tilt_RT is None:
            self._static_wv = self.verts + self.pivot
        # Pre-compute emissive color
        self._emissive_col = _mix(color, (255, 255, 255), 0.20) if emissive else color
        # Pre-compute highlight color
        self._highlight_col = _mix(color, (255, 255, 255), 0.30)

    def world_verts(self, angle=0.0):
        if self._static_wv is not None:
            return self._static_wv
        v = self.verts
        if self.spin:
            v = v @ rot_z_T(angle * self.spin)
        if self._tilt_RT is not None:
            v = v @ self._tilt_RT
        return v + self.pivot


class Part:
    __slots__ = ("key", "name", "meshes", "specs", "order", "explode", "color", "popdir")

    def __init__(self, key, name, meshes, specs, order, explode, color):
        self.key = key
        self.name = name
        self.meshes = meshes
        self.specs = specs
        self.order = order
        self.explode = np.asarray(explode, dtype=float)
        self.color = color
        n = np.linalg.norm(self.explode)
        self.popdir = self.explode / n if n > 1e-6 else np.array([0., 0., 1.])


# =============================================================================
# SECTION 6 -- COLORS
# =============================================================================

C_BG_TOP    = (8, 10, 20)
C_BG_BOT    = (1, 2, 5)
C_BH        = (5, 5, 8)
C_BH_GLOW   = (255, 160, 50)
C_BH_DISK   = (255, 110, 30)
C_BH_DISK2  = (255, 180, 60)
C_PHOTON    = (140, 100, 255)
C_SPHERE    = (100, 200, 240)
C_SPHERE_HI = (160, 230, 255)
C_STRING    = (210, 215, 230)
C_TIP       = (220, 190, 120)
C_STATION   = (120, 220, 170)
C_STATION_HI= (180, 255, 210)
C_ORBIT     = (100, 140, 220)
C_LASER     = (255, 190, 70)
C_LASER_HI  = (255, 235, 150)
C_GEAR      = (150, 155, 170)
C_GEAR_HI   = (215, 220, 235)
C_MAGNET    = (245, 75, 75)
C_COIL      = (80, 245, 175)
C_GYRO      = (195, 175, 55)
C_TEXT      = (215, 225, 240)
C_DIM       = (100, 115, 135)
C_ACCENT    = (255, 195, 75)
C_WARN      = (255, 110, 55)
C_GOOD      = (110, 225, 140)
C_PANEL     = (18, 24, 38)
C_PANEL_HI  = (28, 36, 54)
C_AP        = (90, 195, 155)
C_EP        = (255, 130, 55)
C_HALBACH   = (245, 85, 85)
C_DRAWSHAFT = (175, 180, 200)
C_SWIVEL    = (130, 195, 250)
C_CLUTCH    = (255, 170, 55)
C_PHASE1    = (255, 130, 55)
C_PHASE2    = (100, 180, 255)
C_PHASE3    = (110, 225, 140)
C_PHASE4    = (150, 130, 200)
# Detailed component colors
C_JET       = (180, 220, 255)   # relativistic jets
C_JET_HI    = (220, 240, 255)   # jet inner core
C_ERGO      = (90, 60, 180)     # ergosphere (Kerr-like)
C_LENS      = (200, 180, 255)   # gravitational lensing rings
C_DOPP_BLUE = (80, 140, 255)    # Doppler blueshifted disk side
C_DOPP_RED  = (220, 100, 50)    # Doppler redshifted disk side
C_COOL_FIN  = (100, 180, 220)   # cryogenic cooling fins
C_LATTICE   = (120, 170, 210)   # graphene lattice pattern
C_FLYWHEEL  = (200, 180, 100)   # internal flywheel
C_HABITAT   = (140, 200, 160)   # habitat interior
C_DOCK      = (180, 190, 210)   # docking port
C_RADIATOR  = (80, 110, 160)    # heat radiator fins
C_SOLAR     = (60, 90, 140)     # solar panel arrays
C_CREW      = (160, 210, 180)   # crew module windows
C_THRUST    = (255, 180, 80)    # thruster glow
C_DEPLOY    = (170, 175, 190)   # deployment mechanism
C_STRESS    = (255, 100, 60)    # stress indicator
C_COUNTER   = (100, 200, 160)   # counter-rotating ring


# =============================================================================
# SECTION 7 -- PART BUILDERS
# =============================================================================

def build_black_hole():
    """Black hole: event horizon, accretion disk with Doppler shift, relativistic jets,
    photon sphere, ISCO ring, ergosphere, gravitational lensing rings."""
    m = []
    rs = BH_DISP_R  # scene-scaled for visibility relative to orbit
    # Adaptive detail based on screen-projected size
    if rs > 1.0:
        eh_segs, eh_rings = 10, 6
        disk_segs = 16
    elif rs > 0.1:
        eh_segs, eh_rings = 14, 8
        disk_segs = 20
    else:
        eh_segs, eh_rings = 16, 10
        disk_segs = 24

    # Gravitational lensing rings (concentric, faint, outside photon sphere)
    for i in range(3):
        lr = rs * (1.8 + 0.3 * i)
        v, f = _ring(lr, lr * 0.98, 0, max(16, disk_segs - 8))
        m.append(Mesh(v, f, _mix(C_LENS, C_BH_GLOW, 0.2 + 0.15 * i),
                      f"Lensing ring {i+1}", alpha=int(80 - 15 * i), emissive=True))

    # Event horizon (black sphere)
    v, f = _sph(rs, eh_segs, eh_rings)
    m.append(Mesh(v, f, C_BH, "Event horizon", spin=0.0, group="bh"))

    # Ergosphere (oblate spheroid, slightly larger than EH - Kerr-like)
    v, f = _sph(rs * 1.3, eh_segs, eh_rings)
    m.append(Mesh(v, f, C_ERGO, "Ergosphere", spin=0.01, group="bh", alpha=60))

    # Photon sphere (faint)
    v2, f2 = _sph(rs * 1.5, 8, 5)
    m.append(Mesh(v2, f2, C_PHOTON, "Photon sphere", spin=0.02, group="bh", alpha=100))

    # Accretion disk inner (bright, hot) - split into Doppler-shifted halves
    # Blueshifted side (approaching, +Z side)
    v3a, f3a = _ann(rs * 3.0, rs * 1.8, -rs * 0.06, rs * 0.06, disk_segs)
    m.append(Mesh(v3a, f3a, _mix(C_BH_DISK, C_DOPP_BLUE, 0.35),
                  "Accretion disk (blueshifted)", spin=0.3, group="bh_disk", alpha=220))
    # Redshifted side (receding, -Z side) - overlay with warm tint
    v3b, f3b = _ann(rs * 3.0, rs * 1.8, -rs * 0.06, rs * 0.06, disk_segs)
    m.append(Mesh(v3b, f3b, _mix(C_BH_DISK, C_DOPP_RED, 0.25),
                  "Accretion disk (redshifted)", spin=0.3, group="bh_disk", alpha=140))

    # Accretion disk outer (cooler, dimmer)
    v4, f4 = _ann(rs * 4.5, rs * 3.0, -rs * 0.03, rs * 0.03, disk_segs)
    m.append(Mesh(v4, f4, C_BH_DISK2, "Disk outer", spin=0.2, group="bh_disk", alpha=140))

    # ISCO ring (innermost stable circular orbit)
    v5, f5 = _ring(rs * 3.5, rs * 3.2, rs * 0.015, max(16, disk_segs - 4))
    m.append(Mesh(v5, f5, C_BH_GLOW, "ISCO ring", spin=0.15, group="bh_disk", alpha=120, emissive=True))

    # Gravitational lensing glow (low detail, very translucent)
    v6, f6 = _sph(rs * 1.15, 6, 4)
    m.append(Mesh(v6, f6, C_BH_GLOW, "Lensing glow", spin=0.0, group="bh", alpha=80, emissive=True))

    # Relativistic jets (perpendicular to disk, along Y axis)
    jet_len = rs * 6.0
    jet_r_base = rs * 0.15
    jet_r_tip = rs * 0.5
    for sign in (-1, 1):
        # Outer jet cone
        v, f = _cone(jet_r_tip, 0, sign * jet_len, 12)
        m.append(Mesh(v, f, C_JET, f"Relativistic jet {'N' if sign > 0 else 'S'}",
                      alpha=80, emissive=True, pivot=(0, 0, 0),
                      tilt=(sign * PI / 2, 0)))
        # Inner jet core (brighter, narrower)
        v, f = _cone(jet_r_base * 0.5, 0, sign * jet_len * 0.7, 8)
        m.append(Mesh(v, f, C_JET_HI, f"Jet core {'N' if sign > 0 else 'S'}",
                      alpha=140, emissive=True, pivot=(0, 0, 0),
                      tilt=(sign * PI / 2, 0)))

    # Hawking radiation glow (very faint, only visible for small BHs)
    hawking_t = 6.169e-8 * M_SUN / BH_MASS_KG
    if hawking_t > 1e-6:  # only show for low-mass BHs
        v, f = _sph(rs * 1.08, 6, 4)
        m.append(Mesh(v, f, (150, 200, 255), "Hawking radiation",
                      spin=0.0, group="bh", alpha=30, emissive=True))

    rs_display = f"{BH_RS/1000:.1f} km" if BH_RS >= 1000 else f"{BH_RS:.3e} m"
    rph_display = f"{BH_RPH/1000:.1f} km" if BH_RPH >= 1000 else f"{BH_RPH:.3e} m"
    risco_display = f"{BH_RISCO/1000:.1f} km" if BH_RISCO >= 1000 else f"{BH_RISCO:.3e} m"
    return Part("blackhole", f"BLACK HOLE ({CURRENT_SYSTEM_NAME})", m, [
        f"Mass: {BH_MASS_KG/M_SUN:.2f} solar masses ({BH_MASS_KG:.3e} kg)",
        f"Schwarzschild radius: {rs_display}",
        f"Photon sphere: {rph_display} (1.5 r_s)",
        f"ISCO: {risco_display} (3 r_s)",
        f"Ergosphere: {rs_display} (oblate, Kerr-like)",
        f"Average density: {bh_density():.2e} kg/m^3",
        f"Total energy (E=mc^2): {BH_MASS_KG * C**2:.2e} J",
        f"Distance from Earth: {BH_DIST_LY:.0f} ly",
        f"Surface gravity: {G*BH_MASS_KG/BH_RS**2:.2e} m/s^2",
        f"Hawking temperature: {hawking_t:.3e} K",
        f"Hawking power: {1.0546e-34 * C**6 / (15360.0 * PI * G**2 * BH_MASS_KG**2):.3e} W",
        "Type: Schwarzschild (non-rotating)",
        "Relativistic jets: perpendicular to accretion disk",
        "Doppler shift: blueshifted (approaching) / redshifted (receding)",
        "Gravitational lensing: photon paths bent near EH",
        "Energy source for the harvester system",
    ], 0, (0, 0, 0), C_BH)


def build_orbit():
    """Elliptical orbit path from EP to AP."""
    m = []
    segs = 64
    pts = []
    for i in range(segs):
        t_frac = i / segs
        nu = true_anomaly_from_time(t_frac)
        r = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu))
        x = r * math.cos(nu) * DS
        z = r * math.sin(nu) * DS
        pts.append((x, 0, z))
    # Merge orbit segments into a single mesh for performance
    all_v = []
    all_f = []
    for i in range(segs):
        p0 = pts[i]
        p1 = pts[(i+1) % segs]
        cx, cz = (p0[0]+p1[0])/2, (p0[2]+p1[2])/2
        dx, dz = p1[0]-p0[0], p1[2]-p0[2]
        length = math.hypot(dx, dz)
        if length < 1e-8:
            continue
        angle = math.atan2(dx, dz)
        v, f = _box(0, 0, 0, SCENE_R * 0.012, SCENE_R * 0.004, length)
        base = len(all_v)
        Ry = rot_y(angle)
        offset = np.array([cx, 0, cz])
        for vv in v:
            tv = Ry @ np.array(vv) + offset
            all_v.append(tuple(tv))
        for ff in f:
            all_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(all_v, all_f, C_ORBIT, "Orbit path", alpha=200))
    # Direction arrows along orbit (show travel direction)
    arrow_v, arrow_f = [], []
    n_arrows = 8
    for ai in range(n_arrows):
        t = ai / n_arrows
        nu = true_anomaly_from_time(t)
        r = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu))
        x = r * math.cos(nu) * DS
        z = r * math.sin(nu) * DS
        # Next point for direction
        nu2 = true_anomaly_from_time((ai + 0.5) / n_arrows)
        r2 = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu2))
        x2 = r2 * math.cos(nu2) * DS
        z2 = r2 * math.sin(nu2) * DS
        dx, dz = x2 - x, z2 - z
        angle = math.atan2(dx, dz)
        # Small arrow cone
        v, f = _cone(SCENE_R * 0.003, 0, SCENE_R * 0.008, 6)
        base = len(arrow_v)
        Ry = rot_y(angle)
        for vv in v:
            tv = Ry @ np.array(vv)
            arrow_v.append((tv[0] + x, tv[1], tv[2] + z))
        for ff in f:
            arrow_f.append(tuple(idx + base for idx in ff))
    if arrow_v:
        m.append(Mesh(arrow_v, arrow_f, C_ACCENT, "Direction arrows", emissive=True, alpha=160))
    # EP marker
    v, f = _sph(SCENE_R * 0.005, 12, 8)
    m.append(Mesh(v, f, C_EP, "Periastron (EP)", emissive=True, alpha=200,
                  pivot=(ORBIT_EP_M * DS, 0, 0)))
    # EP ring (emphasize periastron)
    v, f = _ring(SCENE_R * 0.008, SCENE_R * 0.006, 0, 16)
    m.append(Mesh(v, f, C_EP, "EP ring", emissive=True, alpha=120,
                  pivot=(ORBIT_EP_M * DS, 0, 0)))
    # AP marker
    v, f = _sph(SCENE_R * 0.005, 12, 8)
    m.append(Mesh(v, f, C_AP, "Apastron (AP)", emissive=True, alpha=200,
                  pivot=(-ORBIT_AP_M * DS, 0, 0)))
    # AP ring (emphasize apastron)
    v, f = _ring(SCENE_R * 0.008, SCENE_R * 0.006, 0, 16)
    m.append(Mesh(v, f, C_AP, "AP ring", emissive=True, alpha=120,
                  pivot=(-ORBIT_AP_M * DS, 0, 0)))
    # Phase zone markers (4 colored dots at phase boundaries)
    phase_colors = [C_PHASE1, C_PHASE2, C_PHASE3, C_PHASE4]
    phase_names = ["Charging", "Outbound", "Harvesting", "Inbound"]
    phase_fracs = [0.0, 0.1, 0.5, 0.9]
    phase_v, phase_f = [], []
    for i, (tf, pc) in enumerate(zip(phase_fracs, phase_colors)):
        nu = true_anomaly_from_time(tf)
        r = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu))
        x = r * math.cos(nu) * DS
        z = r * math.sin(nu) * DS
        v, f = _sph(SCENE_R * 0.003, 8, 6)
        base = len(phase_v)
        for vv in v:
            phase_v.append((vv[0]+x, vv[1], vv[2]+z))
        for ff in f:
            phase_f.append(tuple(idx + base for idx in ff))
    if phase_v:
        m.append(Mesh(phase_v, phase_f, C_ACCENT, "Phase markers", emissive=True, alpha=180))
    # Velocity vector at EP (tangent to orbit, scaled)
    vep_len = SCENE_R * 0.04 * (ORBIT_V_EP / max(ORBIT_V_EP, ORBIT_V_AP))
    nu_ep = 0.0
    r_ep = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu_ep))
    # Tangent direction at EP (perpendicular to radius, in orbital plane)
    vep_dx = -math.sin(nu_ep)
    vep_dz = math.cos(nu_ep)
    vep_angle = math.atan2(vep_dx, vep_dz)
    v, f = _cone(SCENE_R * 0.003, 0, vep_len, 6)
    m.append(Mesh(v, f, C_WARN, "V@EP vector", emissive=True, alpha=200,
                  pivot=(r_ep * math.cos(nu_ep) * DS, 0, r_ep * math.sin(nu_ep) * DS),
                  tilt=(0, vep_angle)))
    # Velocity vector at AP
    vap_len = SCENE_R * 0.04 * (ORBIT_V_AP / max(ORBIT_V_EP, ORBIT_V_AP))
    nu_ap = PI
    r_ap = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu_ap))
    vap_dx = -math.sin(nu_ap)
    vap_dz = math.cos(nu_ap)
    vap_angle = math.atan2(vap_dx, vap_dz)
    v, f = _cone(SCENE_R * 0.003, 0, vap_len, 6)
    m.append(Mesh(v, f, C_GOOD, "V@AP vector", emissive=True, alpha=200,
                  pivot=(r_ap * math.cos(nu_ap) * DS, 0, r_ap * math.sin(nu_ap) * DS),
                  tilt=(0, vap_angle)))
    # Ghosted sphere position markers along orbit (show trajectory distribution)
    n_ghosts = 8
    ghost_v, ghost_f = [], []
    for gi in range(n_ghosts):
        t_g = gi / n_ghosts
        nu_g = true_anomaly_from_time(t_g)
        r_g = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu_g))
        x_g = r_g * math.cos(nu_g) * DS
        z_g = r_g * math.sin(nu_g) * DS
        v, f = _sph(SCENE_R * 0.002, 6, 4)
        base = len(ghost_v)
        for vv in v:
            ghost_v.append((vv[0] + x_g, vv[1], vv[2] + z_g))
        for ff in f:
            ghost_f.append(tuple(idx + base for idx in ff))
    if ghost_v:
        m.append(Mesh(ghost_v, ghost_f, _mix(C_SPHERE, C_ORBIT, 0.5),
                      "Trajectory markers", alpha=80, emissive=True))
    return Part("orbit", "ORBITAL PATH", m, [
        f"Periastron (EP): {ORBIT_EP_AU:.2f} AU ({ORBIT_EP_M:.3e} m)",
        f"Apastron (AP): {ORBIT_AP_AU:.2f} AU ({ORBIT_AP_M:.3e} m)",
        f"Semi-major axis: {ORBIT_A_M/AU_M:.2f} AU",
        f"Eccentricity: {ORBIT_E:.3f}",
        f"Orbital period: {ORBIT_PERIOD_YR:.1f} years",
        f"Velocity at EP: {ORBIT_V_EP/1000:.1f} km/s",
        f"Velocity at AP: {ORBIT_V_AP/1000:.1f} km/s",
        f"Gravity at EP: {gravity_at_distance(ORBIT_EP_M):.2e} m/s^2",
        f"Gravity at AP: {gravity_at_distance(ORBIT_AP_M):.2e} m/s^2",
        f"EP drift/cycle: {EP_DRIFT_KM:.4f} km (compensated by laser)",
        f"Safety margin: {SAFETY_MARGIN*100:.0f}% excess impact parameter",
        f"Highly eccentric ellipse around {CURRENT_SYSTEM_NAME}",
        "Phase zones: Charging (EP) -> Outbound -> Harvesting (AP) -> Inbound",
        "Velocity vectors: orange=EP (max), green=AP (min)",
        f"NOTE: BH/sphere/station visually enlarged for visibility",
        f"  Real Rs/EP ratio = {BH_RS/ORBIT_EP_M:.2e} (BH is {BH_RS/ORBIT_EP_M*100:.4f}% of EP)",
    ], 1, (0, 0, 0), C_ORBIT)


def build_sphere():
    """The energy-harvesting sphere: body, Halbach array, internal structure."""
    m = []
    r = SPHERE_DISP_R  # scene-scaled for visibility relative to orbit
    # Main body
    v, f = _sph(r, 12, 8)
    m.append(Mesh(v, f, C_SPHERE, "Sphere body", spin=1.0, group="sphere"))
    # Reinforcement coating layers (concentric, low detail since translucent)
    for i in range(3):
        v, f = _sph(r * (1.0 + 0.01 * (i+1)), 8, 6)
        m.append(Mesh(v, f, _mix(C_SPHERE, C_SPHERE_HI, 0.3 + 0.2*i),
                      f"Coating layer {i+1}", spin=1.0, group="sphere", alpha=60))
    # Halbach array magnets around equator (merged into single mesh)
    n_mag = 16
    hal_v = []
    hal_f = []
    for i in range(n_mag):
        a = 2*PI * i / n_mag
        mx = r * 1.02 * math.cos(a)
        my = r * 1.02 * math.sin(a)
        v, f = _box(mx, my, 0, r*0.08, r*0.08, r*0.15)
        base = len(hal_v)
        for vv in v:
            hal_v.append(vv)
        for ff in f:
            hal_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(hal_v, hal_f, C_MAGNET, "Halbach array", spin=1.0, group="sphere"))
    # Polar aperture (BH-facing pole, -X direction)
    v, f = _cyl(r*0.08, -r*1.05, -r*0.9, 16)
    m.append(Mesh(v, f, C_GEAR, "Polar aperture", spin=1.0, group="sphere"))
    # Internal drum
    v, f = _cyl(r*0.3, -r*0.5, r*0.5, 16)
    m.append(Mesh(v, f, C_GEAR_HI, "Drum", spin=1.0, group="drum"))
    # Gear train (4 stages of planetary gears)
    for stage in range(GEAR_STAGES):
        sr = r * (0.15 + 0.05 * stage)
        sz = r * (0.3 - 0.08 * stage)
        # Sun gear
        v, f = _cyl(sr * 0.3, sz-0.01, sz+0.01, 10)
        m.append(Mesh(v, f, C_GEAR, f"Sun gear S{stage+1}", spin=2.0+stage, group="gear"))
        # Planet gears (3 per stage)
        for p in range(3):
            pa = 2*PI * p / 3
            px = sr * 0.65 * math.cos(pa)
            py = sr * 0.65 * math.sin(pa)
            v, f = _cyl(sr * 0.2, sz-0.01, sz+0.01, 8)
            m.append(Mesh(v, f, C_GEAR_HI, f"Planet {stage+1}.{p}",
                          spin=-(2.0+stage), pivot=(px, py, 0)))
        # Ring gear
        v, f = _ann(sr, sr*0.9, sz-0.01, sz+0.01, 16)
        m.append(Mesh(v, f, C_GEAR, f"Ring S{stage+1}", alpha=160))
    # Drive shaft (connects gears to sphere interior)
    v, f = _cyl(r*0.05, -r*0.6, r*0.6, 12)
    m.append(Mesh(v, f, C_DRAWSHAFT, "Drive shaft", spin=1.0, group="shaft"))
    # Rotary swivel at pole
    v, f = _sph(r*0.06, 10, 6)
    m.append(Mesh(v, f, C_SWIVEL, "Swivel joint", pivot=(-r*0.95, 0, 0)))
    # Electromagnetic clutch
    v, f = _ann(r*0.12, r*0.08, -r*0.35, -r*0.25, 16)
    m.append(Mesh(v, f, C_CLUTCH, "EM clutch", alpha=180))
    # Ratchet mechanism
    v, f = _cyl(r*0.04, -r*0.32, -r*0.28, 8)
    m.append(Mesh(v, f, C_GEAR, "Ratchet", spin=1.0, group="drum"))
    # Eddy current brake
    v, f = _ann(r*0.14, r*0.10, -r*0.42, -r*0.38, 12)
    m.append(Mesh(v, f, C_MAGNET, "Eddy brake", alpha=120))
    # RTG housing (radioisotope thermoelectric generator)
    v, f = _box(r*0.6, r*0.3, r*0.3, r*0.12, r*0.12, r*0.12)
    m.append(Mesh(v, f, C_GEAR, "RTG housing", alpha=180))
    # Sensor array (accelerometers, strain gauges, Doppler) - merged
    sen_v, sen_f = [], []
    for i in range(4):
        sa = 2*PI * i / 4
        sx = r * 1.01 * math.cos(sa)
        sy = r * 1.01 * math.sin(sa)
        v, f = _sph(r*0.03, 8, 6)
        base = len(sen_v)
        for vv in v:
            sen_v.append((vv[0]+sx, vv[1]+sy, vv[2]))
        for ff in f:
            sen_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(sen_v, sen_f, C_SWIVEL, "Sensor array"))
    # Escape thrusters (ion drives) - merged
    thr_v, thr_f = [], []
    for i in range(3):
        ta = 2*PI * i / 3 + PI/6
        tx = r * 0.98 * math.cos(ta)
        ty = r * 0.98 * math.sin(ta)
        v, f = _cone(r*0.04, r*1.08, r*1.15, 8)
        base = len(thr_v)
        for vv in v:
            thr_v.append((vv[0]+tx, vv[1]+ty, vv[2]))
        for ff in f:
            thr_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(thr_v, thr_f, C_GEAR_HI, "Escape thrusters"))
    # Thruster glow nozzles (emissive)
    glow_v, glow_f = [], []
    for i in range(3):
        ta = 2*PI * i / 3 + PI/6
        tx = r * 0.98 * math.cos(ta)
        ty = r * 0.98 * math.sin(ta)
        v, f = _sph(r*0.025, 6, 4)
        base = len(glow_v)
        for vv in v:
            glow_v.append((vv[0]+tx, vv[1]+ty, vv[2]+r*1.15))
        for ff in f:
            glow_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(glow_v, glow_f, C_THRUST, "Thruster glow", emissive=True, alpha=180))
    # Internal flywheel (counter-rotating, stores angular momentum)
    v, f = _cyl(r*0.22, -r*0.15, r*0.15, 14)
    m.append(Mesh(v, f, C_FLYWHEEL, "Internal flywheel", spin=-0.5, group="drum"))
    # Flywheel rim (heavier outer edge)
    v, f = _ann(r*0.22, r*0.18, -r*0.16, r*0.16, 14)
    m.append(Mesh(v, f, _mix(C_FLYWHEEL, C_GEAR_HI, 0.4), "Flywheel rim",
                  spin=-0.5, group="drum", alpha=200))
    # Counter-rotating ring (stabilization)
    v, f = _ann(r*0.45, r*0.42, -r*0.02, r*0.02, 16)
    m.append(Mesh(v, f, C_COUNTER, "Counter-rotating ring", spin=-0.3, group="drum", alpha=140))
    # Cryogenic cooling fins (radial fins around equator, between Halbach magnets)
    fin_v, fin_f = [], []
    n_fins = 8
    for i in range(n_fins):
        a = 2*PI * (i + 0.5) / n_mag  # offset between magnets
        fx = r * 1.03 * math.cos(a)
        fy = r * 1.03 * math.sin(a)
        v, f = _box(fx, fy, 0, r*0.03, r*0.12, r*0.25)
        base = len(fin_v)
        for vv in v:
            fin_v.append(vv)
        for ff in f:
            fin_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(fin_v, fin_f, C_COOL_FIN, "Cryogenic cooling fins", alpha=160))
    # Graphene lattice ribs (meridian lines on sphere surface)
    rib_v, rib_f = [], []
    n_ribs = 6
    for i in range(n_ribs):
        a = 2*PI * i / n_ribs
        for j in range(8):
            va0 = PI * j / 8 - PI/2
            va1 = PI * (j+1) / 8 - PI/2
            x0 = r * 1.005 * math.cos(va0) * math.cos(a)
            y0 = r * 1.005 * math.cos(va0) * math.sin(a)
            z0 = r * 1.005 * math.sin(va0)
            x1 = r * 1.005 * math.cos(va1) * math.cos(a)
            y1 = r * 1.005 * math.cos(va1) * math.sin(a)
            z1 = r * 1.005 * math.sin(va1)
            # Small box segment along meridian
            mx, my, mz = (x0+x1)/2, (y0+y1)/2, (z0+z1)/2
            dx, dy, dz = x1-x0, y1-y0, z1-z0
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length < 1e-6:
                continue
            v, f = _box(mx, my, mz, r*0.008, r*0.008, length)
            base = len(rib_v)
            for vv in v:
                rib_v.append(vv)
            for ff in f:
                rib_f.append(tuple(idx + base for idx in ff))
    if rib_v:
        m.append(Mesh(rib_v, rib_f, C_LATTICE, "Graphene lattice ribs",
                      spin=1.0, group="sphere", alpha=100))
    # Communication antenna boom (opposite from BH-facing pole)
    v, f = _cyl(r*0.015, r*0.9, r*1.2, 8)
    m.append(Mesh(v, f, C_STATION_HI, "Comm antenna boom", spin=1.0, group="sphere"))
    # Antenna dish at boom tip
    v, f = _cone(r*0.04, r*1.15, r*1.25, 10)
    m.append(Mesh(v, f, C_STATION_HI, "Antenna dish", spin=1.0, group="sphere", alpha=180))
    # Radiation shielding panels (boron composite, on outer surface)
    shield_v, shield_f = [], []
    for i in range(4):
        a = 2*PI * i / 4 + PI/4
        sx = r * 1.015 * math.cos(a)
        sy = r * 1.015 * math.sin(a)
        v, f = _box(sx, sy, 0, r*0.02, r*0.15, r*0.3)
        base = len(shield_v)
        for vv in v:
            shield_v.append(vv)
        for ff in f:
            shield_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(shield_v, shield_f, _mix(C_GEAR, (80,60,40), 0.5),
                  "Radiation shielding", alpha=140))
    return Part("sphere", "ENERGY SPHERE", m, [
        f"Mass: {SPHERE_MASS_KG:.2e} kg",
        f"Radius: {SPHERE_RADIUS_M:.0f} m",
        f"Material: Graphene composite",
        f"Density: {SPHERE_DENSITY:.0f} kg/m^3",
        f"Tensile strength: {SPHERE_TENSILE_PA/1e9:.0f} GPa",
        f"Max RPM: {SPHERE_RPM_MAX:.0f} ({SPHERE_E_MAX/3.6e18:.2f} PWh capacity)",
        f"Target RPM: {SPHERE_RPM_TARGET:.0f} (5% below max)",
        f"Operating energy: {SPHERE_E_OPER:.2e} J ({SPHERE_E_OPER/3.6e18:.2f} PWh)",
        f"Max capacity: {SPHERE_E_MAX:.2e} J ({SPHERE_E_MAX/3.6e18:.2f} PWh at {SPHERE_RPM_MAX:.0f} RPM)",
        f"Moment of inertia: {SPHERE_I:.2e} kg m^2",
        f"Gear ratio: {GEAR_RATIO_TOTAL:.0f}:1 ({GEAR_STAGES} stages x {GEAR_RATIO_PER:.0f}:1)",
        f"Efficiency: {GEAR_EFFICIENCY*100:.0f}%",
        "Disengagement: triple-redundant (EM clutch + swivel + ratchet + eddy brake)",
        f"RTG power: {SPHERE_RTG_W/1000:.0f} kW total (Pu-238)",
        f"Halbach freq: {HALBACH_FREQ_HZ:.1f} Hz at {SPHERE_RPM_TARGET:.0f} RPM",
        "Magnets: cryogenically cooled (superconducting)",
        f"Escape thrusters: ion drives, delta-v = {SPHERE_DELTA_V:.0f} m/s",
        "Radiation shielding: boron composites",
        f"Safety margin: {SAFETY_MARGIN*100:.0f}% excess impact parameter",
        "Sensors: halt unreeling if dg spikes >10%",
        "Manufacturing: additive graphene-carbyne lattices",
        "Internal flywheel: counter-rotating angular momentum storage",
        "Cooling: cryogenic fins between Halbach array elements",
        "Lattice: graphene meridian ribs for structural integrity",
        "Counter-rotating ring: gyroscopic stabilization",
    ], 2, (0, 0, 0.15), C_SPHERE)


def build_string(extension_frac=0.0):
    """The string extending from the sphere's pole toward the black hole.
    extension_frac: 0=reeled in, 1=fully extended."""
    m = []
    r_sphere = SPHERE_DISP_R  # match sphere scale
    # String length in display units (scene-scaled)
    max_len = STRING_LENGTH_M * DS * STRING_DISP_SCALE  # scale for visibility
    cur_len = max_len * extension_frac
    if cur_len < 0.001:
        cur_len = 0.001
    # String shaft (from pole toward BH, i.e. -X direction)
    str_r = max(0.003, STRING_DIAM_M * DS * STRING_DISP_SCALE * 10)  # visible thickness
    v, f = _cyl(str_r, -r_sphere * 1.1 - cur_len, -r_sphere * 1.1, 12)
    m.append(Mesh(v, f, C_STRING, "String", alpha=220))
    # Tapered section near tip
    if cur_len > 0.01:
        v, f = _cone(str_r * 1.5, -r_sphere * 1.1 - cur_len, -r_sphere * 1.1 - cur_len + 0.02, 12)
        m.append(Mesh(v, f, _mix(C_STRING, C_TIP, 0.3), "String taper", alpha=200))
    # Tip mass (osmium sphere) with detail
    tip_r = max(0.01, STRING_TIP_R_M * DS * STRING_DISP_SCALE * 10)
    v, f = _sph(tip_r, 12, 8)
    m.append(Mesh(v, f, C_TIP, "Tip mass (osmium)",
                  pivot=(-r_sphere * 1.1 - cur_len - tip_r, 0, 0)))
    # Tip mass attachment ring
    v, f = _ann(tip_r * 1.15, tip_r * 1.05, -r_sphere * 1.1 - cur_len - tip_r * 0.1,
                -r_sphere * 1.1 - cur_len - tip_r * 0.05, 12)
    m.append(Mesh(v, f, C_GEAR, "Tip attachment ring", alpha=180))
    # Deployment drum mechanism (at sphere pole, where string exits)
    drum_r = max(0.015, str_r * 3)
    v, f = _cyl(drum_r, -r_sphere * 1.12, -r_sphere * 1.08, 12)
    m.append(Mesh(v, f, C_DEPLOY, "Deployment drum", alpha=200))
    # Drum end caps
    v, f = _ann(drum_r * 1.1, drum_r * 0.9, -r_sphere * 1.13, -r_sphere * 1.07, 12)
    m.append(Mesh(v, f, C_GEAR_HI, "Drum caps", alpha=160))
    # Tension visualization (segmented with color gradient: cool near sphere, hot near tip)
    if extension_frac > 0.01:
        n_segs = 12
        for i in range(n_segs):
            frac = i / n_segs
            z0 = -r_sphere * 1.1 - cur_len * (1.0 - frac)
            z1 = -r_sphere * 1.1 - cur_len * (1.0 - (i+1)/n_segs)
            if abs(z1 - z0) < 0.001:
                continue
            # Color gradient: blue (low tension) near sphere -> red (high tension) near tip
            t_frac_color = frac  # 0 at sphere, 1 at tip
            seg_col = _mix(C_COOL_FIN, C_STRESS, t_frac_color * extension_frac)
            v, f = _cyl(str_r * 1.15, z0, z1, 8)
            m.append(Mesh(v, f, seg_col, f"Tension seg {i+1}",
                         alpha=int(100 + 80 * extension_frac)))
    # Stress indicator rings (at high-stress points along string)
    if extension_frac > 0.05:
        stress_v, stress_f = [], []
        n_stress = 3
        for i in range(n_stress):
            frac = 0.3 + 0.2 * i  # stress points at 30%, 50%, 70% along string
            sz = -r_sphere * 1.1 - cur_len * (1.0 - frac)
            v, f = _ann(str_r * 1.4, str_r * 1.2, sz - 0.003, sz + 0.003, 10)
            base = len(stress_v)
            for vv in v:
                stress_v.append(vv)
            for ff in f:
                stress_f.append(tuple(idx + base for idx in ff))
        if stress_v:
            m.append(Mesh(stress_v, stress_f, C_STRESS, "Stress indicators",
                         alpha=int(120 + 60 * extension_frac), emissive=True))
    # String guide roller (at sphere pole exit point)
    v, f = _cyl(str_r * 2, -r_sphere * 1.07, -r_sphere * 1.05, 10)
    m.append(Mesh(v, f, C_GEAR_HI, "Guide roller", alpha=180))
    return Part("string", "STRING & TIP MASS", m, [
        "Material: Graphene composite",
        "Manufacturing: CVD-grown, bundled strands for flexibility",
        f"Diameter: {STRING_DIAM_M*100:.1f} cm ({STRING_DIAM_M/0.0254:.1f} in)",
        f"Tensile strength: {STRING_TENSILE/1e9:.0f} GPa",
        f"Max tension: {STRING_T_MAX:.2e} N",
        f"Length: {STRING_LENGTH_M:.2e} m ({STRING_LENGTH_MI:.0f} miles)",
        f"Tip mass: {STRING_TIP_MASS:.2e} kg (osmium, R={STRING_TIP_R_M:.0f} m)",
        f"Safety margin: {SAFETY_MARGIN*100:.0f}% excess impact parameter",
        f"Current extension: {extension_frac*100:.1f}%",
        f"Energy at full extension: {SPHERE_E_PWH:.2e} J",
        "Reusable: reeled back at AP (not sacrificed)",
        "Deployment: motorized drum with guide roller",
        "Tension gradient: color-coded (blue=low, red=high)",
        "Stress rings: at 30%, 50%, 70% along string length",
        "Tip attachment: osmium sphere with locking ring",
    ], 3, (0, 0, -0.1), C_STRING)


def build_station():
    """Space station at AP: gyroscopic flywheel, receiver coils, gravity laser, habitat,
    docking ports, crew modules, heat radiators, solar arrays, truss structure."""
    m = []
    s = STATION_DISP_S  # scene-scaled station size
    # Main hull (central module)
    v, f = _box(0, 0, 0, s*2, s*0.8, s*0.6)
    m.append(Mesh(v, f, C_STATION, "Station hull", alpha=200))
    # Hull reinforcement ribs (merged)
    rib_v, rib_f = [], []
    for i in range(5):
        x = -s + i * s * 0.5
        v, f = _box(x, 0, 0, s*0.01, s*0.82, s*0.62)
        base = len(rib_v)
        for vv in v:
            rib_v.append(vv)
        for ff in f:
            rib_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(rib_v, rib_f, _mix(C_STATION, C_GEAR, 0.4), "Hull ribs", alpha=160))
    # Habitat module (cylinder perpendicular to hull, rotating for artificial gravity)
    v, f = _cyl(s*0.25, -s*0.4, s*0.4, 16)
    m.append(Mesh(v, f, C_HABITAT, "Habitat module", spin=0.5, group="gyro", alpha=180))
    # Habitat window strip (emissive, simulating lit windows)
    v, f = _ann(s*0.26, s*0.24, -s*0.35, s*0.35, 16)
    m.append(Mesh(v, f, C_CREW, "Habitat windows", spin=0.5, group="gyro", alpha=120, emissive=True))
    # Docking ring around habitat
    v, f = _ann(s*0.28, s*0.25, -s*0.02, s*0.02, 16)
    m.append(Mesh(v, f, C_DOCK, "Docking ring", alpha=160))
    # Docking ports (3 ports around ring)
    dock_v, dock_f = [], []
    for i in range(3):
        a = 2*PI * i / 3
        dx = s * 0.27 * math.cos(a)
        dy = s * 0.27 * math.sin(a)
        v, f = _cyl(s*0.03, -s*0.06, s*0.06, 8)
        base = len(dock_v)
        for vv in v:
            dock_v.append((vv[0]+dx, vv[1]+dy, vv[2]))
        for ff in f:
            dock_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(dock_v, dock_f, C_DOCK, "Docking ports", alpha=180))
    # Truss structure (connecting hull to radiator panels)
    truss_v, truss_f = [], []
    for side in (-1, 1):
        for offset in (0, s*0.5):
            # Diagonal truss beams
            v, f = _box(side * s*1.1, offset, 0, s*0.4, s*0.02, s*0.02)
            base = len(truss_v)
            for vv in v:
                truss_v.append(vv)
            for ff in f:
                truss_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(truss_v, truss_f, C_GEAR, "Truss structure", alpha=140))
    # Heat radiator fins (large, dark panels for thermal rejection)
    rad_v, rad_f = [], []
    for side in (-1, 1):
        for offset in (0, s*0.5):
            v, f = _box(side * s*1.5, offset, 0, s*0.8, s*0.01, s*0.55)
            base = len(rad_v)
            for vv in v:
                rad_v.append(vv)
            for ff in f:
                rad_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(rad_v, rad_f, C_RADIATOR, "Heat radiator fins", alpha=180))
    # Radiator coolant pipes (merged, small cylinders along panel edges)
    pipe_v, pipe_f = [], []
    for side in (-1, 1):
        for offset in (0, s*0.5):
            v, f = _cyl(0.003, side*s*1.1, side*s*1.9, 6)
            base = len(pipe_v)
            for vv in v:
                pipe_v.append((vv[0], vv[1]+offset, vv[2]))
            for ff in f:
                pipe_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(pipe_v, pipe_f, C_COOL_FIN, "Coolant pipes", alpha=160))
    # Solar panel arrays (smaller, angled panels for backup power)
    sol_v, sol_f = [], []
    for side in (-1, 1):
        v, f = _box(side * s*1.5, -s*0.7, 0, s*0.5, s*0.01, s*0.35)
        base = len(sol_v)
        for vv in v:
            sol_v.append(vv)
        for ff in f:
            sol_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(sol_v, sol_f, C_SOLAR, "Solar panel arrays", alpha=200))
    # Gyroscopic flywheel (unbalanced, for station-keeping)
    v, f = _cyl(s*0.3, -s*0.1, s*0.1, 20)
    m.append(Mesh(v, f, C_GYRO, "Gyro flywheel", spin=3.0, group="gyro"))
    # Offset mass on flywheel (the "unbalanced" part)
    v, f = _sph(s*0.06, 8, 6)
    m.append(Mesh(v, f, C_GYRO, "Gyro offset mass", spin=3.0, group="gyro",
                  pivot=(s*0.3, 0, 0)))
    # Gimbal frame
    v, f = _ann(s*0.35, s*0.32, -s*0.12, s*0.12, 20)
    m.append(Mesh(v, f, C_GEAR, "Gimbal frame", alpha=160))
    # Gimbal outer ring
    v, f = _ann(s*0.4, s*0.37, -s*0.14, s*0.14, 16)
    m.append(Mesh(v, f, C_GEAR_HI, "Gimbal outer ring", alpha=120))
    # Receiver coil array (long array along flyby path, segmented for visibility)
    coil_len = 0.18
    coil_v, coil_f = [], []
    n_coils = 5
    for i in range(n_coils):
        cz = -coil_len/2 + coil_len * (i + 0.5) / n_coils
        seg_half = coil_len / (n_coils * 2) * 0.8
        v, f = _cyl(0.005, cz - seg_half, cz + seg_half, 12)
        base = len(coil_v)
        for vv in v:
            coil_v.append(vv)
        for ff in f:
            coil_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(coil_v, coil_f, C_COIL, "Receiver coil array", emissive=True, alpha=180))
    # Coil support struts (merged)
    strut_v, strut_f = [], []
    for i in range(4):
        a = 2*PI * i / 4
        v, f = _box(math.cos(a)*0.025, math.sin(a)*0.025, 0,
                    0.004, 0.004, coil_len*0.9)
        base = len(strut_v)
        for vv in v:
            strut_v.append(vv)
        for ff in f:
            strut_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(strut_v, strut_f, C_STATION_HI, "Coil struts"))
    # Gravity laser emitter (larger, more prominent)
    v, f = _cone(s*0.09, s*0.3, s*0.55, 16)
    m.append(Mesh(v, f, C_LASER, "Gravity laser emitter", alpha=200))
    v, f = _cyl(s*0.06, s*0.25, s*0.38, 12)
    m.append(Mesh(v, f, C_LASER_HI, "Laser aperture", emissive=True))
    # Laser focusing lens (in front of aperture)
    v, f = _sph(s*0.04, 8, 6)
    m.append(Mesh(v, f, C_LASER_HI, "Focusing lens", emissive=True, alpha=200,
                  pivot=(s*0.42, 0, 0)))
    # Communication dish
    v, f = _cone(s*0.1, s*0.5, s*0.65, 16)
    m.append(Mesh(v, f, C_STATION, "Comm dish", alpha=180))
    # Antenna array (small spikes)
    ant_v, ant_f = [], []
    for i in range(3):
        aa = 2*PI * i / 3
        v, f = _cyl(0.003, 0, s*0.15, 6)
        base = len(ant_v)
        for vv in v:
            ant_v.append((vv[0] + math.cos(aa)*s*0.3, vv[1] + s*0.3, vv[2] + math.sin(aa)*s*0.3))
        for ff in f:
            ant_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(ant_v, ant_f, C_STATION_HI, "Antenna array"))
    # Fusion reactor housing (powers gravity laser)
    v, f = _box(s*0.8, -s*0.3, 0, s*0.3, s*0.3, s*0.4)
    m.append(Mesh(v, f, _mix(C_LASER, (70,55,35), 0.35), "Fusion reactor", alpha=180))
    # Reactor glow indicator
    v, f = _sph(s*0.08, 8, 6)
    m.append(Mesh(v, f, C_LASER_HI, "Reactor glow", emissive=True, alpha=120,
                  pivot=(s*0.8, -s*0.3, 0)))
    # Reactor coolant loop (torus around reactor)
    v, f = _torus(s*0.25, s*0.02, 12, 6)
    m.append(Mesh(v, f, C_COOL_FIN, "Reactor coolant loop", alpha=140,
                  pivot=(s*0.8, -s*0.3, 0)))
    # Crew module (small pressurized section on hull)
    v, f = _cyl(s*0.08, s*0.3, s*0.5, 10)
    m.append(Mesh(v, f, C_HABITAT, "Crew module", alpha=180))
    # Crew module window
    v, f = _sph(s*0.03, 6, 4)
    m.append(Mesh(v, f, C_CREW, "Crew window", emissive=True, alpha=200,
                  pivot=(s*0.42, 0, s*0.08)))
    # Position at AP (negative X)
    for mesh in m:
        mesh.pivot = mesh.pivot + np.array([-ORBIT_AP_M * DS, 0, 0])
        if mesh._static_wv is not None:
            mesh._static_wv = mesh.verts + mesh.pivot
    return Part("station", "SPACE STATION (AP)", m, [
        f"Position: Apastron ({ORBIT_AP_AU:.2f} AU, circular orbit)",
        f"Mass: ~{STATION_MASS_KG:.0e} kg",
        f"Gravity at AP: {gravity_at_distance(ORBIT_AP_M):.2e} m/s^2",
        f"Station orbit: circular at AP, v_circ={math.sqrt(G*BH_MASS_KG/ORBIT_AP_M)/1000:.1f} km/s",
        f"Station-keeping: Unbalanced gyroscopic flywheel",
        f"  Gyro mass: {STATION_GYRO_MASS:.0e} kg, R={STATION_GYRO_R:.0f} m",
        f"  Gyro RPM: {STATION_GYRO_RPM:.0f}",
        f"  Efficiency: {GYRO_EFFICIENCY*100:.0f}% (regenerative, losses as heat)",
        f"  Powered by ~1% of harvested energy",
        f"Harvesting: Magnetic inductive coupling (non-contact)",
        f"  Halbach B-field: {STATION_B_FIELD:.1f} T (NdFeB, cryogenic)",
        f"  Rotating field: {HALBACH_FREQ_HZ:.1f} Hz at {SPHERE_RPM_TARGET:.0f} RPM",
        f"  Coil array: {STATION_COIL_LEN/1000:.0f} km superconducting (YBCO, LHe cooled)",
        f"  Harvest window: {STATION_HARVEST_S/86400:.0f} days near AP",
        f"  Avg power: {harvest_power()/1e9:.1f} GW",
        f"  Efficiency: {STATION_EFFICIENCY*100:.0f}% (after rectification)",
        f"  Flyby separation: ~10-100 m, relative speed ~{relative_flyby_velocity()/1000:.1f} km/s",
        f"  Energy/harvest: {HARVEST_ENERGY_J:.2e} J",
        f"Gravity laser: {LASER_POWER_GW:.0f} GW (graviton emitter, eff={LASER_EFFICIENCY*100:.0f}%)",
        f"Fusion reactor: ~{STATION_FUSION_TW:.0f} TW (helium-3)",
        "Targeting: optical telescopes + Doppler radar",
        "Comms: quantum-encrypted laser links",
        "Function: Harvest spin energy + orbital correction",
        "Habitat: rotating cylinder, artificial gravity",
        "Docking: 3 ports, automated approach",
        "Thermal: radiator fins + coolant loops",
        "Power: solar arrays (backup) + fusion (primary)",
        "Crew: pressurized module with life support",
    ], 4, (0, 0, 0.2), C_STATION)


def build_gravity_laser(t_frac=0.0):
    """Gravity laser beam from station to sphere for orbital correction.
    Visible during correction phases (near EP outbound and at AP).
    Shows segmented beam, targeting reticle, and pulse glow."""
    m = []
    # Determine if laser should be visible
    # Phase 1 early: near EP outbound correction ; 0.45-0.55: AP correction
    show = (0.05 < t_frac < 0.08) or (0.45 < t_frac < 0.55)
    if not show:
        return Part("laser", "GRAVITY LASER", [], [], 5, (0, 0, 0.3), C_LASER)

    sx, sz, r = orbital_position(t_frac)
    station_x = -ORBIT_AP_M * DS
    station_z = 0.0
    dx = sx - station_x
    dz = sz - station_z
    dist = math.hypot(dx, dz)
    if dist < 0.01:
        return Part("laser", "GRAVITY LASER", [], [], 5, (0, 0, 0.3), C_LASER)
    angle = math.atan2(dx, dz)

    # Outer beam (wide, translucent)
    beam_r = SCENE_R * 0.001
    v, f = _cone(beam_r, 0, dist, 8)
    m.append(Mesh(v, f, C_LASER, "Laser beam", alpha=100,
                  pivot=(station_x, 0, station_z), tilt=(0, angle)))

    # Mid beam (medium brightness)
    v, f = _cone(beam_r * 0.6, 0, dist * 0.98, 8)
    m.append(Mesh(v, f, _mix(C_LASER, C_LASER_HI, 0.4), "Laser mid", alpha=140,
                  pivot=(station_x, 0, station_z), tilt=(0, angle)))

    # Inner core (bright, narrow)
    v, f = _cone(beam_r * 0.25, 0, dist * 0.95, 6)
    m.append(Mesh(v, f, C_LASER_HI, "Laser core", alpha=200,
                  pivot=(station_x, 0, station_z), tilt=(0, angle)))

    # Pulse glow at emitter (station side)
    v, f = _sph(SCENE_R * 0.002, 8, 6)
    m.append(Mesh(v, f, C_LASER_HI, "Emitter pulse", emissive=True, alpha=200,
                  pivot=(station_x, 0, station_z)))

    # Targeting reticle at sphere (ring + crosshair)
    reticle_v, reticle_f = [], []
    # Ring around target
    v, f = _ring(SCENE_R * 0.002, SCENE_R * 0.0015, 0, 12)
    base = len(reticle_v)
    for vv in v:
        reticle_v.append((vv[0]+sx, vv[1], vv[2]+sz))
    for ff in f:
        reticle_f.append(tuple(idx + base for idx in ff))
    # Crosshair lines (4 short boxes)
    for ci in range(4):
        ca = 2 * PI * ci / 4
        cx = SCENE_R * 0.0025 * math.cos(ca)
        cz = SCENE_R * 0.0025 * math.sin(ca)
        v, f = _box(0, 0, 0, SCENE_R * 0.0003, SCENE_R * 0.0003, SCENE_R * 0.0012)
        Ry = rot_y(ca)
        base = len(reticle_v)
        reticle_offset = np.array([sx + cx * 0.5, 0, sz + cz * 0.5])
        for vv in v:
            tv = Ry @ np.array(vv) + reticle_offset
            reticle_v.append(tuple(tv))
        for ff in f:
            reticle_f.append(tuple(idx + base for idx in ff))
    if reticle_v:
        m.append(Mesh(reticle_v, reticle_f, C_LASER_HI, "Targeting reticle",
                      emissive=True, alpha=180))

    # Impact glow at target
    v, f = _sph(SCENE_R * 0.002, 8, 6)
    m.append(Mesh(v, f, C_LASER_HI, "Impact glow", emissive=True, alpha=200,
                  pivot=(sx, 0, sz)))

    return Part("laser", "GRAVITY LASER", m, [
        f"Power: {LASER_POWER_GW:.0f} GW (graviton emitter, eff={LASER_EFFICIENCY*100:.0f}%)",
        f"Force: {LASER_FORCE_N:.0e} N (outward radial pull)",
        f"Target: sphere at r={r/AU_M:.2f} AU",
        "Phase 2: Corrects AP drift near EP (outbound, f~5 deg, ~1 day post-EP)",
        "  Oberth effect: less delta-v needed at high speed (~0.001 m/s)",
        "Phase 4: Restores EP at AP passage (tangential/radial, ~0.0005 m/s)",
        f"EP drift/cycle: {EP_DRIFT_KM:.4f} km (compensated)",
        "Beam divergence: <1 urad, transmission ~1.5 hr",
        "Targeting: optical telescopes + Doppler radar",
        "Beam: 3-layer (outer/mid/core) with targeting reticle",
    ], 5, (0, 0, 0.3), C_LASER)


def build_constellation(n_spheres=None):
    """Constellation of N spheres in phased orbits (one harvest per day).
    Shows sphere dots along orbit path with faint connecting path line."""
    if n_spheres is None:
        n_spheres = N_SPHERES
    m = []
    # Merge all sphere dots into a single mesh for performance
    all_v = []
    all_f = []
    n_vis = min(n_spheres, 150)  # cap visual dots for performance
    # Use lower detail for more spheres to maintain performance
    if n_vis > 80:
        sph_segs, sph_rings = 4, 3  # very low detail (12 faces/sphere)
    else:
        sph_segs, sph_rings = 5, 4  # low detail (20 faces/sphere)
    # Also build orbit path segments connecting sphere positions
    path_v = []
    path_f = []
    for i in range(n_vis):
        t_frac = i / n_spheres
        nu = true_anomaly_from_time(t_frac)
        r = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu))
        x = r * math.cos(nu) * DS
        z = r * math.sin(nu) * DS
        v, f = _sph(SCENE_R * 0.004, sph_segs, sph_rings)
        base = len(all_v)
        for vv in v:
            all_v.append((vv[0] + x, vv[1], vv[2] + z))
        for ff in f:
            all_f.append(tuple(idx + base for idx in ff))
        # Path segment to next sphere
        if i < n_vis - 1:
            t_next = (i + 1) / n_spheres
            nu2 = true_anomaly_from_time(t_next)
            r2 = ORBIT_A_M * (1.0 - ORBIT_E**2) / (1.0 + ORBIT_E * math.cos(nu2))
            x2 = r2 * math.cos(nu2) * DS
            z2 = r2 * math.sin(nu2) * DS
            cx, cz = (x + x2) / 2, (z + z2) / 2
            dx, dz = x2 - x, z2 - z
            length = math.hypot(dx, dz)
            if length > 1e-8:
                angle = math.atan2(dx, dz)
                v, f = _box(0, 0, 0, SCENE_R * 0.001, SCENE_R * 0.0004, length)
                base = len(path_v)
                Ry = rot_y(angle)
                offset = np.array([cx, 0, cz])
                for vv in v:
                    tv = Ry @ np.array(vv) + offset
                    path_v.append(tuple(tv))
                for ff in f:
                    path_f.append(tuple(idx + base for idx in ff))
    m.append(Mesh(all_v, all_f, C_SPHERE, "Constellation dots", alpha=200))
    if path_v:
        m.append(Mesh(path_v, path_f, _mix(C_ORBIT, C_SPHERE, 0.3),
                      "Constellation path", alpha=60))
    return Part("constellation", "SPHERE CONSTELLATION", m, [
        f"Count: {N_SPHERES} spheres",
        f"Harvest rate: 1 per day",
        f"Energy/harvest: {SPHERE_E_PWH:.2e} J ({SPHERE_E_PWH/3.6e18:.2f} PWh)",
        f"Mass equivalent/harvest: {MASS_PER_HARVEST:.0f} kg (E=mc^2)",
        f"Total harvests to deplete BH: {HARVESTS_TO_DEPLETE:.2e}",
        f"Depletion time: {DEPLETE_YEARS:.2e} years",
        f"Annual energy: {N_SPHERES * SPHERE_E_PWH / 3.6e18:.0f} PWh/yr",
        f"Powers ~{HOMES_POWERED/1e6:.0f}M homes continuously",
        "Phased orbits: one EP passage per day",
        f"Visual: {n_vis} dots + connecting path line",
    ], 6, (0, 0, -0.2), C_SPHERE)


def build_trail(sim):
    """Build a fading trail mesh from recent orbital positions."""
    if len(sim.trail) < 2:
        return None
    all_v = []
    all_f = []
    n = len(sim.trail)
    for i in range(n - 1):
        x0, z0 = sim.trail[i]
        x1, z1 = sim.trail[i + 1]
        dx, dz = x1 - x0, z1 - z0
        length = math.hypot(dx, dz)
        if length < 1e-8:
            continue
        # Fade: older segments are thinner
        frac = (i + 1) / n  # 0..1, newer = higher
        thickness = max(SCENE_R * 0.0003, SCENE_R * 0.0012 * frac)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        angle = math.atan2(dx, dz)
        v, f = _box(0, 0, 0, thickness, SCENE_R * 0.0002, length)
        base = len(all_v)
        Ry = rot_y(angle)
        offset = np.array([cx, 0, cz])
        for vv in v:
            tv = Ry @ np.array(vv) + offset
            all_v.append(tuple(tv))
        for ff in f:
            all_f.append(tuple(idx + base for idx in ff))
    if not all_v:
        return None
    # Color fades from dim to bright accent
    m = [Mesh(all_v, all_f, C_ACCENT, "Orbital trail", alpha=120, emissive=True)]
    return Part("trail", "ORBITAL TRAIL", m, [
        f"Trail points: {n}",
        f"Shows recent orbital path",
    ], 7, (0, 0, 0), C_ACCENT)


def build_energy_effects(sim):
    """Dynamic visual effects based on simulation state.
    Shows energy flow beams, charging glow, and spin indicators."""
    m = []
    sx, sz, r = sim.orbital_pos()
    station_x = -ORBIT_AP_M * DS
    station_z = 0.0

    # Phase 0: Charging - string tension glow near sphere pole
    if sim.phase_idx == 0 and sim.string_ext > 0.01:
        # Glow sphere at sphere pole (where string attaches)
        glow_r = SCENE_R * 0.003 + SCENE_R * 0.001 * sim.string_ext
        v, f = _sph(glow_r, 10, 6)
        # Position near sphere pole pointing toward BH
        bh_angle = math.atan2(-sz, sx)
        gx = sx + math.cos(bh_angle) * SCENE_R * 0.006
        gz = sz + math.sin(bh_angle) * SCENE_R * 0.006
        m.append(Mesh(v, f, C_WARN, "Charging glow", emissive=True, alpha=180,
                      pivot=(gx, 0, gz)))
        # Tension line glow segments along string
        if sim.string_ext > 0.05:
            n_glow = 6
            glow_v, glow_f = [], []
            str_r = SCENE_R * 0.0006
            for i in range(n_glow):
                frac = i / n_glow
                # Position along string from sphere toward BH
                t = frac * sim.string_ext
                px = sx + math.cos(bh_angle) * (SCENE_R * 0.006 + t * SCENE_R * 0.02)
                pz = sz + math.sin(bh_angle) * (SCENE_R * 0.006 + t * SCENE_R * 0.02)
                v, f = _sph(str_r * (1.5 - frac * 0.5), 6, 4)
                base = len(glow_v)
                for vv in v:
                    glow_v.append((vv[0] + px, vv[1], vv[2] + pz))
                for ff in f:
                    glow_f.append(tuple(idx + base for idx in ff))
            if glow_v:
                m.append(Mesh(glow_v, glow_f, _mix(C_WARN, C_LASER, 0.4),
                             "Tension glow", emissive=True, alpha=120))

    # Phase 2: Harvesting - energy beam/glow between sphere and station
    if sim.phase_idx == 2:
        dx = sx - station_x
        dz = sz - station_z
        dist = math.hypot(dx, dz)
        har_frac = 1.0 - (sim.t_frac - sim.phase_bounds[2]) / (sim.phase_bounds[3] - sim.phase_bounds[2])
        if dist > 0.01:
            angle = math.atan2(dx, dz)
            # Main energy beam (pulsing green)
            beam_r = SCENE_R * 0.001 + SCENE_R * 0.0005 * har_frac
            v, f = _cone(beam_r, 0, dist, 8)
            m.append(Mesh(v, f, C_COIL, "Energy beam", emissive=True, alpha=140,
                          pivot=(station_x, 0, station_z), tilt=(0, angle)))
            # Inner bright core
            v, f = _cone(beam_r * 0.4, 0, dist * 0.95, 6)
            m.append(Mesh(v, f, C_GOOD, "Beam core", emissive=True, alpha=200,
                          pivot=(station_x, 0, station_z), tilt=(0, angle)))
            # Energy flow particles along beam (small spheres traveling station->sphere)
            n_flow = 5
            flow_v, flow_f = [], []
            for fi in range(n_flow):
                t = (fi + 0.5) / n_flow  # 0 at station, 1 at sphere
                # Interpolate position along beam
                px = station_x + dx * t
                pz = station_z + dz * t
                v, f = _sph(SCENE_R * 0.0006, 5, 4)
                base = len(flow_v)
                for vv in v:
                    flow_v.append((vv[0] + px, vv[1], vv[2] + pz))
                for ff in f:
                    flow_f.append(tuple(idx + base for idx in ff))
            if flow_v:
                m.append(Mesh(flow_v, flow_f, C_GOOD, "Energy flow particles",
                              emissive=True, alpha=200))
        # Glow at sphere (harvest point) - always show during harvest
        v, f = _sph(SCENE_R * 0.004, 10, 6)
        m.append(Mesh(v, f, C_COIL, "Harvest glow", emissive=True, alpha=160,
                      pivot=(sx, 0, sz)))
        # Glow at station coils - always show during harvest
        v, f = _sph(SCENE_R * 0.003, 10, 6)
        m.append(Mesh(v, f, C_COIL, "Coil glow", emissive=True, alpha=160,
                      pivot=(station_x, 0, station_z)))
        # Magnetic field rings around sphere (Halbach array visualization)
        n_rings = 3
        ring_v, ring_f = [], []
        for ri in range(n_rings):
            ring_r = SCENE_R * 0.005 + SCENE_R * 0.002 * ri
            v, f = _ring(ring_r, ring_r * 0.9, 0, 16)
            base = len(ring_v)
            for vv in v:
                ring_v.append((vv[0] + sx, vv[1], vv[2] + sz))
            for ff in f:
                ring_f.append(tuple(idx + base for idx in ff))
        if ring_v:
            m.append(Mesh(ring_v, ring_f, C_HALBACH, "Magnetic field", emissive=True, alpha=100))
        # Magnetic field lines (torus around sphere showing dipole field)
        v, f = _torus(SCENE_R * 0.005, SCENE_R * 0.001, 12, 6)
        m.append(Mesh(v, f, C_HALBACH, "Field lines (torus)", emissive=True, alpha=80,
                      pivot=(sx, 0, sz)))
        # Spin indicator ring (shows sphere is spinning, counter-rotating)
        v, f = _ring(SCENE_R * 0.004, SCENE_R * 0.0035, 0, 16)
        m.append(Mesh(v, f, C_FLYWHEEL, "Spin indicator", spin=2.0, group="drum",
                      alpha=120, emissive=True, pivot=(sx, 0, sz)))

    # Phase 1: Laser correction - brighten laser beam
    if sim.phase_idx == 1 and sim.laser_active:
        # Laser glow at sphere position
        v, f = _sph(SCENE_R * 0.002, 8, 6)
        m.append(Mesh(v, f, C_LASER_HI, "Laser impact", emissive=True, alpha=200,
                      pivot=(sx, 0, sz)))

    # Phase 3: Laser correction at AP
    if sim.phase_idx == 3 and sim.laser_active:
        v, f = _sph(SCENE_R * 0.002, 8, 6)
        m.append(Mesh(v, f, C_LASER_HI, "Laser impact", emissive=True, alpha=200,
                      pivot=(sx, 0, sz)))

    if not m:
        return None
    return Part("effects", "ENERGY FLOW", m, [
        f"Phase: {sim.phase_name()}",
        f"Active effects: {len(m)}",
        "Components: beam, core, flow particles, field rings, torus, spin indicator",
    ], 7, (0, 0, 0), C_GOOD)


def build_depletion_scene(dep):
    """Build 3D scene for BH depletion/instability view.
    Shows shrinking black hole, Hawking radiation, and final explosion."""
    m = []
    mass_frac = dep.mass_fraction()
    rs = dep.schwarzschild_radius() * DS * (BH_DISP_R / max(BH_RS * DS, 1e-12))  # match build_black_hole scale
    if rs < 0.001:
        rs = 0.001

    if dep.exploded:
        # === EXPLOSION PHASE ===
        prog = dep.explosion_progress()
        # Gamma flash (brief, intense white at start)
        if prog < 0.15:
            flash_alpha = int(255 * (1.0 - prog / 0.15))
            v, f = _sph(rs * 0.5, 8, 6)
            m.append(Mesh(v, f, (255, 255, 255), "Gamma flash", alpha=flash_alpha, emissive=True))
        # Expanding shockwave shell
        shell_r = rs * (1.0 + prog * 20.0)
        v, f = _sph(shell_r, 16, 12)
        exp_col = _mix(C_BH_GLOW, (255, 255, 255), prog)
        m.append(Mesh(v, f, exp_col, "Shockwave", alpha=int(200 * (1.0 - prog * 0.7)),
                      emissive=True, group="bh"))
        # Expanding ring waves (2 rings at different speeds, in disk plane)
        for wi in range(2):
            wave_r = rs * (1.0 + prog * (15.0 + wi * 8.0))
            wave_w = rs * 0.08 * (1.0 - prog * 0.5)
            if wave_w > 0.001:
                v, f = _ring(wave_r, max(wave_r - wave_w, wave_r * 0.95), 0, 20)
                m.append(Mesh(v, f, _mix((255, 200, 100), C_BH_GLOW, prog),
                              f"Ring wave {wi+1}", alpha=int(150 * (1.0 - prog * 0.8)),
                              emissive=True))
        # Inner bright core (fading)
        core_r = rs * (1.0 + prog * 3.0)
        v, f = _sph(core_r, 12, 8)
        core_col = _mix((255, 255, 255), C_BH_GLOW, prog)
        m.append(Mesh(v, f, core_col, "Explosion core", alpha=int(255 * (1.0 - prog * 0.5)),
                      emissive=True))
        # Radiation jets (two cones along Y axis)
        jet_len = rs * (2.0 + prog * 15.0)
        jet_r = rs * (0.3 + prog * 2.0)
        for sign in (-1, 1):
            v, f = _cone(jet_r, 0, sign * jet_len, 12)
            m.append(Mesh(v, f, _mix(C_BH_GLOW, (255, 200, 100), prog),
                         f"Jet {'N' if sign > 0 else 'S'}", alpha=int(180 * (1.0 - prog * 0.6)),
                         emissive=True, pivot=(0, 0, 0), tilt=(sign * PI / 2, 0)))
            # Jet core (brighter inner cone)
            v, f = _cone(jet_r * 0.4, 0, sign * jet_len * 0.85, 8)
            m.append(Mesh(v, f, (255, 240, 200),
                         f"Jet core {'N' if sign > 0 else 'S'}", alpha=int(220 * (1.0 - prog * 0.5)),
                         emissive=True, pivot=(0, 0, 0), tilt=(sign * PI / 2, 0)))
        # Particle debris (scattered spheres)
        if prog < 0.8:
            n_debris = 20
            dev, def_ = [], []
            rng = np.random.RandomState(123)
            for i in range(n_debris):
                angle = rng.uniform(0, 2 * PI)
                elev = rng.uniform(-PI / 2, PI / 2)
                dist = rs * (1.0 + prog * rng.uniform(5, 18))
                dx = dist * math.cos(elev) * math.cos(angle)
                dy = dist * math.sin(elev)
                dz = dist * math.cos(elev) * math.sin(angle)
                dr = rs * 0.05 * (1.0 - prog)
                v, f = _sph(max(0.001, dr), 6, 4)
                base = len(dev)
                for vv in v:
                    dev.append((vv[0] + dx, vv[1] + dy, vv[2] + dz))
                for ff in f:
                    def_.append(tuple(idx + base for idx in ff))
            if dev:
                m.append(Mesh(dev, def_, C_BH_GLOW, "Debris", alpha=int(160 * (1.0 - prog)),
                              emissive=True))
        # Secondary explosion particles (smaller, faster, appear slightly later)
        if 0.1 < prog < 0.7:
            n_sec = 12
            sec_v, sec_f = [], []
            rng2 = np.random.RandomState(456)
            for i in range(n_sec):
                angle = rng2.uniform(0, 2 * PI)
                elev = rng2.uniform(-PI / 2, PI / 2)
                dist = rs * (0.5 + prog * rng2.uniform(3, 10))
                dx = dist * math.cos(elev) * math.cos(angle)
                dy = dist * math.sin(elev)
                dz = dist * math.cos(elev) * math.sin(angle)
                dr = rs * 0.03 * (1.0 - prog)
                v, f = _sph(max(0.001, dr), 5, 4)
                base = len(sec_v)
                for vv in v:
                    sec_v.append((vv[0] + dx, vv[1] + dy, vv[2] + dz))
                for ff in f:
                    sec_f.append(tuple(idx + base for idx in ff))
            if sec_v:
                m.append(Mesh(sec_v, sec_f, (255, 180, 120), "Secondary debris",
                              alpha=int(120 * (1.0 - prog)), emissive=True))
        # Planck remnant (tiny bright dot at center, appears after explosion peaks)
        if prog > 0.5:
            rem_r = 0.002
            v, f = _sph(rem_r, 8, 6)
            m.append(Mesh(v, f, (255, 255, 255), "Planck remnant", emissive=True, alpha=255))
        # Wormhole tunnel forming (appears as explosion fades, prog > 0.6)
        if prog > 0.6:
            wh_prog = (prog - 0.6) / 0.4  # 0..1 within wormhole phase
            # Funnel throat (narrowing tunnel along Y axis)
            throat_r = rs * 0.3 * (1.0 - wh_prog * 0.7)
            throat_len = rs * (3.0 + wh_prog * 8.0)
            n_rings = 8
            wh_v, wh_f = [], []
            for ri in range(n_rings):
                t = ri / (n_rings - 1)
                ring_r = throat_r * (1.0 + t * 2.0)  # widens toward far end
                y0 = -throat_len * 0.5 + throat_len * t
                segs = 16
                for si in range(segs):
                    a0 = 2 * PI * si / segs
                    a1 = 2 * PI * (si + 1) / segs
                    # Quad: (ring_r*cos(a0), y0, ring_r*sin(a0)) -> (ring_r*cos(a1), y0, ring_r*sin(a1))
                    # -> far end ring
                    base = len(wh_v)
                    wh_v.append((ring_r * math.cos(a0), y0, ring_r * math.sin(a0)))
                    wh_v.append((ring_r * math.cos(a1), y0, ring_r * math.sin(a1)))
                    wh_f.append((base, base + 1, base))
                # Connect to next ring
                if ri < n_rings - 1:
                    next_r = throat_r * (1.0 + (t + 1.0/(n_rings-1)) * 2.0)
                    y1 = -throat_len * 0.5 + throat_len * (t + 1.0/(n_rings-1))
                    for si in range(segs):
                        a0 = 2 * PI * si / segs
                        a1 = 2 * PI * (si + 1) / segs
                        base = len(wh_v)
                        wh_v.append((ring_r * math.cos(a0), y0, ring_r * math.sin(a0)))
                        wh_v.append((ring_r * math.cos(a1), y0, ring_r * math.sin(a1)))
                        wh_v.append((next_r * math.cos(a1), y1, next_r * math.sin(a1)))
                        wh_v.append((next_r * math.cos(a0), y1, next_r * math.sin(a0)))
                        wh_f.append((base, base + 1, base + 2))
                        wh_f.append((base, base + 2, base + 3))
            if wh_v:
                wh_col = _mix((100, 80, 200), (200, 150, 255), wh_prog)
                m.append(Mesh(wh_v, wh_f, wh_col, "Wormhole throat",
                             alpha=int(120 * wh_prog), emissive=True))
            # White hole emerging (bright sphere at far end of wormhole)
            wh_r = rs * (0.1 + wh_prog * 0.5)
            wh_y = throat_len * 0.5
            v, f = _sph(wh_r, 12, 8)
            m.append(Mesh(v, f, (255, 240, 200), "White hole",
                         emissive=True, alpha=int(200 * wh_prog),
                         pivot=(0, wh_y, 0)))
            # White hole radiation burst (expanding shell)
            burst_r = wh_r * (1.0 + wh_prog * 3.0)
            v, f = _sph(burst_r, 10, 6)
            m.append(Mesh(v, f, (255, 220, 150), "WH radiation",
                         emissive=True, alpha=int(100 * wh_prog),
                         pivot=(0, wh_y, 0)))
        specs = [
            "=== BLACK HOLE EXPLOSION ===",
            f"Explosion progress: {prog*100:.1f}%",
            f"Energy released: {dep.initial_mass * C**2:.2e} J",
            "Hawking radiation runaway -> final burst",
            f"Planck remnant: ~2.18e-8 kg, ~4 Planck lengths",
            f"Remnant density: ~5.16e96 kg/m^3",
            "All mass converted to radiation",
        ]
        if prog > 0.6:
            specs.append("=== WORMHOLE / WHITE HOLE ===")
            specs.append("Einstein-Rosen bridge forming")
            specs.append("White hole: time-reverse of BH")
            specs.append("Matter/light can only exit (not enter)")
            specs.append("Theoretical: ER=EPR conjecture")
            specs.append("Unstable, short-lived in practice")
        return Part("depletion", "BH DEPLETION - EXPLOSION", m, specs, 0, (0, 0, 0), C_BH_GLOW)

    # === STABLE/DEPLETING PHASE ===
    # Adaptive detail based on visual size
    if rs > 2.0 or rs < 0.01:
        eh_segs, eh_rings = 16, 10
        disk_segs = 24
    else:
        eh_segs, eh_rings = 24, 16
        disk_segs = 36

    # Gravitational lensing rings (concentric, faint)
    for i in range(3):
        lr = rs * (1.8 + 0.3 * i)
        v, f = _ring(lr, lr * 0.98, 0, max(16, disk_segs - 8))
        m.append(Mesh(v, f, _mix(C_LENS, C_BH_GLOW, 0.2 + 0.15 * i),
                      f"Lensing ring {i+1}", alpha=int(50 - 10 * i), emissive=True))

    # Event horizon (shrinking)
    v, f = _sph(rs, eh_segs, eh_rings)
    m.append(Mesh(v, f, C_BH, "Event horizon", spin=0.0, group="bh"))

    # Ergosphere (oblate spheroid, Kerr-like)
    v, f = _sph(rs * 1.3, eh_segs, eh_rings)
    m.append(Mesh(v, f, C_ERGO, "Ergosphere", spin=0.01, group="bh", alpha=30))

    # Hawking radiation glow (intensifies as mass decreases)
    hawking_intensity = 1.0 - mass_frac  # 0 at full mass, 1 at depleted
    glow_r = rs * (1.15 + hawking_intensity * 0.5)
    glow_alpha = int(40 + hawking_intensity * 180)
    glow_col = _mix(C_BH_GLOW, (100, 200, 255), hawking_intensity)
    v, f = _sph(glow_r, 8, 6)
    m.append(Mesh(v, f, glow_col, "Hawking radiation", spin=0.0, group="bh",
                  alpha=glow_alpha, emissive=True))

    # Photon sphere
    v, f = _sph(rs * 1.5, 8, 5)
    m.append(Mesh(v, f, C_PHOTON, "Photon sphere", spin=0.02, group="bh", alpha=60))

    # Accretion disk (Doppler-shifted, shrinks with BH, color shifts hotter as mass decreases)
    disk_inner = rs * 1.6
    disk_outer = rs * (2.5 + hawking_intensity * 1.5)
    disk_col_blue = _mix(_mix(C_BH_DISK, C_DOPP_BLUE, 0.35), (150, 200, 255), hawking_intensity)
    v, f = _ann(disk_outer, disk_inner, -rs * 0.05, rs * 0.05, disk_segs)
    m.append(Mesh(v, f, disk_col_blue, "Accretion disk (blueshifted)",
                  spin=0.3, group="bh_disk", alpha=180))
    disk_col_red = _mix(_mix(C_BH_DISK, C_DOPP_RED, 0.25), (150, 200, 255), hawking_intensity)
    v, f = _ann(disk_outer, disk_inner, -rs * 0.05, rs * 0.05, disk_segs)
    m.append(Mesh(v, f, disk_col_red, "Accretion disk (redshifted)",
                  spin=0.3, group="bh_disk", alpha=100))

    # Outer disk (cooler, dimmer)
    v, f = _ann(rs * 3.5, rs * 2.5, -rs * 0.02, rs * 0.02, disk_segs)
    m.append(Mesh(v, f, C_BH_DISK2, "Disk outer", spin=0.2, group="bh_disk", alpha=100))

    # ISCO ring
    v, f = _ring(rs * 3.0, rs * 2.8, rs * 0.01, max(16, disk_segs - 4))
    m.append(Mesh(v, f, C_BH_GLOW, "ISCO ring", spin=0.15, group="bh_disk", alpha=80, emissive=True))

    # Relativistic jets (perpendicular to disk, intensify as Hawking radiation increases)
    jet_len = rs * (4.0 + hawking_intensity * 4.0)
    jet_r_base = rs * 0.12
    jet_r_tip = rs * (0.3 + hawking_intensity * 0.3)
    jet_alpha = int(60 + hawking_intensity * 80)
    for sign in (-1, 1):
        v, f = _cone(jet_r_tip, 0, sign * jet_len, 10)
        m.append(Mesh(v, f, _mix(C_JET, (255, 200, 100), hawking_intensity),
                      f"Relativistic jet {'N' if sign > 0 else 'S'}",
                      alpha=jet_alpha, emissive=True, pivot=(0, 0, 0),
                      tilt=(sign * PI / 2, 0)))
        v, f = _cone(jet_r_base * 0.5, 0, sign * jet_len * 0.7, 6)
        m.append(Mesh(v, f, C_JET_HI, f"Jet core {'N' if sign > 0 else 'S'}",
                      alpha=int(jet_alpha * 1.5), emissive=True, pivot=(0, 0, 0),
                      tilt=(sign * PI / 2, 0)))

    # Hawking radiation particles (emitted from event horizon)
    n_particles = int(10 + hawking_intensity * 40)
    if n_particles > 0:
        part_v, part_f = [], []
        rng = np.random.RandomState(dep.particle_seed % 10000)
        for i in range(n_particles):
            angle = rng.uniform(0, 2 * PI)
            elev = rng.uniform(-PI / 2, PI / 2)
            dist = rs * rng.uniform(1.2, 2.5 + hawking_intensity * 3.0)
            px = dist * math.cos(elev) * math.cos(angle)
            py = dist * math.sin(elev)
            pz = dist * math.cos(elev) * math.sin(angle)
            pr = rs * 0.02 * (1.0 + hawking_intensity)
            v, f = _sph(max(0.001, pr), 5, 4)
            base = len(part_v)
            for vv in v:
                part_v.append((vv[0] + px, vv[1] + py, vv[2] + pz))
            for ff in f:
                part_f.append(tuple(idx + base for idx in ff))
        if part_v:
            part_col = _mix(C_BH_GLOW, (150, 220, 255), hawking_intensity)
            m.append(Mesh(part_v, part_f, part_col, "Hawking particles",
                         emissive=True, alpha=int(100 + hawking_intensity * 100)))

    # Harvesting beam effects (spheres harvesting energy)
    if mass_frac > 0.01:
        n_harvest_beams = min(8, max(1, int(dep.harvest_rate_per_yr)))
        beam_v, beam_f = [], []
        for i in range(n_harvest_beams):
            angle = 2 * PI * i / n_harvest_beams + dep.disc_angle * 0.1
            beam_dist = rs * 4.0
            bx = beam_dist * math.cos(angle)
            bz = beam_dist * math.sin(angle)
            # Small sphere representing harvesting sphere
            v, f = _sph(rs * 0.08, 6, 4)
            base = len(beam_v)
            for vv in v:
                beam_v.append((vv[0] + bx, vv[1], vv[2] + bz))
            for ff in f:
                beam_f.append(tuple(idx + base for idx in ff))
            # Energy beam from sphere to BH
            beam_len = math.hypot(bx, bz)
            beam_angle = math.atan2(bx, bz)
            v, f = _cone(rs * 0.015, 0, beam_len, 6)
            base = len(beam_v)
            Ry = rot_y(beam_angle)
            for vv in v:
                tv = Ry @ np.array(vv)
                beam_v.append((tv[0] + bx, tv[1], tv[2] + bz))
            for ff in f:
                beam_f.append(tuple(idx + base for idx in ff))
        if beam_v:
            m.append(Mesh(beam_v, beam_f, C_COIL, "Harvesting spheres",
                         emissive=True, alpha=150))

    # Build specs
    t_h = dep.hawking_temperature()
    p_h = dep.hawking_power()
    rs_km = dep.schwarzschild_radius() / 1000.0
    rs_m = dep.schwarzschild_radius()
    bh_vol = (4.0/3.0) * PI * rs_m**3 if rs_m > 0 else 0
    bh_density_val = dep.mass_kg / bh_vol if bh_vol > 0 else 0
    rs_disp = f"{rs_km:.4f} km" if rs_m >= 1000 else f"{rs_m:.3e} m"
    specs = [
        f"Mass: {dep.mass_kg:.3e} kg ({dep.mass_kg/M_SUN:.4f} M_sun)",
        f"Mass remaining: {mass_frac*100:.6f}%",
        f"Schwarzschild radius: {rs_disp}",
        f"BH density: {bh_density_val:.3e} kg/m^3",
        f"Harvests: {dep.harvest_count:.3e}",
        f"Years elapsed: {dep.years_elapsed:.3e} yr",
        f"Hawking temperature: {t_h:.3e} K",
        f"Hawking power: {p_h:.3e} W",
        f"Harvest rate: {dep.harvest_rate_per_yr:.1f}/yr ({N_SPHERES} spheres)",
        f"Mass/harvest: {MASS_PER_HARVEST:.0f} kg (E=mc^2)",
        f"Harvests to deplete: {HARVESTS_TO_DEPLETE:.2e}",
        f"Depletion time: {DEPLETE_YEARS:.2e} years",
    ]
    if dep.is_critical():
        specs.append("*** APPROACHING INSTABILITY ***")
        specs.append("Critical: mass < 1% of initial")
        specs.append("Hawking evaporation accelerating rapidly")
        specs.append("Jets intensifying, radiation peaking")
    else:
        specs.append(f"Stable: {DEPLETE_YEARS:.2e} yr to depletion at current rate")
    specs.append("Ergosphere: oblate, Kerr-like (1.3 Rs)")
    specs.append("Jets: intensify as Hawking radiation grows")
    specs.append("Doppler shift: blue (approaching) / red (receding)")
    specs.append("Gravitational lensing: photon paths bent near EH")

    return Part("depletion", "BH DEPLETION - HARVESTING", m, specs, 0, (0, 0, 0), C_BH_GLOW)


# =============================================================================
# SECTION 8 -- RENDERER
# =============================================================================

class BHHRenderer:
    """3D orbit-camera renderer with painter's algorithm + flat shading."""

    def __init__(self, parts, home=(0.5, 0.35, 4.0)):
        self.parts = parts
        self._home = home
        self.az, self.el, self.dist = home
        self.dist_target = self.dist
        self.pan = np.array([0.0, 0.0])
        self.light = np.array([0.4, 0.6, 1.0])
        self.light /= np.linalg.norm(self.light)
        self.show_labels = True
        self.exploded = False
        self.explode_amt = 0.0
        self.section = False
        self.hovered = None
        self.selected = None
        self.cull = True
        self.min_area = 12.0
        self.zoom_min = 0.1
        self.zoom_max = 100.0
        self.center = np.array([0.0, 0.0, 0.0])

    def reset_view(self):
        self.az, self.el, self.dist = self._home
        self.dist_target = self.dist
        self.pan = np.array([0.0, 0.0])

    def zoom(self, factor):
        self.dist_target = max(self.zoom_min, min(self.zoom_max, self.dist_target * factor))

    def orbit(self, dx, dy, fine=False):
        sens = 0.004 if fine else 0.009
        self.az += dx * sens
        self.el = max(-1.55, min(1.55, self.el + dy * sens))

    def pan_by(self, dx, dy, fine=False):
        sens = 0.45 if fine else 1.0
        self.pan += np.array([dx * sens, dy * sens])
        # Limit pan to reasonable range
        self.pan[0] = max(-5000, min(5000, self.pan[0]))
        self.pan[1] = max(-5000, min(5000, self.pan[1]))

    def tick(self, dt):
        target = 1.0 if self.exploded else 0.0
        self.explode_amt += (target - self.explode_amt) * min(1.0, dt * 4.0)
        self.dist += (self.dist_target - self.dist) * min(1.0, dt * 6.0)

    def active_part(self):
        i = self.selected if self.selected is not None else self.hovered
        return self.parts[i] if i is not None and i < len(self.parts) else None

    def render(self, surf, rect, angles, font=None, interactive=False, mouse_pos=None):
        clip = surf.get_clip()
        surf.set_clip(rect)
        cx = rect.x + rect.w / 2.0 + self.pan[0]
        cy = rect.y + rect.h / 2.0 + self.pan[1]
        focal = min(rect.w, rect.h) * 1.05
        Rcam = rot_x(self.el) @ rot_y(self.az)
        RcamT = Rcam.T
        lx, ly, lz = float(self.light[0]), float(self.light[1]), float(self.light[2])

        polys = []
        labels = []
        screeninfo = []
        _polys_append = polys.append

        _angles = angles
        _default_angle = angles.get("default", 0.0)
        _rot_cache = {}
        _explode_amt = self.explode_amt
        _has_explode = _explode_amt > 0.001
        for pi, part in enumerate(self.parts):
            off = part.explode * _explode_amt if _has_explode else None
            highlight = (pi == (self.selected if self.selected is not None else self.hovered))
            ol = (255, 210, 120) if highlight else (12, 14, 18)
            allcam = []
            for mesh in part.meshes:
                ang = _angles.get(mesh.group, _default_angle)
                if mesh._static_wv is not None:
                    wv = mesh._static_wv
                elif mesh.spin:
                    rk = (mesh.group, mesh.spin)
                    rot = _rot_cache.get(rk)
                    if rot is None:
                        rot = rot_z_T(ang * mesh.spin)
                        _rot_cache[rk] = rot
                    v = mesh.verts @ rot
                    if mesh._tilt_RT is not None:
                        v = v @ mesh._tilt_RT
                    wv = v + mesh.pivot
                elif mesh._tilt_RT is not None:
                    wv = mesh.verts @ mesh._tilt_RT + mesh.pivot
                else:
                    wv = mesh.verts + mesh.pivot
                if off is not None:
                    wv = wv + off
                cam = wv @ RcamT
                cam[:, 2] += self.dist
                allcam.append(cam)
                col = mesh._highlight_col if highlight else mesh._emissive_col
                cr, cg, cb = col
                ma = mesh.alpha
                z = cam[:, 2]
                safe = np.where(z > 0.05, z, 1e9)
                sx = cx + focal * cam[:, 0] / safe
                sy = cy - focal * cam[:, 1] / safe

                # Vectorized face processing
                # Triangles
                if len(mesh.idx3) > 0:
                    idx = mesh.idx3
                    tri = cam[idx]  # (nf, 3, 3)
                    a = tri[:, 0]; b = tri[:, 1]; c = tri[:, 2]
                    u = b - a
                    w = c - a
                    nx = u[:, 1] * w[:, 2] - u[:, 2] * w[:, 1]
                    ny = u[:, 2] * w[:, 0] - u[:, 0] * w[:, 2]
                    nz = u[:, 0] * w[:, 1] - u[:, 1] * w[:, 0]
                    inv = 1.0 / np.sqrt(nx*nx + ny*ny + nz*nz + 1e-30)
                    nx *= inv; ny *= inv; nz *= inv
                    flip = nz > 0
                    nx[flip] *= -1; ny[flip] *= -1; nz[flip] *= -1
                    zv = z[idx]  # (nf, 3)
                    face_z = (zv[:, 0] + zv[:, 1] + zv[:, 2]) / 3.0
                    vis = (zv[:, 0] > 0.05) & (zv[:, 1] > 0.05) & (zv[:, 2] > 0.05)
                    if self.cull:
                        vis &= nz < 0.01
                        # Area cull: skip tiny faces
                        sxy = sx[idx[:, :3]]  # only need 3 verts for tri area
                        syy = sy[idx[:, :3]]
                        area = np.abs((sxy[:, 1]-sxy[:, 0])*(syy[:, 2]-syy[:, 0]) - (sxy[:, 2]-sxy[:, 0])*(syy[:, 1]-syy[:, 0])) * 0.5
                        vis &= area >= self.min_area
                    if self.section:
                        wvf = wv[idx]  # (nf, 3, 3)
                        fy = (wvf[:, 0, 1] + wvf[:, 1, 1] + wvf[:, 2, 1]) / 3.0
                        vis &= fy <= 0
                    d = nx * lx + ny * ly + nz * lz
                    shade = 0.45 + 0.55 * np.maximum(0.0, d)
                    if mesh.emissive:
                        shade = np.maximum(shade, 0.90)
                    # Depth fog: darken distant faces for depth perception
                    fog_near = self.dist * 0.5
                    fog_far = self.dist * 3.0
                    fog = 1.0 - 0.20 * np.clip((face_z - fog_near) / (fog_far - fog_near + 1e-10), 0, 1)
                    shade = shade * fog
                    vi = np.where(vis)[0]
                    nv = len(vi)
                    if nv == 0:
                        continue
                    i0 = idx[vi, 0]; i1 = idx[vi, 1]; i2 = idx[vi, 2]
                    fz = face_z[vi]
                    sh = shade[vi]
                    crs = np.clip(cr * sh, 0, 255).astype(np.int16).tolist()
                    cgs = np.clip(cg * sh, 0, 255).astype(np.int16).tolist()
                    cbs = np.clip(cb * sh, 0, 255).astype(np.int16).tolist()
                    sx0 = sx[i0].astype(np.int32).tolist(); sy0 = sy[i0].astype(np.int32).tolist()
                    sx1 = sx[i1].astype(np.int32).tolist(); sy1 = sy[i1].astype(np.int32).tolist()
                    sx2 = sx[i2].astype(np.int32).tolist(); sy2 = sy[i2].astype(np.int32).tolist()
                    fz = fz.tolist()
                    for j in range(nv):
                        fc = (crs[j], cgs[j], cbs[j])
                        pts = [(sx0[j], sy0[j]), (sx1[j], sy1[j]), (sx2[j], sy2[j])]
                        _polys_append((fz[j], pts, fc, ol, ma))

                # Quads
                if len(mesh.idx4) > 0:
                    idx = mesh.idx4
                    quad = cam[idx]  # (nf, 4, 3)
                    a = quad[:, 0]; b = quad[:, 1]; c = quad[:, 2]
                    u = b - a
                    w = c - a
                    nx = u[:, 1] * w[:, 2] - u[:, 2] * w[:, 1]
                    ny = u[:, 2] * w[:, 0] - u[:, 0] * w[:, 2]
                    nz = u[:, 0] * w[:, 1] - u[:, 1] * w[:, 0]
                    inv = 1.0 / np.sqrt(nx*nx + ny*ny + nz*nz + 1e-30)
                    nx *= inv; ny *= inv; nz *= inv
                    flip = nz > 0
                    nx[flip] *= -1; ny[flip] *= -1; nz[flip] *= -1
                    zv = z[idx]  # (nf, 4)
                    face_z = (zv[:, 0] + zv[:, 1] + zv[:, 2] + zv[:, 3]) / 4.0
                    vis = (zv[:, 0] > 0.05) & (zv[:, 1] > 0.05) & (zv[:, 2] > 0.05) & (zv[:, 3] > 0.05)
                    if self.cull:
                        vis &= nz < 0.01
                        # Area cull: skip tiny faces (quad = sum of 2 triangles)
                        sxy4 = sx[idx]  # (nf, 4)
                        syy4 = sy[idx]
                        area1 = np.abs((sxy4[:, 1]-sxy4[:, 0])*(syy4[:, 2]-syy4[:, 0]) - (sxy4[:, 2]-sxy4[:, 0])*(syy4[:, 1]-syy4[:, 0])) * 0.5
                        area2 = np.abs((sxy4[:, 2]-sxy4[:, 0])*(syy4[:, 3]-syy4[:, 0]) - (sxy4[:, 3]-sxy4[:, 0])*(syy4[:, 2]-syy4[:, 0])) * 0.5
                        vis &= (area1 + area2) >= self.min_area
                    if self.section:
                        wvf = wv[idx]  # (nf, 4, 3)
                        fy = (wvf[:, 0, 1] + wvf[:, 1, 1] + wvf[:, 2, 1] + wvf[:, 3, 1]) / 4.0
                        vis &= fy <= 0
                    d = nx * lx + ny * ly + nz * lz
                    shade = 0.45 + 0.55 * np.maximum(0.0, d)
                    if mesh.emissive:
                        shade = np.maximum(shade, 0.90)
                    # Depth fog: darken distant faces for depth perception
                    fog_near = self.dist * 0.5
                    fog_far = self.dist * 3.0
                    fog = 1.0 - 0.20 * np.clip((face_z - fog_near) / (fog_far - fog_near + 1e-10), 0, 1)
                    shade = shade * fog
                    vi = np.where(vis)[0]
                    nv = len(vi)
                    if nv == 0:
                        continue
                    i0 = idx[vi, 0]; i1 = idx[vi, 1]; i2 = idx[vi, 2]; i3 = idx[vi, 3]
                    fz = face_z[vi]
                    sh = shade[vi]
                    crs = np.clip(cr * sh, 0, 255).astype(np.int16).tolist()
                    cgs = np.clip(cg * sh, 0, 255).astype(np.int16).tolist()
                    cbs = np.clip(cb * sh, 0, 255).astype(np.int16).tolist()
                    sx0 = sx[i0].astype(np.int32).tolist(); sy0 = sy[i0].astype(np.int32).tolist()
                    sx1 = sx[i1].astype(np.int32).tolist(); sy1 = sy[i1].astype(np.int32).tolist()
                    sx2 = sx[i2].astype(np.int32).tolist(); sy2 = sy[i2].astype(np.int32).tolist()
                    sx3 = sx[i3].astype(np.int32).tolist(); sy3 = sy[i3].astype(np.int32).tolist()
                    fz = fz.tolist()
                    for j in range(nv):
                        fc = (crs[j], cgs[j], cbs[j])
                        pts = [(sx0[j], sy0[j]), (sx1[j], sy1[j]), (sx2[j], sy2[j]), (sx3[j], sy3[j])]
                        _polys_append((fz[j], pts, fc, ol, ma))
            if not allcam:
                continue
            cam_all = np.vstack(allcam)
            cen = cam_all.mean(axis=0)
            if cen[2] > 0.05:
                safe_z = np.where(cam_all[:, 2] <= 0.05, 1e9, cam_all[:, 2])
                scx = cx + focal * cam_all[:, 0] / safe_z
                scy = cy - focal * cam_all[:, 1] / safe_z
                pcx = cx + focal * cen[0] / cen[2]
                pcy = cy - focal * cen[1] / cen[2]
                rad = float(np.max(np.hypot(scx - pcx, scy - pcy))) * 0.55 + 6
                screeninfo.append((pi, pcx, pcy, rad, cen[2]))
                if self.show_labels and font:
                    labels.append((cen[2], (pcx, pcy), part.name))

        # Paint far-to-near
        polys.sort(key=itemgetter(0), reverse=True)
        rx, ry, rw, rh = rect.x, rect.y, rect.w, rect.h
        rx2, ry2 = rx + rw, ry + rh
        # Approximate background color for alpha pre-mixing
        _bg = (15, 15, 30)
        for _, pts, fc, outline, ma in polys:
            try:
                # Clamp coordinates to prevent overflow/artifacts
                clamped = [(max(-32000, min(32000, p[0])),
                            max(-32000, min(32000, p[1]))) for p in pts]
                # Fast bounds check - skip entirely outside
                xs = [p[0] for p in clamped]
                ys = [p[1] for p in clamped]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                if max_x < rx or min_x >= rx2 or max_y < ry or min_y >= ry2:
                    continue
                if ma < 255:
                    # Pre-mix with approximate background for translucency
                    af = ma / 255.0
                    fc_blend = (int(fc[0] * af + _bg[0] * (1 - af)),
                                int(fc[1] * af + _bg[1] * (1 - af)),
                                int(fc[2] * af + _bg[2] * (1 - af)))
                    ol_blend = (int(outline[0] * af + _bg[0] * (1 - af)),
                                int(outline[1] * af + _bg[1] * (1 - af)),
                                int(outline[2] * af + _bg[2] * (1 - af)))
                    pygame.draw.polygon(surf, fc_blend, clamped)
                    pygame.draw.polygon(surf, ol_blend, clamped, 1)
                else:
                    pygame.draw.polygon(surf, fc, clamped)
                    pygame.draw.polygon(surf, outline, clamped, 1)
            except Exception:
                pass

        # Labels
        if self.show_labels and font:
            labels.sort(key=itemgetter(0))
            used = []
            for _, (lxp, lyp), text in labels:
                ly2 = lyp
                for uy in used:
                    if abs(ly2 - uy) < 15:
                        ly2 = uy + 15
                used.append(ly2)
                img = _render_text(font, text, C_TEXT)
                surf.blit(img, (lxp + 8, ly2))

        # Hover picking
        if interactive and mouse_pos is not None:
            mxp, myp = mouse_pos
            best, bestd = None, 1e18
            for pi, pcx, pcy, rad, depth in screeninfo:
                if math.hypot(mxp - pcx, myp - pcy) <= rad and depth < bestd:
                    bestd, best = depth, pi
            self.hovered = best if best is not None and best < len(self.parts) else None

        surf.set_clip(clip)


# =============================================================================
# SECTION 9 -- SIMULATION STATE
# =============================================================================

class SimState:
    """Tracks the orbital cycle simulation."""

    PHASES = ["Charging (EP)", "Outbound transit", "Harvesting (AP)", "Inbound return"]
    PHASE_DESC = [
        "String unreels into tidal gradient -> pull-to-rotation spins sphere to target RPM",
        "String retracts; sphere coasts at full RPM; gravity laser corrects orbital drift near EP",
        "Magnetic inductive coupling harvests spin energy -> 135 GW; rotation decelerates to 0 RPM",
        "Sphere coasts inbound at 0 RPM; gravity laser at AP restores EP for next cycle",
    ]

    def __init__(self):
        self.phase_bounds = compute_phase_bounds()
        self.t_frac = 0.0         # 0..1 fraction of orbital period
        self.speed = 0.05         # simulation speed (fraction per second)
        self.paused = False
        self.rpm = 0.0
        self.energy_j = 0.0
        self.string_ext = 0.0     # 0..1
        self.phase_idx = 0
        self.cycle_count = 0
        self.total_energy_harvested = 0.0
        self.disc_angle = 0.0     # for spin animation
        self.gyro_angle = 0.0
        self.laser_active = False
        self.harvest_power_w = 0.0
        self.orbit_drift_km = 0.0
        self.trail = []           # recent (x, z) positions for trail visualization
        self.trail_max = 60       # max trail points

    def update(self, dt):
        if not self.paused:
            self.t_frac += self.speed * dt
            if self.t_frac >= 1.0:
                self.t_frac -= 1.0
                self.cycle_count += 1
                self.total_energy_harvested += HARVEST_ENERGY_J
                self.orbit_drift_km += EP_DRIFT_KM

        # Determine phase
        if self.t_frac < self.phase_bounds[1]:
            self.phase_idx = 0    # Charging at EP
        elif self.t_frac < self.phase_bounds[2]:
            self.phase_idx = 1    # Outbound
        elif self.t_frac < self.phase_bounds[3]:
            self.phase_idx = 2    # Harvesting at AP
        else:
            self.phase_idx = 3    # Inbound

        # Charging: spin up sphere as string unreels
        if self.phase_idx == 0:
            charge_frac = self.t_frac / self.phase_bounds[1]
            self.string_ext = charge_frac
            self.rpm = SPHERE_RPM_TARGET * charge_frac
            self.energy_j = SPHERE_E_PWH * charge_frac
            self.laser_active = False
            self.harvest_power_w = 0.0
        elif self.phase_idx == 1:
            # Outbound: string retracts, RPM holds, laser corrects near EP
            out_frac = (self.t_frac - self.phase_bounds[1]) / (self.phase_bounds[2] - self.phase_bounds[1])
            self.string_ext = max(0.0, 1.0 - out_frac * 3.0)  # retract over first 1/3
            self.rpm = SPHERE_RPM_TARGET
            self.energy_j = SPHERE_E_PWH
            self.laser_active = (out_frac < 0.15)
            self.harvest_power_w = 0.0
        elif self.phase_idx == 2:
            # Harvesting: spin down to 0
            har_frac = (self.t_frac - self.phase_bounds[2]) / (self.phase_bounds[3] - self.phase_bounds[2])
            self.rpm = SPHERE_RPM_TARGET * (1.0 - har_frac)
            self.energy_j = SPHERE_E_PWH * (1.0 - har_frac)
            self.string_ext = 0.0
            self.laser_active = True
            self.harvest_power_w = harvest_power()
        else:
            # Inbound: coast at 0 RPM
            self.rpm = 0.0
            self.energy_j = 0.0
            self.string_ext = 0.0
            self.laser_active = False
            self.harvest_power_w = 0.0

        # Animation angles
        self.disc_angle += self.rpm * 2.0 * PI / 60.0 * dt
        self.gyro_angle += STATION_GYRO_RPM * 2.0 * PI / 60.0 * dt

        # Record trail point
        tx, tz, _ = orbital_position(self.t_frac)
        self.trail.append((tx, tz))
        if len(self.trail) > self.trail_max:
            self.trail.pop(0)

    def phase_name(self):
        return self.PHASES[self.phase_idx]

    def orbital_pos(self):
        return orbital_position(self.t_frac)

    def orbital_vel(self):
        return orbital_velocity(self.t_frac)


class DepletionState:
    """Simulates black hole depletion from harvesting over cosmic timescales.
    Shows mass loss, shrinking event horizon, rising Hawking temperature,
    and final explosion as the BH becomes unstable."""

    # Hawking constant: hbar c^3 / (8 pi G M k_B)
    # T_H = hbar c^3 / (8 pi G M k_B) ~ 6.17e-8 * M_sun / M  Kelvin
    HAWKING_T_CONST = 6.169e-8  # K * kg (for M_sun scale: T = const * M_sun / M)

    def __init__(self):
        self.mass_kg = float(BH_MASS_KG)
        self.initial_mass = float(BH_MASS_KG)
        self.harvest_count = 0
        self.years_elapsed = 0.0
        self.speed = max(1.0, DEPLETE_YEARS / 30.0)  # deplete in ~30 seconds
        self.paused = False
        self.exploded = False
        self.explosion_t = 0.0    # time since explosion started
        self.harvest_rate_per_yr = float(N_SPHERES) * 365.25  # N_SPHERES harvests/day * 365.25 days/yr
        self.disc_angle = 0.0
        self.particle_seed = 0    # for Hawking radiation animation

    def update(self, dt):
        if self.paused:
            return
        if not self.exploded:
            self.years_elapsed += self.speed * dt
            # Mass loss: each harvest removes MASS_PER_HARVEST kg
            n_harvests = int(self.years_elapsed * self.harvest_rate_per_yr)
            self.harvest_count = n_harvests
            self.mass_kg = self.initial_mass - n_harvests * MASS_PER_HARVEST
            # Instability: BH becomes unstable when mass drops below 0.1% of initial
            instability_threshold = self.initial_mass * 1e-3
            if self.mass_kg <= instability_threshold:
                self.exploded = True
                self.mass_kg = instability_threshold
                self.explosion_t = 0.0
        else:
            self.explosion_t += dt
            # Explosion grows then fades over ~10 seconds
        self.disc_angle += 0.5 * dt
        self.particle_seed += 1

    def schwarzschild_radius(self):
        if self.mass_kg <= 0:
            return 0
        return 2.0 * G * self.mass_kg / C**2

    def hawking_temperature(self):
        if self.mass_kg <= 0:
            return 0
        return self.HAWKING_T_CONST * M_SUN / self.mass_kg

    def hawking_power(self):
        """Total Hawking radiation power in Watts."""
        if self.mass_kg <= 0:
            return 0
        # P = hbar c^6 / (15360 pi G^2 M^2)
        hbar = 1.0546e-34
        return hbar * C**6 / (15360.0 * PI * G**2 * self.mass_kg**2)

    def mass_fraction(self):
        if self.initial_mass <= 0:
            return 0
        return self.mass_kg / self.initial_mass

    def is_critical(self):
        return self.mass_kg < self.initial_mass * 1e-2  # <1% of initial mass

    def explosion_progress(self):
        """0..1 progress of explosion animation."""
        if not self.exploded:
            return 0.0
        return min(1.0, self.explosion_t / 10.0)

    def reset(self):
        self.mass_kg = float(BH_MASS_KG)
        self.initial_mass = float(BH_MASS_KG)
        self.harvest_count = 0
        self.years_elapsed = 0.0
        self.speed = max(1.0, DEPLETE_YEARS / 30.0)
        self.exploded = False
        self.explosion_t = 0.0
        self.disc_angle = 0.0
        self.particle_seed = 0


# =============================================================================
# SECTION 10 -- UI HELPERS
# =============================================================================

_panel_cache = {}

def _panel(surf, x, y, w, h, alpha=220):
    key = (int(w), int(h), alpha)
    s = _panel_cache.get(key)
    if s is None:
        s = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
        s.fill((*C_PANEL, alpha))
        if len(_panel_cache) < 32:
            _panel_cache[key] = s
    surf.blit(s, (x, y))
    pygame.draw.rect(surf, (50, 60, 80), (x, y, w, h), 1)

_text_cache = {}
_text_cache_max = 512

def _render_text(font, text, color):
    key = (id(font), text, color)
    img = _text_cache.get(key)
    if img is not None:
        return img
    img = font.render(text, True, color)
    if len(_text_cache) < _text_cache_max:
        _text_cache[key] = img
    return img

_bg_cache = None
_bg_cache_key = None

def vgradient(surf, top, bot):
    global _bg_cache, _bg_cache_key
    w, h = surf.get_width(), surf.get_height()
    key = (w, h, top, bot)
    if _bg_cache is not None and _bg_cache_key == key:
        surf.blit(_bg_cache, (0, 0))
        return
    bg = pygame.Surface((w, h))
    arr = pygame.surfarray.pixels3d(bg)
    t = np.linspace(0.0, 1.0, h, dtype=np.float32).reshape(1, h, 1)
    top_a = np.array(top, dtype=np.float32).reshape(1, 1, 3)
    bot_a = np.array(bot, dtype=np.float32).reshape(1, 1, 3)
    arr[:] = (top_a + (bot_a - top_a) * t).astype(np.uint8)
    del arr
    # Add deterministic starfield with varied star colors and nebula tints
    rng = np.random.RandomState(42)
    # Subtle nebula clouds using vectorized numpy (fast)
    bg_arr = pygame.surfarray.pixels3d(bg).astype(np.int32)
    n_neb = 3
    neb_colors = [(20, 15, 40), (15, 25, 35), (25, 20, 30)]
    for ni in range(n_neb):
        nx = rng.randint(0, w)
        ny = rng.randint(0, h)
        nr = rng.randint(80, 200)
        ncol = neb_colors[ni]
        x0 = max(0, nx - nr)
        x1 = min(w, nx + nr)
        y0 = max(0, ny - nr)
        y1 = min(h, ny + nr)
        xs = np.arange(x0, x1).reshape(-1, 1)
        ys = np.arange(y0, y1).reshape(1, -1)
        dist = np.sqrt((xs - nx)**2 + (ys - ny)**2)
        mask = dist < nr
        alpha = (30 * (1.0 - dist / nr)).astype(np.int32)
        alpha = np.where(mask, alpha, 0)
        region = bg_arr[x0:x1, y0:y1]
        region[:, :, 0] = np.minimum(255, region[:, :, 0] + ncol[0] * alpha // 30)
        region[:, :, 1] = np.minimum(255, region[:, :, 1] + ncol[1] * alpha // 30)
        region[:, :, 2] = np.minimum(255, region[:, :, 2] + ncol[2] * alpha // 30)
    bg_arr_u8 = bg_arr.astype(np.uint8)
    del bg_arr
    arr2 = pygame.surfarray.pixels3d(bg)
    arr2[:] = bg_arr_u8
    del arr2
    # Stars with color variation (white, blue-white, yellow-white, red-white)
    n_stars = min(w * h // 2500, 500)
    star_colors = [
        (200, 200, 230),   # blue-white
        (230, 230, 255),   # white
        (255, 240, 200),   # yellow-white
        (255, 210, 190),   # red-white
        (200, 220, 255),   # pale blue
    ]
    for _ in range(n_stars):
        sx = rng.randint(0, w)
        sy = rng.randint(0, h)
        brightness = rng.randint(50, 220)
        col_base = star_colors[rng.randint(0, len(star_colors))]
        col = (min(255, col_base[0] * brightness // 200),
               min(255, col_base[1] * brightness // 200),
               min(255, col_base[2] * brightness // 200))
        sz = 1 if rng.random() > 0.12 else 2
        if sz == 1:
            bg.set_at((sx, sy), col)
        else:
            pygame.draw.circle(bg, col, (sx, sy), 1)
    _bg_cache = bg
    _bg_cache_key = key
    surf.blit(bg, (0, 0))


# =============================================================================
# SECTION 11 -- APPLICATION
# =============================================================================

class App:
    def __init__(self):
        pygame.init()
        self.W, self.H = 1600, 920
        self.win_w, self.win_h = 1600, 920
        self.window = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        self.screen = pygame.Surface((self.W, self.H))
        pygame.display.set_caption("BHH - Black Hole Energy Harvester")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 14)
        self.fsmall = pygame.font.SysFont("consolas", 12)
        self.fbig = pygame.font.SysFont("consolas", 28, bold=True)
        self.fmed = pygame.font.SysFont("consolas", 18, bold=True)
        self._recompute_viewport()

        self.mode = "overview"   # "overview" | "simulate" | "depletion" | "systems" | "custom"
        self.systems = list(PRESET_SYSTEMS)
        self.system_idx = 0
        self.current_system = self.systems[0]
        self.sim = SimState()
        self.dep = DepletionState()
        self.show_info = False
        self.show_help = False
        self.show_labels = True
        self.drag = None
        self.last_mouse = (0, 0)
        self._mouse_down_pos = None
        self.status = ""
        self.status_t = 0.0
        self._custom_surf = None
        self._systems_surf = None
        # Custom build parameters
        self.custom_params = {
            'bh_mass_msun': 10.0,
            'orbit_ep_au': 2.0,
            'orbit_ap_au': 8.0,
            'sphere_mass_kg': 3e11,
            'sphere_rpm_target': 200,
            'string_diam_m': 0.05,
            'n_spheres': 1095,
        }
        self.custom_param_keys = list(self.custom_params.keys())
        self.custom_edit_idx = 0

        # Build parts
        self.parts = self._build_all()
        self.renderer = BHHRenderer(self.parts, home=(0.5, 0.35, CAMERA_HOME_DIST))
        # Cache sphere part and original pivots for simulate mode
        self._sphere_cache = None
        self._sphere_pivots = None
        self._string_cache = None
        self._string_cache_ext = -1.0
        self._laser_cache = None
        self._laser_cache_t = -1.0
        self._info_surf = None
        self._help_surf = None

    def _build_all(self):
        parts = []
        parts.append(build_black_hole())
        parts.append(build_orbit())
        parts.append(build_station())
        parts.append(build_gravity_laser(0.0))
        parts.append(build_constellation())
        # Sample sphere at a representative position on the orbit (near EP)
        # Simplified version for overview (just body + Halbach equator)
        r = SPHERE_DISP_R
        sample_m = []
        v, f = _sph(r, 12, 8)
        sample_m.append(Mesh(v, f, C_SPHERE, "Sample sphere", spin=1.0, group="sphere"))
        # Halbach ring
        n_mag = 12
        hal_v, hal_f = [], []
        for j in range(n_mag):
            ma = 2 * PI * j / n_mag
            mx = r * 0.85 * math.cos(ma)
            my = r * 0.85 * math.sin(ma)
            v, f = _box(mx, my, 0, r*0.08, r*0.08, r*0.15)
            base = len(hal_v)
            for vv in v:
                hal_v.append(vv)
            for ff in f:
                hal_f.append(tuple(idx + base for idx in ff))
        if hal_v:
            sample_m.append(Mesh(hal_v, hal_f, C_HALBACH, "Sample Halbach", spin=1.0, group="sphere"))
        sample_sphere = Part("sample_sphere", "SAMPLE SPHERE", sample_m, [], 6, (0,0,0), C_SPHERE)
        sx, sz, _ = orbital_position(0.02)
        for mesh in sample_sphere.meshes:
            mesh.pivot = mesh.pivot + np.array([sx, 0, sz])
            if mesh._static_wv is not None:
                mesh._static_wv = mesh.verts + mesh.pivot
        parts.append(sample_sphere)
        # Sample string (simplified: just shaft + tip)
        r_sphere = SPHERE_DISP_R
        max_len = STRING_LENGTH_M * DS * STRING_DISP_SCALE
        cur_len = max_len * 0.3
        if cur_len < 0.001:
            cur_len = 0.001
        str_r = max(0.003, STRING_DIAM_M * DS * STRING_DISP_SCALE * 10)
        tip_r = max(0.01, STRING_TIP_R_M * DS * STRING_DISP_SCALE * 10)
        string_m = []
        v, f = _cyl(str_r, cur_len, 0, 8)
        string_m.append(Mesh(v, f, C_STRING, "Sample string shaft"))
        v, f = _sph(tip_r, 8, 6)
        string_m.append(Mesh(v, f, C_TIP, "Sample string tip",
                              pivot=(-cur_len, 0, 0)))
        sample_string = Part("sample_string", "SAMPLE STRING", string_m, [], 6, (0,0,0), C_STRING)
        bh_angle = math.atan2(-sz, sx)
        Ry = rot_y(bh_angle)
        offset = np.array([sx, 0, sz])
        for mesh in sample_string.meshes:
            mesh.pivot = Ry @ mesh.pivot + offset
            mesh._static_wv = mesh.verts + mesh.pivot
        parts.append(sample_string)
        return parts

    def _apply_system(self, cfg):
        """Update global constants from a SystemConfig and rebuild all parts."""
        global BH_MASS_KG, BH_RS, BH_RPH, BH_RISCO, BH_DIST_LY
        global SPHERE_MASS_KG, SPHERE_DENSITY, SPHERE_RADIUS_M, SPHERE_TENSILE_PA
        global SPHERE_RPM_MAX, SPHERE_RPM_TARGET, SPHERE_OMEGA_MAX, SPHERE_OMEGA_TGT
        global SPHERE_I, SPHERE_E_PWH, SPHERE_E_MAX, SPHERE_E_OPER
        global ORBIT_EP_AU, ORBIT_AP_AU, ORBIT_EP_M, ORBIT_AP_M, ORBIT_A_M, ORBIT_E, ORBIT_B_M
        global ORBIT_PERIOD_S, ORBIT_PERIOD_YR, ORBIT_V_EP, ORBIT_V_AP
        global STRING_DIAM_M, STRING_R_M, STRING_T_MAX, STRING_LENGTH_M, STRING_LENGTH_MI
        global STRING_TIP_MASS, STRING_TIP_R_M
        global DRUM_RADIUS_M, CLUTCH_TENSION, HALBACH_FREQ_HZ
        global STATION_MASS_KG
        global N_SPHERES, MASS_PER_HARVEST, HARVESTS_TO_DEPLETE, DEPLETE_YEARS
        global HARVEST_ENERGY_J, HARVEST_POWER_W, STATION_POWER_GW, STATION_HARVEST_S
        global DS
        global CURRENT_SYSTEM_NAME
        global HOMES_POWERED
        global EP_DRIFT_KM
        global ORBIT_MAX_DS, SCENE_R, BH_DISP_R, SPHERE_DISP_R, STATION_DISP_S, STRING_DISP_SCALE, CAMERA_HOME_DIST

        self.current_system = cfg
        CURRENT_SYSTEM_NAME = cfg.name

        # BH
        BH_MASS_KG = cfg.bh_mass_kg
        BH_RS = cfg.bh_rs
        BH_RPH = cfg.bh_rph
        BH_RISCO = cfg.bh_risco
        BH_DIST_LY = cfg.bh_dist_ly

        # Sphere
        SPHERE_MASS_KG = cfg.sphere_mass_kg
        SPHERE_DENSITY = cfg.sphere_density
        SPHERE_RADIUS_M = cfg.sphere_radius_m
        SPHERE_TENSILE_PA = 1.30e11
        SPHERE_RPM_MAX = cfg.sphere_rpm_max
        SPHERE_RPM_TARGET = cfg.sphere_rpm_target
        SPHERE_OMEGA_MAX = cfg.sphere_omega_max
        SPHERE_OMEGA_TGT = cfg.sphere_omega_tgt
        SPHERE_I = cfg.sphere_i
        SPHERE_E_PWH = cfg.sphere_e_pwh
        SPHERE_E_MAX = cfg.sphere_e_max
        SPHERE_E_OPER = cfg.sphere_e_oper

        # Orbit
        ORBIT_EP_AU = cfg.orbit_ep_au
        ORBIT_AP_AU = cfg.orbit_ap_au
        ORBIT_EP_M = cfg.orbit_ep_m
        ORBIT_AP_M = cfg.orbit_ap_m
        ORBIT_A_M = cfg.orbit_a_m
        ORBIT_E = cfg.orbit_e
        ORBIT_B_M = cfg.orbit_b_m
        ORBIT_PERIOD_S = cfg.orbit_period_s
        ORBIT_PERIOD_YR = cfg.orbit_period_yr
        ORBIT_V_EP = cfg.orbit_v_ep
        ORBIT_V_AP = cfg.orbit_v_ap

        # String
        STRING_DIAM_M = cfg.string_diam_m
        STRING_R_M = cfg.string_r_m
        STRING_T_MAX = cfg.string_t_max
        STRING_LENGTH_M = cfg.string_length_m
        STRING_LENGTH_MI = cfg.string_length_m / 1609.344
        STRING_TIP_MASS = cfg.string_tip_mass_kg
        STRING_TIP_R_M = cfg.string_tip_r_m

        # Derived
        DRUM_RADIUS_M = SPHERE_RADIUS_M * 0.3
        CLUTCH_TENSION = STRING_T_MAX
        HALBACH_FREQ_HZ = SPHERE_RPM_TARGET / 60.0
        STATION_MASS_KG = cfg.station_mass_kg

        # Constellation
        N_SPHERES = cfg.n_spheres
        MASS_PER_HARVEST = cfg.mass_per_harvest
        HARVESTS_TO_DEPLETE = cfg.harvests_to_deplete
        DEPLETE_YEARS = cfg.deplete_years
        HARVEST_ENERGY_J = SPHERE_E_PWH * STATION_EFFICIENCY

        # Recompute harvest power: E_spin / harvest_window
        # harvest_window = fraction of period near AP * orbital period
        pb = compute_phase_bounds()
        harvest_frac = pb[3] - pb[2]
        if harvest_frac > 0 and ORBIT_PERIOD_S > 0:
            harvest_window_s = harvest_frac * ORBIT_PERIOD_S
            HARVEST_POWER_W = SPHERE_E_PWH / harvest_window_s
            STATION_POWER_GW = HARVEST_POWER_W / 1e9
            STATION_HARVEST_S = harvest_window_s
        else:
            HARVEST_POWER_W = STATION_POWER_GW * 1e9
        HOMES_POWERED = int(N_SPHERES * SPHERE_E_PWH / 3.6e10) if SPHERE_E_PWH > 0 else 0

        # Display scale
        DS = cfg.ds

        # Scene scale: all components sized relative to orbit for visibility
        ORBIT_MAX_DS = max(ORBIT_EP_M, ORBIT_AP_M) * DS
        SCENE_R = max(ORBIT_MAX_DS, 0.1)
        BH_DISP_R = SCENE_R * 0.04
        SPHERE_DISP_R = SCENE_R * 0.015
        STATION_DISP_S = SCENE_R * 0.025
        STRING_DISP_SCALE = SCENE_R * 0.08 / max(STRING_LENGTH_M * DS, 1e-12)
        CAMERA_HOME_DIST = SCENE_R * 1.5

        # Homes powered (assume avg 10,000 kWh/home/year = 3.6e10 J)
        annual_energy_j = N_SPHERES * SPHERE_E_PWH
        HOMES_POWERED = int(annual_energy_j / 3.6e10) if annual_energy_j > 0 else 0

        # EP drift per cycle (scales with string energy vs orbital momentum)
        # Base: 0.0001 km for Gaia BH1 reference; scale by ratio
        orbital_momentum = SPHERE_MASS_KG * ORBIT_V_EP
        if orbital_momentum > 0 and STRING_T_MAX > 0:
            EP_DRIFT_KM = 0.0001 * (SPHERE_E_PWH / (orbital_momentum * 1000.0)) / (3.6e18 / (2.77e11 * 29000.0))
            if EP_DRIFT_KM < 1e-8:
                EP_DRIFT_KM = 1e-8
        else:
            EP_DRIFT_KM = 0.0001

        # Rebuild parts
        self.parts = self._build_all()
        self.renderer.parts = self.parts
        self.renderer._home = (0.5, 0.35, CAMERA_HOME_DIST)
        self.renderer.reset_view()

        # Reset caches
        self._sphere_cache = None
        self._sphere_pivots = None
        self._string_cache = None
        self._string_cache_ext = -1.0
        self._laser_cache = None
        self._laser_cache_t = -1.0
        self._info_surf = None
        self._help_surf = None

        # Reset simulation state
        self.sim = SimState()
        self.dep = DepletionState()

    def _recompute_viewport(self):
        scale = min(self.win_w / self.W, self.win_h / self.H)
        vw, vh = self.W * scale, self.H * scale
        vx, vy = (self.win_w - vw) / 2.0, (self.win_h - vh) / 2.0
        self._vp = (vx, vy, vw, vh, scale)

    def _to_canvas(self, pos):
        vx, vy, vw, vh, scale = self._vp
        return ((pos[0] - vx) / scale, (pos[1] - vy) / scale)

    def _flash(self, msg):
        self.status = msg
        self.status_t = 2.5

    def _active_parts(self):
        """Parts list for current mode (includes dynamic sphere/string in sim mode)."""
        if self.mode == "depletion":
            return [build_depletion_scene(self.dep)]
        if self.mode in ("systems", "custom"):
            return []
        parts = list(self.parts)
        if self.mode == "simulate":
            # Exclude sample sphere/string (last 2 parts) in simulate mode
            parts = parts[:-2]
            sx, sz, r = self.sim.orbital_pos()
            # Cache sphere part (geometry doesn't change, only position)
            if self._sphere_cache is None:
                self._sphere_cache = build_sphere()
                self._sphere_pivots = [mesh.pivot.copy() for mesh in self._sphere_cache.meshes]
            for i, mesh in enumerate(self._sphere_cache.meshes):
                mesh.pivot = self._sphere_pivots[i] + np.array([sx, 0, sz])
                mesh._static_wv = None
            parts.append(self._sphere_cache)
            # String geometry changes with extension - cache when ext hasn't changed
            ext = self.sim.string_ext
            if self._string_cache is None or abs(ext - self._string_cache_ext) > 0.001:
                self._string_cache = build_string(ext)
                self._string_cache_ext = ext
                self._string_pivots = [m.pivot.copy() for m in self._string_cache.meshes]
                self._string_tilts = [m._tilt_RT.copy() if m._tilt_RT is not None else None for m in self._string_cache.meshes]
            string_part = self._string_cache
            bh_angle = math.atan2(-sz, sx)
            Ry = rot_y(bh_angle)
            RyT = Ry.T
            offset = np.array([sx, 0, sz])
            for i, mesh in enumerate(string_part.meshes):
                mesh.pivot = Ry @ self._string_pivots[i] + offset
                orig_tilt = self._string_tilts[i]
                if orig_tilt is not None:
                    mesh._tilt_RT = orig_tilt @ RyT
                else:
                    mesh._tilt_RT = RyT.copy()
                mesh._static_wv = None
            parts.append(string_part)
            # Laser visibility changes with phase - cache by t_frac
            tf = self.sim.t_frac
            if self._laser_cache is None or abs(tf - self._laser_cache_t) > 0.01:
                self._laser_cache = build_gravity_laser(tf)
                self._laser_cache_t = tf
            parts.append(self._laser_cache)
            # Energy flow effects (charging glow, harvest beam, laser impact)
            effects = build_energy_effects(self.sim)
            if effects is not None:
                parts.append(effects)
            # Orbital trail
            trail = build_trail(self.sim)
            if trail is not None:
                parts.append(trail)
        return parts

    def handle_events(self, dt):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.VIDEORESIZE:
                self.win_w, self.win_h = max(800, e.w), max(600, e.h)
                self.window = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
                self._recompute_viewport()
            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = self._to_canvas(e.pos)
                if e.button == 1:
                    self.drag = "orbit"
                    self._mouse_down_pos = pos
                elif e.button in (2, 3):
                    self.drag = "pan"
                elif e.button == 4:
                    self.renderer.zoom(0.9)
                elif e.button == 5:
                    self.renderer.zoom(1.1)
                self.last_mouse = pos
            if e.type == pygame.MOUSEBUTTONUP and e.button in (1, 2, 3):
                # Click-to-select: if left button released with minimal movement
                if e.button == 1 and self._mouse_down_pos is not None:
                    pos = self._to_canvas(e.pos)
                    dx = pos[0] - self._mouse_down_pos[0]
                    dy = pos[1] - self._mouse_down_pos[1]
                    if abs(dx) < 5 and abs(dy) < 5:
                        self.renderer.selected = self.renderer.hovered
                        if self.renderer.selected is not None:
                            part = self.renderer.active_part()
                            if part:
                                self._flash(f"Selected: {part.name}")
                    self._mouse_down_pos = None
                self.drag = None
            if e.type == pygame.MOUSEMOTION and self.drag:
                mc = self._to_canvas(e.pos)
                dx = mc[0] - self.last_mouse[0]
                dy = mc[1] - self.last_mouse[1]
                fine = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if self.drag == "orbit":
                    self.renderer.orbit(dx, dy, fine)
                else:
                    self.renderer.pan_by(dx, dy)
                self.last_mouse = mc
            if e.type == pygame.KEYDOWN:
                if not self._key(e.key):
                    return False
        return True

    def _adjust_param(self, key, direction):
        """Adjust a custom parameter by one step in given direction."""
        val = self.custom_params[key]
        if key == 'bh_mass_msun':
            return max(0.1, val * (1.5 if direction > 0 else 1/1.5))
        if key == 'orbit_ep_au':
            return max(0.01, val * (1.3 if direction > 0 else 1/1.3))
        if key == 'orbit_ap_au':
            return max(0.1, val * (1.3 if direction > 0 else 1/1.3))
        if key == 'sphere_mass_kg':
            return max(1e3, val * (2.0 if direction > 0 else 0.5))
        if key == 'sphere_rpm_target':
            return max(1, val + (10 if direction > 0 else -10))
        if key == 'string_diam_m':
            return max(0.001, val * (1.5 if direction > 0 else 1/1.5))
        if key == 'n_spheres':
            return max(1, int(val + (100 if direction > 0 else -100)))
        return val

    def _apply_custom_config(self):
        """Build a custom SystemConfig from current params and switch to it."""
        p = self.custom_params
        cfg = create_custom_config(
            bh_mass_msun=p['bh_mass_msun'],
            orbit_ep_au=p['orbit_ep_au'],
            orbit_ap_au=p['orbit_ap_au'],
            sphere_mass_kg=p['sphere_mass_kg'],
            sphere_rpm_target=p['sphere_rpm_target'],
            string_diam_m=p['string_diam_m'],
            n_spheres=int(p['n_spheres']),
        )
        # Replace custom in systems list or add it
        if len(self.systems) > len(PRESET_SYSTEMS):
            self.systems[len(PRESET_SYSTEMS)] = cfg
        else:
            self.systems.append(cfg)
        self.system_idx = len(self.systems) - 1
        self._apply_system(cfg)
        self.mode = "overview"
        self._flash(f"Custom system applied: {cfg.name}")
        self._custom_surf = None

    def _key(self, k):
        if k == pygame.K_ESCAPE:
            if self.show_info:
                self.show_info = False
                return True
            if self.show_help:
                self.show_help = False
                return True
            return False
        if k == pygame.K_TAB:
            modes = ["overview", "simulate", "depletion", "systems", "custom"]
            idx = modes.index(self.mode) if self.mode in modes else 0
            self.mode = modes[(idx + 1) % len(modes)]
            self._flash(f"Mode: {self.mode.upper()}")
            return True
        if k == pygame.K_s:
            self.mode = "systems"
            self._flash("Mode: SYSTEMS")
            return True
        if k == pygame.K_c:
            self.mode = "custom"
            self._flash("Mode: CUSTOM BUILD")
            return True
        # ENTER in systems mode -> go to overview of selected system
        if k == pygame.K_RETURN or k == pygame.K_KP_ENTER:
            if self.mode == "systems":
                self._apply_system(self.systems[self.system_idx])
                self.mode = "overview"
                self._flash(f"Viewing: {self.current_system.name}")
                return True
        # Number keys 1-5 select preset system
        if pygame.K_1 <= k <= pygame.K_9:
            idx = k - pygame.K_1
            if idx < len(self.systems):
                self.system_idx = idx
                self._apply_system(self.systems[idx])
                self._flash(f"System: {self.current_system.name}")
                return True
        # Up/Down to navigate custom params
        if self.mode == "custom":
            if k == pygame.K_UP:
                self.custom_edit_idx = (self.custom_edit_idx - 1) % len(self.custom_param_keys)
                return True
            if k == pygame.K_DOWN:
                self.custom_edit_idx = (self.custom_edit_idx + 1) % len(self.custom_param_keys)
                return True
            if k == pygame.K_LEFT:
                key = self.custom_param_keys[self.custom_edit_idx]
                self.custom_params[key] = self._adjust_param(key, -1)
                return True
            if k == pygame.K_RIGHT:
                key = self.custom_param_keys[self.custom_edit_idx]
                self.custom_params[key] = self._adjust_param(key, 1)
                return True
            if k == pygame.K_RETURN or k == pygame.K_KP_ENTER:
                self._apply_custom_config()
                return True
        if k == pygame.K_i:
            self.show_info = not self.show_info
            return True
        if k == pygame.K_h:
            self.show_help = not self.show_help
            return True
        if k == pygame.K_l:
            self.show_labels = not self.show_labels
            self.renderer.show_labels = self.show_labels
            self._flash("Labels " + ("ON" if self.show_labels else "OFF"))
            return True
        if k == pygame.K_r:
            self.renderer.reset_view()
            self._flash("View reset")
            return True
        if k == pygame.K_p:
            if self.mode == "depletion":
                self.dep.paused = not self.dep.paused
                self._flash("Depletion " + ("PAUSED" if self.dep.paused else "RUNNING"))
            else:
                self.sim.paused = not self.sim.paused
                self._flash("Simulation " + ("PAUSED" if self.sim.paused else "RUNNING"))
            return True
        if k == pygame.K_SPACE:
            if self.mode == "depletion":
                self.dep.reset()
                self._flash("Depletion reset")
                return True
            # Advance to next phase
            bounds = self.sim.phase_bounds
            for b in bounds:
                if self.sim.t_frac < b:
                    self.sim.t_frac = b
                    break
            else:
                self.sim.t_frac = 0.0
            self._flash(f"Jumped to: {self.sim.phase_name()}")
            return True
        if k == pygame.K_EQUALS or k == pygame.K_PLUS:
            if self.mode == "depletion":
                self.dep.speed = min(1e20, self.dep.speed * 10.0)
                self._flash(f"Depletion speed: {self.dep.speed:.1e} yr/s")
            else:
                self.sim.speed = min(1.0, self.sim.speed * 1.5)
                self._flash(f"Sim speed: {self.sim.speed:.3f}")
            return True
        if k == pygame.K_MINUS:
            if self.mode == "depletion":
                self.dep.speed = max(0.1, self.dep.speed / 10.0)
                self._flash(f"Depletion speed: {self.dep.speed:.1e} yr/s")
            else:
                self.sim.speed = max(0.001, self.sim.speed / 1.5)
                self._flash(f"Sim speed: {self.sim.speed:.3f}")
            return True
        if k == pygame.K_e:
            self.renderer.exploded = not self.renderer.exploded
            self._flash("Exploded view " + ("ON" if self.renderer.exploded else "OFF"))
            return True
        if k == pygame.K_x:
            self.renderer.section = not self.renderer.section
            self._flash("Section cut " + ("ON" if self.renderer.section else "OFF"))
            return True
        return True

    def update(self, dt):
        self.sim.update(dt)
        self.dep.update(dt)
        self.renderer.tick(dt)
        if self.status_t > 0:
            self.status_t -= dt

    def draw(self):
        surf = self.screen
        vgradient(surf, C_BG_TOP, C_BG_BOT)

        rect = pygame.Rect(0, 0, self.W, self.H)
        parts = self._active_parts()

        if self.mode == "depletion":
            angles = {"default": 0.0, "bh": 0.0, "bh_disk": self.dep.disc_angle}
        else:
            angles = {"default": 0.0, "sphere": self.sim.disc_angle,
                      "drum": self.sim.disc_angle * 0.5,
                      "shaft": self.sim.disc_angle * 0.3,
                      "gear": self.sim.disc_angle * 0.2,
                      "gyro": self.sim.gyro_angle,
                      "bh": 0.0, "bh_disk": self.sim.t_frac * 2.0}

        # Temporarily set renderer parts
        old_parts = self.renderer.parts
        self.renderer.parts = parts
        mpos = self._to_canvas(pygame.mouse.get_pos())
        self.renderer.render(surf, rect, angles, font=self.font,
                             interactive=True, mouse_pos=mpos)
        self.renderer.parts = old_parts

        # HUD
        if self.mode == "depletion":
            self._draw_depletion_hud()
        elif self.mode == "systems":
            self._draw_systems_hud()
        elif self.mode == "custom":
            self._draw_custom_hud()
        else:
            self._draw_hud()

        if self.show_info:
            self._draw_info()
        if self.show_help:
            self._draw_help()

        if self.status_t > 0:
            img = _render_text(self.fmed, self.status, C_WARN)
            surf.blit(img, (self.W // 2 - img.get_width() // 2, self.H - 50))

        # Present
        vx, vy, vw, vh, scale = self._vp
        self.window.fill((0, 0, 0))
        if abs(scale - 1.0) < 0.01:
            self.window.blit(surf, (int(vx), int(vy)))
        else:
            self.window.blit(pygame.transform.smoothscale(surf, (int(vw), int(vh))),
                             (int(vx), int(vy)))
        pygame.display.flip()

    def _draw_hud(self):
        surf = self.screen
        # Top bar
        _panel(surf, 0, 0, self.W, 32, alpha=200)
        # System color accent bar
        pygame.draw.rect(surf, self.current_system.color_accent, (0, 0, self.W, 3))
        title = f"BHH - {self.current_system.name}"
        if self.mode == "simulate":
            title += f"  |  SIMULATE  |  Phase: {self.sim.phase_name()}  |  Cycle: {self.sim.cycle_count}"
        else:
            title += "  |  OVERVIEW"
        surf.blit(_render_text(self.font, title, self.current_system.color_accent), (12, 8))

        if self.mode == "simulate":
            self._draw_phase_bar(surf)
            # Phase description
            desc = SimState.PHASE_DESC[self.sim.phase_idx]
            desc_surf = _render_text(self.fsmall, desc, C_DIM)
            dx = self.W // 2 - desc_surf.get_width() // 2
            surf.blit(desc_surf, (dx, 56))
        elif self.mode == "overview":
            # Component legend in overview mode
            legend_y = 40
            _panel(surf, self.W // 2 - 200, legend_y, 400, 28, alpha=200)
            legend = "OVERVIEW - Click parts to inspect | TAB to simulate | I for info"
            ls = _render_text(self.fsmall, legend, C_DIM)
            surf.blit(ls, (self.W // 2 - ls.get_width() // 2, legend_y + 8))

        # Right panel: live stats (simulate) or system specs (overview)
        px = self.W - 290
        py = 40
        _panel(surf, px, py, 280, 340, alpha=220)
        # System color accent bar
        pygame.draw.rect(surf, self.current_system.color_accent, (px, py, 280, 3))
        surf.blit(_render_text(self.fsmall, f"SYSTEM: {self.current_system.name}", self.current_system.color_accent), (px+8, py+6))
        yy = py + 24
        if self.mode == "overview":
            stats = [
                f"Mode: OVERVIEW",
                f"System: {self.current_system.name}",
                "",
                f"BH mass: {BH_MASS_KG/M_SUN:.2f} M_sun",
                f"Rs: {BH_RS/1000:.2f} km" if BH_RS >= 1000 else f"Rs: {BH_RS:.3e} m",
                f"EP: {ORBIT_EP_AU:.2f} AU",
                f"AP: {ORBIT_AP_AU:.2f} AU",
                f"Ecc: {ORBIT_E:.3f}",
                f"Period: {ORBIT_PERIOD_YR:.1f} yr",
                "",
                f"Sphere: {SPHERE_MASS_KG:.1e} kg",
                f"  R: {SPHERE_RADIUS_M:.0f} m",
                f"  RPM: {SPHERE_RPM_TARGET:.0f}",
                f"Energy: {SPHERE_E_PWH/3.6e18:.2f} PWh",
                f"Spheres: {N_SPHERES}",
                "",
                f"Depletion: {DEPLETE_YEARS:.1e} yr",
                f"Distance: {BH_DIST_LY:.0f} ly",
                "",
                "Click parts to inspect",
                "TAB to simulate | I for info",
            ]
        else:
            stats = [
                f"Mode: SIMULATE",
                f"Phase: {self.sim.phase_name()}",
                f"Orbit fraction: {self.sim.t_frac:.3f}",
                f"Period: {ORBIT_PERIOD_YR:.1f} years",
                f"Sim speed: {self.sim.speed:.4f}x",
                "",
                f"Sphere RPM: {self.sim.rpm:.1f} / {SPHERE_RPM_TARGET:.0f}",
                f"Energy stored: {self.sim.energy_j:.2e} J",
                f"  = {self.sim.energy_j/3.6e18:.3f} PWh",
                f"String extension: {self.sim.string_ext*100:.1f}%",
                "",
                f"Harvest power: {self.sim.harvest_power_w/1e9:.2f} GW",
                f"Laser: {'ACTIVE' if self.sim.laser_active else 'OFF'}",
                f"Total harvested: {self.sim.total_energy_harvested/3.6e18:.1f} PWh",
                f"Orbit drift: {self.sim.orbit_drift_km:.4f} km",
            ]
        for s in stats:
            col = C_GOOD if "ACTIVE" in s and "Laser" in s else C_TEXT
            if s == "":
                yy += 6
            else:
                surf.blit(_render_text(self.fsmall, s, col), (px+8, yy))
                yy += 16

        # RPM gauge bar (simulate only)
        if self.mode == "simulate":
            bar_y = py + 340 - 70
            surf.blit(_render_text(self.fsmall, "RPM", C_DIM), (px+8, bar_y))
            rpm_frac = self.sim.rpm / SPHERE_RPM_MAX if SPHERE_RPM_MAX > 0 else 0
            rpm_frac = max(0.0, min(1.0, rpm_frac))
            bar_w = 264
            bar_x = px + 8
            pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y + 14, bar_w, 8))
            fill_w = int(bar_w * rpm_frac)
            rpm_col = C_GOOD if rpm_frac < 0.95 else C_WARN
            if fill_w > 0:
                pygame.draw.rect(surf, rpm_col, (bar_x, bar_y + 14, fill_w, 8))
            # Target RPM marker (95% of max)
            target_x = bar_x + int(bar_w * (SPHERE_RPM_TARGET / SPHERE_RPM_MAX))
            pygame.draw.line(surf, C_ACCENT, (target_x, bar_y + 12), (target_x, bar_y + 22), 1)

            # Energy gauge bar
            bar_y2 = bar_y + 28
            surf.blit(_render_text(self.fsmall, "ENERGY (PWh)", C_DIM), (px+8, bar_y2))
            e_frac = self.sim.energy_j / SPHERE_E_PWH if SPHERE_E_PWH > 0 else 0
            e_frac = max(0.0, min(1.0, e_frac))
            pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y2 + 14, bar_w, 8))
            fill_w2 = int(bar_w * e_frac)
            e_col = C_PHASE3 if e_frac > 0.01 else C_DIM
            if fill_w2 > 0:
                pygame.draw.rect(surf, e_col, (bar_x, bar_y2 + 14, fill_w2, 8))

        # Left panel: orbital info + component status (simulate only)
        lx = 12
        ly = 40
        if self.mode == "simulate":
            _panel(surf, lx, ly, 260, 200, alpha=220)
            surf.blit(_render_text(self.fsmall, "ORBITAL PARAMETERS", C_ACCENT), (lx+8, ly+6))
            sx, sz, r = self.sim.orbital_pos()
            v = self.sim.orbital_vel()
            yy = ly + 24
            ostats = [
                f"EP: {ORBIT_EP_AU:.2f} AU",
                f"AP: {ORBIT_AP_AU:.2f} AU",
                f"Eccentricity: {ORBIT_E:.3f}",
                f"Current r: {r/AU_M:.3f} AU",
                f"Current v: {v/1000:.2f} km/s",
                f"Gravity at r: {gravity_at_distance(r):.2e} m/s^2",
                f"Position: ({sx:.3f}, {sz:.3f}) AU",
            ]
            for s in ostats:
                surf.blit(_render_text(self.fsmall, s, C_TEXT), (lx+8, yy))
                yy += 16

            # Component status panel (below orbital info)
            cy = ly + 210
            _panel(surf, lx, cy, 260, 170, alpha=220)
            surf.blit(_render_text(self.fsmall, "COMPONENT STATUS", C_ACCENT), (lx+8, cy+6))
            yy = cy + 24
            # Determine component states based on phase
            if self.sim.phase_idx == 0:
                flywheel_st = "COUNTER-ROTATING"
                cooling_st = "STANDBY"
                laser_st = "OFF"
                gyro_st = f"{STATION_GYRO_RPM:.0f} RPM"
                string_st = f"UNREELING {self.sim.string_ext*100:.0f}%"
                halbach_st = "CHARGING"
            elif self.sim.phase_idx == 1:
                flywheel_st = "COUNTER-ROTATING"
                cooling_st = "STANDBY"
                laser_st = "ACTIVE" if self.sim.laser_active else "OFF"
                gyro_st = f"{STATION_GYRO_RPM:.0f} RPM"
                string_st = "RETRACTED" if self.sim.string_ext < 0.01 else f"RETRACTING {self.sim.string_ext*100:.0f}%"
                halbach_st = "SPINNING"
            elif self.sim.phase_idx == 2:
                flywheel_st = "BRAKING"
                cooling_st = "ACTIVE (CRYO)"
                laser_st = "ACTIVE"
                gyro_st = f"{STATION_GYRO_RPM:.0f} RPM"
                string_st = "STOWED"
                halbach_st = f"{HALBACH_FREQ_HZ:.1f} Hz"
            else:
                flywheel_st = "IDLE"
                cooling_st = "STANDBY"
                laser_st = "ACTIVE" if self.sim.laser_active else "OFF"
                gyro_st = f"{STATION_GYRO_RPM:.0f} RPM"
                string_st = "STOWED"
                halbach_st = "IDLE"
            cstats = [
                f"Flywheel: {flywheel_st}",
                f"Cooling: {cooling_st}",
                f"Halbach: {halbach_st}",
                f"Laser: {laser_st}",
                f"Gyro: {gyro_st}",
                f"String: {string_st}",
                f"RTG: {SPHERE_RTG_W/1000:.0f} kW",
                f"Sensors: {'ACTIVE' if self.sim.phase_idx == 0 else 'MONITORING'}",
            ]
            for s in cstats:
                col = C_GOOD if "ACTIVE" in s or "COUNTER" in s or "BRAKING" in s or "CRYO" in s else C_TEXT
                if "OFF" in s:
                    col = C_DIM
                surf.blit(_render_text(self.fsmall, s, col), (lx+8, yy))
                yy += 16

            # String tension gauge (below component status)
            ten_y = cy + 140
            surf.blit(_render_text(self.fsmall, "STRING TENSION", C_DIM), (lx+8, ten_y))
            ten_frac = self.sim.string_ext
            bar_w = 244
            bar_x = lx + 8
            pygame.draw.rect(surf, C_PANEL_HI, (bar_x, ten_y + 14, bar_w, 8))
            fill_w = int(bar_w * ten_frac)
            ten_col = _mix(C_COOL_FIN, C_STRESS, ten_frac)
            if fill_w > 0:
                pygame.draw.rect(surf, ten_col, (bar_x, ten_y + 14, fill_w, 8))
            part_py = cy + 180
        else:
            # Overview mode: component color legend
            _panel(surf, lx, ly, 260, 380, alpha=220)
            surf.blit(_render_text(self.fsmall, "COMPONENT LEGEND", C_ACCENT), (lx+8, ly+6))
            yy = ly + 24
            legend_items = [
                ("Event horizon", C_BH),
                ("Accretion disk", C_BH_DISK),
                ("Ergosphere", C_ERGO),
                ("Relativistic jets", C_JET),
                ("Lensing rings", C_LENS),
                ("Photon sphere", C_BH_GLOW),
                ("Energy sphere", C_SPHERE),
                ("Halbach array", C_HALBACH),
                ("Flywheel", C_FLYWHEEL),
                ("Cooling fins", C_COOL_FIN),
                ("Graphene lattice", C_LATTICE),
                ("Counter-rot ring", C_COUNTER),
                ("String", C_STRING),
                ("Deployment drum", C_DEPLOY),
                ("Stress indicators", C_STRESS),
                ("Station hull", C_STATION),
                ("Habitat ring", C_HABITAT),
                ("Docking ports", C_DOCK),
                ("Crew module", C_CREW),
                ("Heat radiators", C_RADIATOR),
                ("Solar arrays", C_SOLAR),
                ("Orbit path", C_ORBIT),
                ("Phase markers", C_PHASE1),
                ("Gravity laser", C_LASER),
                ("Magnetic field", C_PHASE3),
            ]
            for label, col in legend_items:
                pygame.draw.rect(surf, col, (lx+8, yy+2, 12, 12))
                pygame.draw.rect(surf, (60, 80, 110), (lx+8, yy+2, 12, 12), 1)
                surf.blit(_render_text(self.fsmall, label, C_TEXT), (lx+26, yy))
                yy += 16
            part_py = ly + 390

        # Part details panel (hovered/selected) - both modes
        part = self.renderer.active_part()
        if part and part.specs:
            py = part_py
            ph = min(200, 24 + len(part.specs) * 15 + 6)
            _panel(surf, lx, py, 260, ph, alpha=220)
            surf.blit(_render_text(self.fsmall, part.name, C_GOOD), (lx+8, py+6))
            yy2 = py + 22
            for spec in part.specs[:11]:
                surf.blit(_render_text(self.fsmall, f"  {spec}", C_TEXT), (lx+8, yy2))
                yy2 += 15

        # Bottom bar: controls
        _panel(surf, 0, self.H - 28, self.W, 28, alpha=200)
        controls = "TAB cycle modes | 1-5 select system | S systems | C custom | mouse orbit/zoom/pan | R reset | L labels | E explode | X section | P pause | SPACE phase/reset | +/- speed | I info | H help | ESC quit"
        surf.blit(_render_text(self.fsmall, controls, C_DIM), (12, self.H - 22))

    def _draw_phase_bar(self, surf):
        """Draw a 4-segment phase indicator bar below the top bar."""
        bar_x = 12
        bar_y = 36
        bar_w = self.W - 24
        bar_h = 6
        pb = self.sim.phase_bounds
        phases = [
            ("Charge", C_PHASE1, pb[0], pb[1]),
            ("Outbound", C_PHASE2, pb[1], pb[2]),
            ("Harvest", C_PHASE3, pb[2], pb[3]),
            ("Inbound", C_PHASE4, pb[3], pb[4]),
        ]
        for label, col, lo, hi in phases:
            seg_x = bar_x + int(bar_w * lo)
            seg_w = int(bar_w * (hi - lo))
            pygame.draw.rect(surf, C_PANEL_HI, (seg_x, bar_y, seg_w, bar_h))
            fill_w = 0
            if self.sim.t_frac >= hi:
                fill_w = seg_w
            elif self.sim.t_frac > lo:
                fill_w = int(seg_w * (self.sim.t_frac - lo) / (hi - lo))
            if fill_w > 0:
                pygame.draw.rect(surf, col, (seg_x, bar_y, fill_w, bar_h))
            # Phase label
            lbl_x = seg_x + seg_w // 2
            lbl = _render_text(self.fsmall, label, col if self.sim.phase_idx == phases.index((label, col, lo, hi)) else C_DIM)
            surf.blit(lbl, (lbl_x - lbl.get_width() // 2, bar_y + bar_h + 2))
        # Current position marker
        pos_x = bar_x + int(bar_w * self.sim.t_frac)
        pygame.draw.line(surf, C_ACCENT, (pos_x, bar_y - 2), (pos_x, bar_y + bar_h + 2), 2)

    def _draw_systems_hud(self):
        """Show all available BH harvesting systems for selection."""
        surf = self.screen
        # Top bar
        _panel(surf, 0, 0, self.W, 32, alpha=200)
        surf.blit(_render_text(self.font, "BHH - MULTI-SYSTEM OVERVIEW  |  Select a system (1-5) or ENTER to view", C_ACCENT), (12, 8))

        # System cards
        card_w = 290
        card_h = 340
        gap = 12
        n = len(self.systems)
        total_w = n * card_w + (n - 1) * gap
        start_x = max(12, (self.W - total_w) // 2)
        start_y = 50

        for i, sys in enumerate(self.systems):
            cx = start_x + i * (card_w + gap)
            cy = start_y
            is_selected = (i == self.system_idx)
            border_col = sys.color_accent if is_selected else (50, 60, 80)
            _panel(surf, cx, cy, card_w, card_h, alpha=220)
            pygame.draw.rect(surf, border_col, (cx, cy, card_w, card_h), 2 if is_selected else 1)

            # System name and number
            num_col = sys.color_accent
            surf.blit(_render_text(self.fmed, f"[{i+1}] {sys.name}", num_col), (cx + 10, cy + 8))
            pygame.draw.line(surf, (60, 80, 110), (cx + 10, cy + 34), (cx + card_w - 10, cy + 34), 1)

            # Description
            surf.blit(_render_text(self.fsmall, sys.desc, C_DIM), (cx + 10, cy + 40))

            # Key stats with color-coded highlights
            yy = cy + 64
            stats = [
                (f"BH mass: {sys.bh_mass_msun:.2f} M_sun", sys.color_accent),
                (f"  = {sys.bh_mass_kg:.3e} kg", C_TEXT),
                (f"Rs: {sys.bh_rs/1000:.2f} km" if sys.bh_rs >= 1000 else f"Rs: {sys.bh_rs:.3e} m", C_TEXT),
                (f"Density: {sys.bh_mass_kg / ((4.0/3.0) * 3.14159 * sys.bh_rs**3):.2e} kg/m^3" if sys.bh_rs > 0 else "Density: N/A", C_TEXT),
                (f"EP: {sys.orbit_ep_au:.2f} AU", C_EP),
                (f"AP: {sys.orbit_ap_au:.2f} AU", C_AP),
                (f"Ecc: {sys.orbit_e:.3f}", C_TEXT),
                (f"Period: {sys.orbit_period_yr:.1f} yr", C_TEXT),
                (f"V@EP: {sys.orbit_v_ep/1000:.1f} km/s", C_TEXT),
                (f"V@AP: {sys.orbit_v_ap/1000:.1f} km/s", C_TEXT),
                (f"Sphere: {sys.sphere_mass_kg:.1e} kg", C_SPHERE),
                (f"  R: {sys.sphere_radius_m:.0f} m", C_TEXT),
                (f"RPM: {sys.sphere_rpm_target:.0f}", C_TEXT),
                (f"Energy: {sys.sphere_e_pwh/3.6e18:.2f} PWh", C_PHASE3),
                (f"Spheres: {sys.n_spheres}", C_TEXT),
                (f"Hawking T: {sys.hawking_temperature():.2e} K", C_BH_GLOW),
                (f"Depletion: {sys.deplete_years:.1e} yr", C_DIM),
                (f"Distance: {sys.bh_dist_ly:.0f} ly", C_DIM),
            ]
            for s, col in stats:
                surf.blit(_render_text(self.fsmall, s, col), (cx + 10, yy))
                yy += 16

            # Mini energy bar at bottom of card
            bar_x = cx + 10
            bar_y = cy + card_h - 38
            bar_w = card_w - 20
            max_energy_all = max(s.sphere_e_pwh for s in self.systems)
            e_frac = sys.sphere_e_pwh / max_energy_all if max_energy_all > 0 else 0
            pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y, bar_w, 6))
            fill_w = int(bar_w * e_frac)
            if fill_w > 0:
                pygame.draw.rect(surf, C_PHASE3, (bar_x, bar_y, fill_w, 6))

            # Selected indicator
            if is_selected:
                surf.blit(_render_text(self.fsmall, ">>> CURRENT <<<", C_GOOD), (cx + 10, cy + card_h - 22))

        # Comparison stats section
        comp_y = start_y + card_h + 12
        comp_h = self.H - 28 - comp_y - 12
        if comp_h > 60:
            _panel(surf, 12, comp_y, self.W - 24, comp_h, alpha=220)
            surf.blit(_render_text(self.fsmall, "RELATIVE SCALE COMPARISON", C_ACCENT), (20, comp_y + 6))
            yy = comp_y + 24
            # Find max values for scaling
            max_mass = max(s.bh_mass_kg for s in self.systems)
            max_energy = max(s.sphere_e_pwh for s in self.systems)
            max_deplete = max(s.deplete_years for s in self.systems)
            max_rs = max(s.bh_rs for s in self.systems)
            metrics = [
                ("BH Mass", "bh_mass_kg", max_mass, "kg", False),
                ("Rs", "bh_rs", max_rs, "km", False),
                ("Energy/harvest", "sphere_e_pwh", max_energy, "J", False),
                ("Depletion time", "deplete_years", max_deplete, "yr", False),
                ("V@EP", "orbit_v_ep", max(s.orbit_v_ep for s in self.systems), "m/s", False),
                ("Annual power", None, max(s.sphere_e_pwh * s.n_spheres for s in self.systems), "J/yr", True),
            ]
            bar_w = self.W - 200
            for label, attr, max_val, unit, is_computed in metrics:
                surf.blit(_render_text(self.fsmall, f"{label}:", C_DIM), (20, yy))
                bx = 130
                for i, sys in enumerate(self.systems):
                    if is_computed:
                        val = sys.sphere_e_pwh * sys.n_spheres
                    else:
                        val = getattr(sys, attr)
                    frac = val / max_val if max_val > 0 else 0
                    seg_w = max(2, int(bar_w * frac / len(self.systems)))
                    col = sys.color_accent
                    pygame.draw.rect(surf, col, (bx, yy + 2, seg_w, 12))
                    bx += seg_w + 2
                # Show max value
                surf.blit(_render_text(self.fsmall, f"max: {max_val:.2e} {unit}", C_DIM), (bx + 8, yy))
                yy += 18

        # Bottom bar
        _panel(surf, 0, self.H - 28, self.W, 28, alpha=200)
        controls = "TAB cycle modes | 1-5 select system | ENTER view selected | C custom build | S systems | H help | ESC quit"
        surf.blit(_render_text(self.fsmall, controls, C_DIM), (12, self.H - 22))

    def _draw_custom_hud(self):
        """Custom system builder UI."""
        surf = self.screen
        # Top bar
        _panel(surf, 0, 0, self.W, 32, alpha=200)
        surf.blit(_render_text(self.font, "BHH - CUSTOM SYSTEM BUILDER  |  UP/DOWN select  |  LEFT/RIGHT adjust  |  ENTER apply", C_ACCENT), (12, 8))

        # Main panel
        pw, ph = 600, 620
        px = self.W // 2 - pw // 2
        py = 50
        _panel(surf, px, py, pw, ph, alpha=230)
        pygame.draw.rect(surf, C_ACCENT, (px, py, pw, ph), 1)

        surf.blit(_render_text(self.fbig, "CUSTOM BUILD", C_ACCENT), (px + 20, py + 16))
        pygame.draw.line(surf, (60, 80, 110), (px + 20, py + 52), (px + pw - 20, py + 52), 1)

        # Parameter labels and values
        param_labels = {
            'bh_mass_msun': 'Black Hole Mass (M_sun)',
            'orbit_ep_au': 'Periastron (AU)',
            'orbit_ap_au': 'Apastron (AU)',
            'sphere_mass_kg': 'Sphere Mass (kg)',
            'sphere_rpm_target': 'Target RPM',
            'string_diam_m': 'String Diameter (m)',
            'n_spheres': 'Number of Spheres',
        }
        param_format = {
            'bh_mass_msun': '{:.2f}',
            'orbit_ep_au': '{:.3f}',
            'orbit_ap_au': '{:.3f}',
            'sphere_mass_kg': '{:.2e}',
            'sphere_rpm_target': '{:.0f}',
            'string_diam_m': '{:.4f}',
            'n_spheres': '{:.0f}',
        }

        yy = py + 64
        for i, key in enumerate(self.custom_param_keys):
            is_active = (i == self.custom_edit_idx)
            label = param_labels.get(key, key)
            val = self.custom_params[key]
            fmt = param_format.get(key, '{}')
            val_str = fmt.format(val)

            if is_active:
                pygame.draw.rect(surf, (30, 50, 70), (px + 10, yy - 2, pw - 20, 28))
                surf.blit(_render_text(self.fmed, ">", C_ACCENT), (px + 16, yy + 2))
            label_col = C_ACCENT if is_active else C_TEXT
            val_col = C_GOOD if is_active else C_TEXT
            surf.blit(_render_text(self.fmed, label, label_col), (px + 36, yy + 2))
            surf.blit(_render_text(self.fmed, val_str, val_col), (px + pw - 160, yy + 2))
            yy += 32

        # Preview derived values
        yy += 10
        pygame.draw.line(surf, (60, 80, 110), (px + 20, yy), (px + pw - 20, yy), 1)
        yy += 10
        surf.blit(_render_text(self.fmed, "DERIVED VALUES (preview)", C_DIM), (px + 20, yy))
        yy += 24

        p = self.custom_params
        try:
            preview = create_custom_config(
                bh_mass_msun=p['bh_mass_msun'],
                orbit_ep_au=p['orbit_ep_au'],
                orbit_ap_au=p['orbit_ap_au'],
                sphere_mass_kg=p['sphere_mass_kg'],
                sphere_rpm_target=p['sphere_rpm_target'],
                string_diam_m=p['string_diam_m'],
                n_spheres=int(p['n_spheres']),
            )
            derived = [
                f"Rs: {preview.bh_rs/1000:.2f} km",
                f"BH density: {preview.bh_mass_kg / ((4.0/3.0)*PI*preview.bh_rs**3):.3e} kg/m^3",
                f"Eccentricity: {preview.orbit_e:.3f}",
                f"Period: {preview.orbit_period_yr:.1f} yr",
                f"V@EP: {preview.orbit_v_ep/1000:.1f} km/s",
                f"V@AP: {preview.orbit_v_ap/1000:.1f} km/s",
                f"Sphere R: {preview.sphere_radius_m:.0f} m",
                f"Energy/harvest: {preview.sphere_e_pwh/3.6e18:.2f} PWh",
                f"String length: {preview.string_length_m/1000:.0f} km",
                f"String tension: {preview.string_t_max:.2e} N",
                f"Hawking T: {preview.hawking_temperature():.2e} K",
                f"Depletion: {preview.deplete_years:.1e} yr",
                f"Annual energy: {preview.sphere_e_pwh * preview.n_spheres / 3.6e18:.0f} PWh/yr",
            ]
            # Validation warnings
            warnings = []
            if preview.orbit_e >= 0.95:
                warnings.append("WARNING: Very high eccentricity!")
            if preview.bh_rs < 0.001:
                warnings.append("WARNING: BH too small (Planck scale)")
            if preview.sphere_rpm_target > 50000:
                warnings.append("WARNING: Very high RPM (material limits)")
            if preview.string_diam_m < 0.0001:
                warnings.append("WARNING: String too thin (may break)")
            for s in derived:
                surf.blit(_render_text(self.fsmall, f"  {s}", C_TEXT), (px + 20, yy))
                yy += 16
            for w in warnings:
                surf.blit(_render_text(self.fsmall, f"  ! {w}", C_WARN), (px + 20, yy))
                yy += 16
        except Exception:
            surf.blit(_render_text(self.fsmall, "  (invalid parameters)", C_WARN), (px + 20, yy))

        # Instructions
        yy = py + ph - 60
        surf.blit(_render_text(self.fsmall, "UP/DOWN: select parameter  |  LEFT/RIGHT: adjust value", C_DIM), (px + 20, yy))
        yy += 16
        surf.blit(_render_text(self.fsmall, "ENTER: build & view system  |  TAB: exit custom mode", C_DIM), (px + 20, yy))

        # Bottom bar
        _panel(surf, 0, self.H - 28, self.W, 28, alpha=200)
        controls = "TAB cycle modes | UP/DOWN select | LEFT/RIGHT adjust | ENTER apply | S systems | H help | ESC quit"
        surf.blit(_render_text(self.fsmall, controls, C_DIM), (12, self.H - 22))

    def _draw_depletion_hud(self):
        surf = self.screen
        dep = self.dep
        mass_frac = dep.mass_fraction()

        # Top bar
        _panel(surf, 0, 0, self.W, 32, alpha=200)
        pygame.draw.rect(surf, self.current_system.color_accent, (0, 0, self.W, 3))
        if dep.exploded:
            title = f"BHH - {CURRENT_SYSTEM_NAME} DEPLETION  |  EXPLOSION  |  Progress: {dep.explosion_progress()*100:.1f}%"
            title_col = C_WARN
        else:
            title = f"BHH - {CURRENT_SYSTEM_NAME} DEPLETION  |  Mass: {dep.mass_kg:.3e} kg ({dep.mass_kg/M_SUN:.4f} M_sun)  |  Years: {dep.years_elapsed:.2e}"
            title_col = C_BH_GLOW if dep.is_critical() else self.current_system.color_accent
        surf.blit(_render_text(self.font, title, title_col), (12, 8))

        # Right panel: depletion stats
        px = self.W - 320
        py = 40
        _panel(surf, px, py, 310, 440, alpha=220)
        surf.blit(_render_text(self.fsmall, "DEPLETION STATUS", C_BH_GLOW), (px+8, py+6))
        yy = py + 24
        t_h = dep.hawking_temperature()
        p_h = dep.hawking_power()
        rs_km = dep.schwarzschild_radius() / 1000.0
        rs_m = dep.schwarzschild_radius()
        bh_vol = (4.0/3.0) * PI * rs_m**3 if rs_m > 0 else 0
        bh_rho = dep.mass_kg / bh_vol if bh_vol > 0 else 0
        rs_display = f"{rs_km:.4f} km" if rs_m >= 1000 else f"{rs_m:.3e} m"
        stats = [
            f"Mass: {dep.mass_kg:.3e} kg",
            f"  = {dep.mass_kg/M_SUN:.6f} M_sun",
            f"Mass remaining: {mass_frac*100:.6f}%",
            f"Schwarzschild R: {rs_display}",
            f"BH density: {bh_rho:.3e} kg/m^3",
            f"Hawking temp: {t_h:.3e} K",
            f"Hawking power: {p_h:.3e} W",
            "",
            f"Harvests: {dep.harvest_count:.3e}",
            f"Years elapsed: {dep.years_elapsed:.3e} yr",
            f"Harvest rate: {dep.harvest_rate_per_yr:.1f}/yr",
            f"Mass/harvest: {MASS_PER_HARVEST:.0f} kg",
            "",
            f"Harvests to deplete: {HARVESTS_TO_DEPLETE:.2e}",
            f"Depletion time: {DEPLETE_YEARS:.2e} yr",
            "",
            f"Sim speed: {dep.speed:.1e} yr/s",
            f"Paused: {'YES' if dep.paused else 'NO'}",
        ]
        if dep.is_critical() and not dep.exploded:
            stats.append("")
            stats.append("*** APPROACHING INSTABILITY ***")
            stats.append("Hawking evaporation accelerating!")
            stats.append("Jets intensifying, radiation peaking")
        if dep.exploded:
            stats.append("")
            stats.append(f"*** EXPLOSION IN PROGRESS ***")
            stats.append(f"Progress: {dep.explosion_progress()*100:.1f}%")
        for s in stats:
            col = C_WARN if "INSTABILITY" in s or "EXPLOSION" in s or "***" in s else C_TEXT
            if "YES" in s and "Paused" in s:
                col = C_WARN
            if s == "":
                yy += 6
            else:
                surf.blit(_render_text(self.fsmall, s, col), (px+8, yy))
                yy += 16

        # Mass depletion bar
        bar_y = py + 440 - 110
        surf.blit(_render_text(self.fsmall, "MASS REMAINING", C_DIM), (px+8, bar_y))
        bar_w = 294
        bar_x = px + 8
        pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y + 14, bar_w, 10))
        fill_w = int(bar_w * mass_frac)
        if fill_w > 0:
            mass_col = C_GOOD if mass_frac > 0.5 else (C_WARN if mass_frac > 0.1 else C_BH_GLOW)
            pygame.draw.rect(surf, mass_col, (bar_x, bar_y + 14, fill_w, 10))
        # Critical threshold marker (0.1% of initial mass)
        crit_frac = 1e-3
        crit_x = bar_x + int(bar_w * crit_frac)
        pygame.draw.line(surf, C_WARN, (crit_x, bar_y + 12), (crit_x, bar_y + 24), 2)

        # Hawking temperature gauge (logarithmic)
        bar_y2 = bar_y + 32
        surf.blit(_render_text(self.fsmall, "HAWKING TEMPERATURE (log)", C_DIM), (px+8, bar_y2))
        # Map temperature from ~1e-8 K (full mass) to ~1e11 K (instability) to 0..1
        t_min, t_max = 1e-8, 1e11
        t_frac = (math.log10(max(t_h, 1e-20)) - math.log10(t_min)) / (math.log10(t_max) - math.log10(t_min))
        t_frac = max(0.0, min(1.0, t_frac))
        pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y2 + 14, bar_w, 10))
        fill_w2 = int(bar_w * t_frac)
        if fill_w2 > 0:
            t_col = C_PHASE3 if t_frac < 0.3 else (C_ACCENT if t_frac < 0.7 else C_WARN)
            pygame.draw.rect(surf, t_col, (bar_x, bar_y2 + 14, fill_w2, 10))

        # Hawking power gauge (logarithmic)
        bar_y3 = bar_y2 + 32
        surf.blit(_render_text(self.fsmall, "HAWKING POWER (log)", C_DIM), (px+8, bar_y3))
        p_min, p_max = 1e-30, 1e20
        p_frac = (math.log10(max(p_h, 1e-40)) - math.log10(p_min)) / (math.log10(p_max) - math.log10(p_min))
        p_frac = max(0.0, min(1.0, p_frac))
        pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y3 + 14, bar_w, 10))
        fill_w3 = int(bar_w * p_frac)
        if fill_w3 > 0:
            p_col = C_PHASE3 if p_frac < 0.3 else (C_ACCENT if p_frac < 0.7 else C_WARN)
            pygame.draw.rect(surf, p_col, (bar_x, bar_y3 + 14, fill_w3, 10))

        # Explosion progress bar (if exploded)
        if dep.exploded:
            bar_y4 = bar_y3 + 32
            prog = dep.explosion_progress()
            surf.blit(_render_text(self.fsmall, "EXPLOSION PROGRESS", C_WARN), (px+8, bar_y4))
            pygame.draw.rect(surf, C_PANEL_HI, (bar_x, bar_y4 + 14, bar_w, 10))
            fill_w4 = int(bar_w * prog)
            if fill_w4 > 0:
                exp_col = _mix((255, 255, 255), C_BH_GLOW, prog)
                pygame.draw.rect(surf, exp_col, (bar_x, bar_y4 + 14, fill_w4, 10))

        # Left panel: phase description / info
        lx = 12
        ly = 40
        _panel(surf, lx, ly, 280, 230, alpha=220)
        surf.blit(_render_text(self.fsmall, "DEPLETION SCENARIO", C_BH_GLOW), (lx+8, ly+6))
        yy = ly + 24
        if dep.exploded:
            prog = dep.explosion_progress()
            if prog > 0.6:
                desc_lines = [
                    "=== WORMHOLE PHASE ===",
                    "Einstein-Rosen bridge forming",
                    "from Planck remnant.",
                    "",
                    "White hole: time-reverse of BH.",
                    "Matter/light can only exit.",
                    "Theoretical ER=EPR connection.",
                    "",
                    "Unstable, short-lived in practice.",
                ]
            elif prog > 0.15:
                desc_lines = [
                    "=== FINAL EXPLOSION ===",
                    "Black hole mass has dropped below",
                    "0.1% of initial mass.",
                    "",
                    "Hawking radiation enters runaway",
                    "phase - all remaining mass converts",
                    "to radiation in a final burst.",
                    "",
                    "Visual: gamma flash, shockwave,",
                    "ring waves, relativistic jets,",
                    "debris + secondary particles.",
                    "",
                    "A Planck-mass remnant may persist",
                    "as a stable exotic object.",
                ]
            else:
                desc_lines = [
                    "=== GAMMA FLASH ===",
                    "Initial burst of high-energy",
                    "gamma radiation from runaway",
                    "Hawking evaporation.",
                    "",
                    "Shockwave expanding outward.",
                    "Ring waves forming in disk plane.",
                    "Relativistic jets along spin axis.",
                ]
        elif dep.is_critical():
            desc_lines = [
                "=== CRITICAL PHASE ===",
                "Black hole approaching instability.",
                "Hawking temperature rising rapidly.",
                "Mass loss accelerating beyond",
                "harvesting rate.",
                "",
                "Visual: ergosphere visible, jets",
                "intensifying, Doppler disk bright,",
                "lensing rings prominent.",
                "",
                "Explosion imminent when mass",
                "drops below 0.1% of initial.",
            ]
        else:
            desc_lines = [
                "=== HARVESTING PHASE ===",
                "Constellation of spheres harvesting",
                f"rotational energy at {N_SPHERES}/day.",
                "",
                f"Each harvest removes",
                f"{MASS_PER_HARVEST:.0f} kg (E=mc^2).",
                "",
                "Visual: event horizon, photon sphere,",
                "accretion disk (Doppler-shifted),",
                "ISCO ring, Hawking radiation glow.",
                "",
                f"Full depletion in ~{DEPLETE_YEARS:.1e} yr.",
                "Hawking temp negligible at this mass.",
            ]
        for line in desc_lines:
            col = C_WARN if "EXPLOSION" in line or "CRITICAL" in line or "imminent" in line else C_TEXT
            if "WORMHOLE" in line or "White hole" in line or "Einstein" in line or "ER=EPR" in line:
                col = (200, 150, 255)
            surf.blit(_render_text(self.fsmall, line, col), (lx+8, yy))
            yy += 15

        # Part details (if hovered/selected)
        part = self.renderer.active_part()
        if part and part.specs:
            py2 = ly + 240
            ph2 = min(250, 24 + len(part.specs) * 15 + 6)
            _panel(surf, lx, py2, 280, ph2, alpha=220)
            surf.blit(_render_text(self.fsmall, part.name, C_BH_GLOW), (lx+8, py2+6))
            yy2 = py2 + 22
            for spec in part.specs[:14]:
                col = C_WARN if "INSTABILITY" in spec or "EXPLOSION" in spec else C_TEXT
                surf.blit(_render_text(self.fsmall, f"  {spec}", col), (lx+8, yy2))
                yy2 += 15

        # Bottom bar: controls
        _panel(surf, 0, self.H - 28, self.W, 28, alpha=200)
        controls = "TAB mode | mouse orbit/zoom/pan | R reset | P pause | +/- speed | SPACE reset depletion | I info | H help | ESC close/quit"
        surf.blit(_render_text(self.fsmall, controls, C_DIM), (12, self.H - 22))

    def _draw_info(self):
        surf = self.screen
        w, h = min(1100, self.W - 40), min(900, self.H - 20)
        x, y = self.W//2 - w//2, max(10, self.H//2 - h//2)
        if self._info_surf is None or self._info_surf.get_size() != (w, h):
            self._info_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            s = self._info_surf
            _panel(s, 0, 0, w, h, alpha=245)
            s.blit(_render_text(self.fmed, f"BHH - {CURRENT_SYSTEM_NAME} - SYSTEM INFORMATION", C_ACCENT), (20, 16))
            pygame.draw.line(s, (60, 80, 110), (20, 44), (w-20, 44), 1)

            left_sections = [
                (f"BLACK HOLE ({CURRENT_SYSTEM_NAME})", [
                    f"Mass: {BH_MASS_KG/M_SUN:.2f} M_sun ({BH_MASS_KG:.3e} kg)",
                    f"Schwarzschild radius: {BH_RS/1000:.1f} km" if BH_RS >= 1000 else f"Schwarzschild radius: {BH_RS:.3e} m",
                    f"Photon sphere: {BH_RPH/1000:.1f} km" if BH_RPH >= 1000 else f"Photon sphere: {BH_RPH:.3e} m",
                    f"ISCO: {BH_RISCO/1000:.1f} km" if BH_RISCO >= 1000 else f"ISCO: {BH_RISCO:.3e} m",
                    f"Ergosphere: {BH_RS*1.3/1000:.1f} km (oblate, Kerr-like)" if BH_RS*1.3 >= 1000 else f"Ergosphere: {BH_RS*1.3:.3e} m",
                    f"Average density: {bh_density():.2e} kg/m^3",
                    f"Total energy (E=mc^2): {BH_MASS_KG * C**2:.2e} J",
                    f"Surface gravity: {G*BH_MASS_KG/BH_RS**2:.2e} m/s^2",
                    f"Distance: {BH_DIST_LY:.0f} ly",
                    f"Hawking temperature: {6.169e-8 * M_SUN / BH_MASS_KG:.3e} K",
                    f"Hawking power: {1.0546e-34 * C**6 / (15360.0 * PI * G**2 * BH_MASS_KG**2):.3e} W",
                    "Type: Schwarzschild (non-rotating)",
                    "Relativistic jets: perpendicular to disk",
                    "Doppler shift: blue (approaching) / red (receding)",
                    "Gravitational lensing: photon paths bent near EH",
                ]),
                ("ENERGY SPHERE", [
                    f"Mass: {SPHERE_MASS_KG:.2e} kg",
                    f"Radius: {SPHERE_RADIUS_M:.0f} m",
                    f"Material: Graphene composite",
                    f"Tensile strength: {SPHERE_TENSILE_PA/1e9:.0f} GPa",
                    f"Max RPM: {SPHERE_RPM_MAX:.0f} -> {SPHERE_E_MAX:.2e} J ({SPHERE_E_MAX/3.6e18:.2f} PWh)",
                    f"Target RPM: {SPHERE_RPM_TARGET:.0f} -> {SPHERE_E_OPER:.2e} J ({SPHERE_E_OPER/3.6e18:.2f} PWh)",
                    f"Moment of inertia: {SPHERE_I:.2e} kg m^2",
                    f"RTG power: {SPHERE_RTG_W/1000:.0f} kW total (Pu-238)",
                    f"Halbach freq: {HALBACH_FREQ_HZ:.1f} Hz (cryogenic NdFeB)",
                    f"Escape thrusters: delta-v = {SPHERE_DELTA_V:.0f} m/s",
                    "Radiation shielding: boron composites",
                    "Safety: halt if dg >10%, 20% excess impact",
                    "AI: neural networks for anomaly detection",
                    f"Reliability: 99.9% over {ORBIT_PERIOD_YR:.1f}-year cycles (Monte Carlo validated)",
                    "Internal flywheel: counter-rotating angular momentum",
                    "Cooling: cryogenic fins between Halbach magnets",
                    "Lattice: graphene meridian ribs for integrity",
                    "Counter-rotating ring: gyroscopic stabilization",
                ]),
                ("STRING & TIP MASS", [
                    f"Material: Graphene composite",
                    f"Diameter: {STRING_DIAM_M*100:.1f} cm ({STRING_DIAM_M/0.0254:.1f} in)",
                    f"Tensile strength: {STRING_TENSILE/1e9:.0f} GPa",
                    f"Max tension: {STRING_T_MAX:.2e} N",
                    f"Length: {STRING_LENGTH_M:.2e} m ({STRING_LENGTH_MI:.0f} miles)",
                    f"Tip mass: {STRING_TIP_MASS:.2e} kg (osmium, R={STRING_TIP_R_M:.0f} m)",
                    f"Safety margin: {SAFETY_MARGIN*100:.0f}% excess impact parameter",
                    "Reusable (reeled back at AP)",
                    "Deployment: motorized drum with guide roller",
                    "Tension gradient: color-coded (blue=low, red=high)",
                    "Stress rings: at 30%, 50%, 70% along length",
                ]),
                ("PULL-TO-ROTATION SYSTEM", [
                    f"Gear stages: {GEAR_STAGES} x {GEAR_RATIO_PER:.0f}:1 = {GEAR_RATIO_TOTAL:.0f}:1",
                    f"Efficiency: {GEAR_EFFICIENCY*100:.0f}%",
                    f"Constant-tension clutch at T_max",
                    "Disengagement: triple-redundant (EM clutch + swivel + ratchet + eddy brake)",
                    f"Drum radius: {DRUM_RADIUS_M:.0f} m",
                    "Bearings: diamond-like carbon, silicon nitride",
                    "Sensors: piezoelectric strain, accelerometers, Doppler",
                    "Controls: radiation-hardened silicon processors",
                    "Gears: 3D-printed reinforced alloys (graphene-infused steel)",
                ]),
            ]

            right_sections = [
                ("ORBIT", [
                    f"Periastron: {ORBIT_EP_AU:.4f} AU",
                    f"Apastron: {ORBIT_AP_AU:.2f} AU",
                    f"Semi-major axis: {ORBIT_A_M/AU_M:.2f} AU",
                    f"Eccentricity: {ORBIT_E:.4f}",
                    f"Period: {ORBIT_PERIOD_YR:.1f} years",
                    f"v at EP: {ORBIT_V_EP/1000:.1f} km/s",
                    f"v at AP: {ORBIT_V_AP/1000:.1f} km/s",
                    f"Gravity at EP: {gravity_at_distance(ORBIT_EP_M):.2e} m/s^2",
                    f"Gravity at AP: {gravity_at_distance(ORBIT_AP_M):.2e} m/s^2",
                    f"EP drift/cycle: {EP_DRIFT_KM:.4f} km",
                    f"EP/ISCO ratio: {ORBIT_EP_M/BH_RISCO:.0f}x (stable orbit)",
                    f"NOTE: BH/sphere/station visually enlarged",
                ]),
                ("SPACE STATION & HARVESTING", [
                    f"Position: Circular orbit at AP ({ORBIT_AP_AU:.2f} AU)",
                    f"Station v_circ: {math.sqrt(G*BH_MASS_KG/ORBIT_AP_M)/1000:.1f} km/s",
                    f"Gravity at AP: {gravity_at_distance(ORBIT_AP_M):.2e} m/s^2",
                    f"Station-keeping: Unbalanced gyroscopic flywheel",
                    f"  Gyro: {STATION_GYRO_MASS:.0e} kg, R={STATION_GYRO_R:.0f} m, {STATION_GYRO_RPM:.0f} RPM",
                    f"  Eff: {GYRO_EFFICIENCY*100:.0f}% regenerative, ~1% of harvest energy",
                    f"Harvesting: Magnetic inductive coupling (non-contact)",
                    f"  Halbach: {STATION_B_FIELD:.1f} T, {HALBACH_FREQ_HZ:.1f} Hz (cryogenic)",
                    f"  Coil: {STATION_COIL_LEN/1000:.0f} km YBCO, LHe cooled",
                    f"  Harvest window: {STATION_HARVEST_S/86400:.0f} days, {harvest_power()/1e9:.0f} GW, {STATION_EFFICIENCY*100:.0f}% eff",
                    f"  Flyby: ~10-100 m separation, ~{relative_flyby_velocity()/1000:.1f} km/s relative",
                    f"Laser: {LASER_POWER_GW:.0f} GW (eff={LASER_EFFICIENCY*100:.0f}%), {LASER_FORCE_N:.0e} N",
                    f"Fusion: ~{STATION_FUSION_TW:.0f} TW (helium-3)",
                    "Targeting: optical telescopes + Doppler radar",
                    "Comms: quantum-encrypted laser links",
                    "Habitat: rotating cylinder, artificial gravity",
                    "Docking: 3 ports, automated approach",
                    "Thermal: radiator fins + coolant loops",
                    "Power: solar arrays (backup) + fusion (primary)",
                    "Crew: pressurized module with life support",
                ]),
                ("CONSTELLATION & DEPLETION", [
                    f"Spheres: {N_SPHERES}",
                    f"Harvest rate: 1/day",
                    f"Mass/harvest (E=mc^2): {MASS_PER_HARVEST:.0f} kg",
                    f"Harvests to deplete: {HARVESTS_TO_DEPLETE:.2e}",
                    f"Depletion time: {DEPLETE_YEARS:.2e} years",
                    f"Annual energy: {N_SPHERES * SPHERE_E_PWH / 3.6e18:.0f} PWh/yr",
                    f"Powers ~{HOMES_POWERED/1e6:.0f}M homes continuously",
                    "Depletion visuals: ergosphere, jets, Doppler disk",
                    "Explosion: gamma flash, shockwave, ring waves",
                    "Final: Planck remnant, wormhole, white hole",
                ]),
                ("OPERATIONAL CYCLE (4 PHASES)", [
                    f"1. Charging at EP: String unreels at T_max, spins to {SPHERE_RPM_TARGET:.0f} RPM",
                    f"   EP drift: {EP_DRIFT_KM:.4f} km/cycle, sensors halt if dg >10%",
                    "2. Outbound: String retracts (~10% out), laser corrects near EP",
                    "   Retraction: drum motor, ~0.05% of harvested energy",
                    "   Correction at f~5deg, Oberth effect, ~0.001 m/s delta-v",
                    "3. Harvesting at AP: Magnetic coupling extracts spin to 0 RPM",
                    f"   {harvest_power()/1e9:.0f} GW for {STATION_HARVEST_S/86400:.0f} days -> {HARVEST_ENERGY_J:.2e} J",
                    "4. Inbound: Coast 0 RPM, laser restores EP at AP (~0.0005 m/s)",
                    f"Cycle repeats every {ORBIT_PERIOD_YR:.1f} years per sphere",
                ]),
            ]

            col_w = w // 2
            section_colors = [C_EP, C_SPHERE, C_STRING, C_GEAR, C_AP, C_STATION, C_PHASE3, C_PHASE4]
            yy_left = 52
            yy_right = 52
            si = 0
            for title, items in left_sections:
                sc = section_colors[si % len(section_colors)]
                pygame.draw.rect(s, sc, (20, yy_left + 2, 3, 16))
                s.blit(_render_text(self.font, title, sc), (28, yy_left))
                yy_left += 20
                for item in items:
                    s.blit(_render_text(self.fsmall, f"  {item}", C_TEXT), (28, yy_left))
                    yy_left += 14
                yy_left += 6
                si += 1
            si = 4
            for title, items in right_sections:
                sc = section_colors[si % len(section_colors)]
                pygame.draw.rect(s, sc, (col_w+20, yy_right + 2, 3, 16))
                s.blit(_render_text(self.font, title, sc), (col_w+28, yy_right))
                yy_right += 20
                for item in items:
                    s.blit(_render_text(self.fsmall, f"  {item}", C_TEXT), (col_w+28, yy_right))
                    yy_right += 14
                yy_right += 6
                si += 1
            s.blit(_render_text(self.fsmall, "I or ESC to close", C_DIM), (20, h-22))
        surf.blit(self._info_surf, (x, y))

    def _draw_help(self):
        surf = self.screen
        w, h = 560, 560
        x, y = self.W//2 - w//2, self.H//2 - h//2
        if self._help_surf is None:
            self._help_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            s = self._help_surf
            _panel(s, 0, 0, w, h, alpha=245)
            s.blit(_render_text(self.fmed, "CONTROLS", C_ACCENT), (20, 16))
            pygame.draw.line(s, (60, 80, 110), (20, 44), (w-20, 44), 1)
            helps = [
                ("TAB", "Cycle: OVERVIEW -> SIMULATE -> DEPLETION -> SYSTEMS -> CUSTOM"),
                ("S", "Systems selection screen"),
                ("C", "Custom system builder"),
                ("1-5", "Quick-select preset system"),
                ("ENTER", "View selected system / Apply custom build"),
                ("Mouse L-click", "Select part for inspection"),
                ("Mouse L-drag", "Orbit camera (rotate view)"),
                ("Mouse R-drag", "Pan camera"),
                ("Mouse wheel", "Zoom in/out"),
                ("R", "Reset camera view"),
                ("L", "Toggle part labels"),
                ("E", "Toggle exploded view"),
                ("X", "Toggle section cut"),
                ("P", "Pause/resume simulation or depletion"),
                ("SPACE", "Next phase / Reset depletion"),
                ("+ / -", "Increase/decrease sim or depletion speed"),
                ("I", "Toggle system information panel"),
                ("H", "Toggle this help panel"),
                ("ESC", "Close panel / Quit"),
            ]
            yy = 52
            for key, desc in helps:
                s.blit(_render_text(self.font, key, C_ACCENT), (20, yy))
                s.blit(_render_text(self.font, desc, C_TEXT), (140, yy))
                yy += 22
            # Model components section
            yy += 8
            pygame.draw.line(s, (60, 80, 110), (20, yy), (w-20, yy), 1)
            yy += 8
            s.blit(_render_text(self.fmed, "DETAILED MODEL COMPONENTS", C_ACCENT), (20, yy))
            yy += 22
            components = [
                "Black Hole: event horizon, ergosphere, photon sphere,",
                "  ISCO ring, accretion disk (Doppler-shifted), jets,",
                "  gravitational lensing rings, Hawking radiation glow",
                "Sphere: Halbach array, gears, flywheel, cooling fins,",
                "  graphene lattice ribs, counter-rotating ring,",
                "  RTG, sensors, thrusters, antenna, shielding",
                "String: deployment drum, tension gradient segments,",
                "  stress indicator rings, tip mass with locking ring",
                "Station: habitat (rotating), docking ports, crew module,",
                "  radiator fins, solar arrays, gyro flywheel, coil array,",
                "  gravity laser, fusion reactor, comm dish",
                "Orbit: path, direction arrows, phase markers,",
                "  velocity vectors at EP and AP",
                "Laser: 3-layer beam, targeting reticle, impact glow",
                "Effects: energy beam, flow particles, magnetic field,",
                "  spin indicator, charging glow, laser impact",
                "Depletion: ergosphere, jets, Doppler disk, lensing,",
                "  Hawking radiation, ISCO ring, harvesting beams",
                "Explosion: gamma flash, shockwave, ring waves, jets,",
                "  debris, secondary particles, Planck remnant, wormhole",
            ]
            for line in components:
                s.blit(_render_text(self.fsmall, line, C_TEXT), (20, yy))
                yy += 15
            s.blit(_render_text(self.fsmall, "H or ESC to close", C_DIM), (20, h-22))
        surf.blit(self._help_surf, (x, y))

    def run(self):
        banner = (
            "\n" + "=" * 72 +
            "\n BHH - BLACK HOLE ENERGY HARVESTER" +
            "\n" + "=" * 72 +
            f"\n {self.current_system.name} -> tidal gradient -> string -> pull-to-rotation -> spin sphere" +
            "\n -> coast to AP -> magnetic inductive harvest -> gravity laser correction" +
            f"\n -> repeat. {SPHERE_E_PWH/3.6e18:.1f} PWh per cycle, {N_SPHERES} spheres, 1 harvest/day." +
            "\n" +
            "\n DETAILED MODEL COMPONENTS:" +
            "\n   Black Hole: event horizon, ergosphere, photon sphere, ISCO ring," +
            "\n     Doppler-shifted accretion disk, relativistic jets, lensing rings" +
            "\n   Sphere: Halbach array, flywheel, cooling fins, graphene lattice," +
            "\n     counter-rotating ring, RTG, sensors, thrusters, antenna, shielding" +
            "\n   String: deployment drum, tension gradient, stress indicators," +
            "\n     tip mass with locking ring" +
            "\n   Station: rotating habitat, docking ports, crew module, radiators," +
            "\n     solar arrays, gyro flywheel, coil array, gravity laser, fusion reactor" +
            "\n   Orbit: path, direction arrows, phase markers, velocity vectors" +
            "\n   Laser: 3-layer beam, targeting reticle, impact glow" +
            "\n   Effects: energy beam, flow particles, magnetic field, spin indicator" +
            "\n   Depletion: Hawking radiation, jets, Doppler disk, explosion + wormhole" +
            "\n" +
            "\n Now supports 5 preset systems + custom builds!" +
            "\n TAB  :  OVERVIEW -> SIMULATE -> DEPLETION -> SYSTEMS -> CUSTOM" +
            "\n 1-5  :  Quick-select preset system (Gaia BH1, Cygnus X-1, Sgr A*, etc.)" +
            "\n S    :  Systems selection screen   C: Custom system builder" +
            "\n Mouse:  orbit / zoom / pan   R: reset   L: labels   E: explode" +
            "\n Sim:   P pause   SPACE phase   +/- speed   I info   H help" +
            "\n" + "=" * 72 + "\n"
        )
        print(banner)
        while True:
            dt = self.clock.tick(60) / 1000.0
            if not self.handle_events(dt):
                break
            self.update(dt)
            self.draw()
        pygame.quit()


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    if pygame is None:
        print("pygame is required for the interactive viewer.\n"
              "Install it with:  pip install pygame numpy\n")
        return 1
    App().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
