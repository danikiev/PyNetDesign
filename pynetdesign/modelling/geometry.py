"""Synthetic DAS geometry builders used by examples and tests.

These helpers generate simple borehole, surface, and dark-fiber layouts in
the tab-delimited geometry format consumed by :mod:`pynetdesign.modelling.io`.
"""

import numpy as np

__all__ = [
    'generate_geometry',
    'generate_borehole_geometry',
    'generate_surface_geometry',
    'generate_darkfiber_geometry',
]


def _format_header_value(value: float) -> str:
    """Format numeric header values without forcing integer rounding."""
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def generate_geometry(
    mode: str,
    # Common parameters
    center_x: float = 0.0,
    center_y: float = 0.0,
    spacing: float = 10.0,
    noise_level: float = 5.0e-5,
    gauge_length: float = 10.0,
    cable_length: float = 5000.0,
    # Borehole parameters
    start_depth: float = 0.0,
    azimuth: float = 0.0,
    dip: float = 90.0,
    surface_noise: float = None,
    noise_decay_depth: float = 150.0,
    noise_low_depth: float = 200.0,
    # Surface / dark-fiber common
    depth: float = 0.0,
    # Surface zigzag
    surface_shape: str = 'zigzag',
    zigzag_amplitude: float = 500.0,
    zigzag_segment_length: float = 1000.0,
    # Surface L-shape
    l_arm_x: float = 3000.0,
    l_arm_y: float = 3000.0,
    # Surface square / rectangle
    rect_width: float = 3000.0,
    rect_height: float = 3000.0,
    # Surface double lines
    double_line_separation: float = 500.0,
    # Dark-fiber parameters
    start: dict = None,
    turns: dict = None,
    behavior: dict = None,
    seed: int = 42,
):
    """Generate a DAS geometry file in PyNetDesign tab-delimited format."""
    if mode == 'borehole':
        coords = generate_borehole_geometry(
            center_x,
            center_y,
            spacing,
            start_depth,
            cable_length,
            azimuth,
            dip,
        )
    elif mode == 'surface':
        coords = generate_surface_geometry(
            center_x,
            center_y,
            spacing,
            depth,
            cable_length,
            surface_shape,
            zigzag_amplitude,
            zigzag_segment_length,
            l_arm_x,
            l_arm_y,
            rect_width,
            rect_height,
            double_line_separation,
        )
    elif mode == 'darkfiber':
        coords = generate_darkfiber_geometry(
            center_x,
            center_y,
            spacing,
            depth,
            cable_length,
            start,
            turns,
            behavior,
            seed,
        )
    else:
        raise ValueError(
            f"Unknown mode: {mode}. Use 'borehole', 'surface', or 'darkfiber'."
        )

    header = (
        f"Northing(m)\tEasting(m)\tElevation(m)\t"
        f"NoiseLevel(1/s)\tGaugeLength={_format_header_value(gauge_length)}(m)"
    )
    lines = [header]

    for x, y, z in coords:
        current_noise = noise_level
        if mode == 'borehole' and surface_noise is not None:
            depth_m = -z
            if depth_m < noise_decay_depth:
                current_noise = surface_noise
            elif depth_m < noise_low_depth:
                log_n0 = np.log(surface_noise)
                log_nf = np.log(noise_level)
                t = (
                    (depth_m - noise_decay_depth)
                    / (noise_low_depth - noise_decay_depth)
                )
                log_n = log_n0 + (log_nf - log_n0) * t
                current_noise = np.exp(log_n)
        lines.append(f"{y:.2f}\t{x:.2f}\t{z:.2f}\t{current_noise:.6e}")

    return lines


def generate_borehole_geometry(
    center_x: float,
    center_y: float,
    spacing: float,
    start_depth: float,
    cable_length: float,
    azimuth: float,
    dip: float,
):
    """Generate borehole DAS channel coordinates."""
    measured_depths = start_depth + _build_sample_distances(cable_length, spacing)

    dip_rad = np.radians(dip)
    az_rad = np.radians(azimuth)

    coords = []
    for measured_depth in measured_depths:
        true_vertical_depth = measured_depth * np.sin(dip_rad)
        horizontal_offset = measured_depth * np.cos(dip_rad)
        dx = horizontal_offset * np.sin(az_rad)
        dy = horizontal_offset * np.cos(az_rad)
        x = center_x + dx
        y = center_y + dy
        coords.append((x, y, -true_vertical_depth))

    return coords


def generate_surface_geometry(
    center_x: float,
    center_y: float,
    spacing: float,
    depth: float,
    cable_length: float,
    shape: str,
    zigzag_amplitude: float,
    zigzag_segment_length: float,
    l_arm_x: float,
    l_arm_y: float,
    rect_width: float,
    rect_height: float,
    double_line_separation: float,
):
    """Generate surface DAS channel coordinates."""
    if shape == 'line':
        waypoints = _surface_line(center_x, center_y, cable_length)
    elif shape == 'zigzag':
        waypoints = _surface_zigzag(
            center_x,
            center_y,
            cable_length,
            zigzag_amplitude,
            zigzag_segment_length,
        )
    elif shape == 'L':
        waypoints = _surface_l(center_x, center_y, l_arm_x, l_arm_y)
    elif shape == 'square':
        waypoints = _surface_square(center_x, center_y, rect_width, rect_height)
    elif shape == 'double_line':
        waypoints = _surface_double_line(
            center_x,
            center_y,
            cable_length,
            double_line_separation,
        )
    else:
        raise ValueError(f"Unknown surface_shape: {shape}")

    return _interpolate_polyline(waypoints, spacing, depth)


def generate_darkfiber_geometry(
    center_x: float,
    center_y: float,
    spacing: float,
    depth: float,
    cable_length: float,
    start: dict = None,
    turns: dict = None,
    behavior: dict = None,
    seed: int = 42,
):
    """Generate a continuous dark-fiber cable path."""
    rng = np.random.RandomState(seed)
    start_segment = _normalize_darkfiber_start(start)

    if turns is None:
        # Turn at one quarter, one half and three quarters of the cable, so that the
        # default layout works for any cable length. For a 24 km cable these are the
        # 6, 12 and 18 km turns used historically.
        turns = {0.25 * cable_length: 0.0,
                 0.50 * cable_length: 90.0,
                 0.75 * cable_length: 0.0}
    if not isinstance(turns, dict):
        raise ValueError("turns must be a dictionary for darkfiber mode.")

    turn_distances = sorted(turns.keys())
    current_dist = 0.0
    for turn_distance in turn_distances:
        if turn_distance <= current_dist or turn_distance >= cable_length:
            raise ValueError(
                "turn distances must be strictly increasing and lie within "
                "cable_length."
            )
        current_dist = turn_distance

    segment_behavior = _normalize_darkfiber_behavior(
        behavior,
        turn_distances,
        start_segment,
    )

    seg_lengths = []
    seg_azimuths = []
    seg_defs = [start_segment]

    current_dist = 0.0
    current_azimuth = start_segment['azimuth']
    for turn_distance in turn_distances:
        seg_lengths.append(turn_distance - current_dist)
        seg_azimuths.append(current_azimuth)
        current_dist = turn_distance
        current_azimuth = turns[turn_distance]
        seg_defs.append(segment_behavior[turn_distance])

    if current_dist < cable_length:
        seg_lengths.append(cable_length - current_dist)
        seg_azimuths.append(current_azimuth)

    all_coords = []
    current_xy = np.array([0.0, 0.0], dtype=float)
    for index, (segment_length, segment_azimuth, segment_def) in enumerate(
        zip(seg_lengths, seg_azimuths, seg_defs)
    ):
        seg_coords = _generate_darkfiber_segment(
            start_xy=current_xy,
            length=segment_length,
            azimuth=segment_azimuth,
            depth=depth,
            spacing=spacing,
            segment=segment_def,
            rng=rng,
        )

        if index > 0:
            seg_coords = seg_coords[1:]
        all_coords.extend(seg_coords)

        if seg_coords:
            current_xy = np.array(seg_coords[-1][:2], dtype=float)

    if not all_coords:
        return []

    all_coords = np.asarray(all_coords, dtype=float)
    if start_segment['start_x'] is not None:
        all_coords[:, 0] += start_segment['start_x']
        all_coords[:, 1] += start_segment['start_y']
    else:
        min_x, max_x = np.min(all_coords[:, 0]), np.max(all_coords[:, 0])
        min_y, max_y = np.min(all_coords[:, 1]), np.max(all_coords[:, 1])
        all_coords[:, 0] += center_x - (min_x + max_x) / 2
        all_coords[:, 1] += center_y - (min_y + max_y) / 2

    return _resample_polyline_coords(all_coords, spacing)


def _build_sample_distances(total_length, spacing):
    """Return cumulative distances sampled at the requested spacing."""
    if spacing <= 0:
        raise ValueError("spacing must be positive")

    total_length = float(total_length)
    n_full_steps = int(np.floor(total_length / spacing))
    sample_s = spacing * np.arange(n_full_steps + 1, dtype=float)

    if sample_s.size == 0:
        sample_s = np.array([0.0], dtype=float)

    if not np.isclose(sample_s[-1], total_length):
        sample_s = np.append(sample_s, total_length)

    return sample_s


def _resample_polyline_coords(coords, spacing):
    """Resample a 3D polyline so channel spacing follows the cable path."""
    coords = np.asarray(coords, dtype=float)

    if coords.ndim != 2 or coords.shape[1] != 3:
        raise ValueError("coords must have shape (n_points, 3)")
    if coords.shape[0] == 0:
        return []
    if coords.shape[0] == 1:
        return [tuple(coords[0])]

    seg_vecs = np.diff(coords, axis=0)
    seg_lens = np.linalg.norm(seg_vecs, axis=1)
    keep = np.concatenate(([True], seg_lens > 0.0))
    coords = coords[keep]

    if coords.shape[0] == 1:
        return [tuple(coords[0])]

    seg_lens = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    cum_len = np.concatenate(([0.0], np.cumsum(seg_lens)))
    sample_s = _build_sample_distances(cum_len[-1], spacing)

    x = np.interp(sample_s, cum_len, coords[:, 0])
    y = np.interp(sample_s, cum_len, coords[:, 1])
    z = np.interp(sample_s, cum_len, coords[:, 2])

    return list(zip(x, y, z))


def _surface_line(center_x, center_y, length):
    """Straight line along the X axis."""
    return [
        (center_x - length / 2, center_y),
        (center_x + length / 2, center_y),
    ]


def _surface_zigzag(center_x, center_y, length, amplitude, segment_length):
    """Zigzag path along the X axis with alternating Y offsets."""
    x_start = center_x - length / 2
    n_seg = int(length / segment_length)
    points = []
    for idx in range(n_seg + 1):
        x = x_start + idx * segment_length
        y = center_y + amplitude * (1 if idx % 2 == 0 else -1)
        points.append((x, y))
    return points


def _surface_l(center_x, center_y, arm_x, arm_y):
    """L-shaped path: horizontal arm followed by vertical arm."""
    return [
        (center_x - arm_x / 2, center_y),
        (center_x + arm_x / 2, center_y),
        (center_x + arm_x / 2, center_y + arm_y),
    ]


def _surface_square(center_x, center_y, width, height):
    """Rectangular perimeter."""
    return [
        (center_x - width / 2, center_y - height / 2),
        (center_x + width / 2, center_y - height / 2),
        (center_x + width / 2, center_y + height / 2),
        (center_x - width / 2, center_y + height / 2),
        (center_x - width / 2, center_y - height / 2),
    ]


def _surface_double_line(center_x, center_y, length, separation):
    """Two parallel lines connected at one end."""
    y1 = center_y - separation / 2
    y2 = center_y + separation / 2
    return [
        (center_x - length / 2, y1),
        (center_x + length / 2, y1),
        (center_x + length / 2, y2),
        (center_x - length / 2, y2),
    ]


def _interpolate_polyline(waypoints, spacing, depth):
    """Interpolate (x, y) waypoints at uniform spacing along the path."""
    elevation = -depth
    coords = [(x, y, elevation) for x, y in waypoints]
    return _resample_polyline_coords(coords, spacing)


def _normalize_darkfiber_start(start):
    """Validate and normalize the first dark-fiber segment definition."""
    defaults = {
        'start_x': None,
        'start_y': None,
        'azimuth': 90.0,
        'behavior': 'sinusoid',
        'sinusoid_amplitude': 500.0,
        'sinusoid_period': 2000.0,
        'amp_variation_amplitude': 200.0,
        'amp_variation_period': 3000.0,
    }

    if start is None:
        start = {}
    if not isinstance(start, dict):
        raise ValueError("start must be a dictionary for darkfiber mode.")

    segment = defaults.copy()
    segment.update(start)

    if segment['behavior'] not in ('straight', 'sinusoid'):
        raise ValueError(
            "start['behavior'] must be either 'straight' or 'sinusoid'."
        )

    if (segment['start_x'] is None) != (segment['start_y'] is None):
        raise ValueError(
            "start['start_x'] and start['start_y'] must be provided together."
        )

    if segment['behavior'] == 'sinusoid':
        for key in (
            'sinusoid_amplitude',
            'sinusoid_period',
            'amp_variation_amplitude',
            'amp_variation_period',
        ):
            if segment[key] is None:
                raise ValueError(
                    f"start['{key}'] is required for sinusoid behavior."
                )

    return segment


def _normalize_darkfiber_behavior(behavior, turn_distances, start_segment):
    """Validate and normalize per-segment behavior definitions."""
    if behavior is None:
        behavior = {td: start_segment['behavior'] for td in turn_distances}
    if not isinstance(behavior, dict):
        raise ValueError("behavior must be a dictionary for darkfiber mode.")

    if set(behavior.keys()) != set(turn_distances):
        raise ValueError(
            "behavior keys must match turns keys exactly for darkfiber mode."
        )

    normalized = {}
    last_sinusoid = {
        'sinusoid_amplitude': start_segment['sinusoid_amplitude'],
        'sinusoid_period': start_segment['sinusoid_period'],
        'amp_variation_amplitude': start_segment['amp_variation_amplitude'],
        'amp_variation_period': start_segment['amp_variation_period'],
    }

    for turn_distance in turn_distances:
        spec = behavior[turn_distance]
        if isinstance(spec, str):
            spec = {'behavior': spec}
        elif isinstance(spec, dict):
            spec = spec.copy()
        else:
            raise ValueError(
                "Each behavior entry must be either a string or a dictionary."
            )

        segment_behavior = spec.get('behavior')
        if segment_behavior not in ('straight', 'sinusoid'):
            raise ValueError(
                f"behavior[{turn_distance}] must define 'straight' or "
                f"'sinusoid' behavior."
            )

        segment = {'behavior': segment_behavior}
        if segment_behavior == 'sinusoid':
            for key in last_sinusoid:
                segment[key] = spec.get(key, last_sinusoid[key])
            last_sinusoid = {key: segment[key] for key in last_sinusoid}

        normalized[turn_distance] = segment

    return normalized


def _generate_darkfiber_segment(start_xy, length, azimuth, depth, spacing,
                                segment, rng):
    """Generate one dark-fiber segment before final spacing resampling."""
    dense_spacing = min(max(spacing / 5.0, 0.5), 2.0)
    sample_s = _build_sample_distances(length, dense_spacing)

    az_rad = np.radians(azimuth)
    tangent = np.array([np.sin(az_rad), np.cos(az_rad)])
    perpendicular = np.array([-tangent[1], tangent[0]])

    base_x = start_xy[0] + sample_s * tangent[0]
    base_y = start_xy[1] + sample_s * tangent[1]
    wobble = np.zeros_like(sample_s)

    if segment['behavior'] == 'sinusoid':
        amp_phase = rng.uniform(0, 2 * np.pi)
        local_amp = (
            segment['sinusoid_amplitude']
            + segment['amp_variation_amplitude']
            * np.sin(
                2 * np.pi * sample_s / segment['amp_variation_period']
                + amp_phase
            )
        )
        wobble = local_amp * np.sin(
            2 * np.pi * sample_s / segment['sinusoid_period']
        )

        taper_radius = min(segment['sinusoid_period'] / 2.0, length / 2.0)
        if taper_radius > 0:
            taper = np.ones_like(sample_s)

            start_mask = sample_s < taper_radius
            taper[start_mask] *= 0.5 * (
                1 - np.cos(np.pi * sample_s[start_mask] / taper_radius)
            )

            end_dist = length - sample_s
            end_mask = end_dist < taper_radius
            taper[end_mask] *= 0.5 * (
                1 - np.cos(np.pi * end_dist[end_mask] / taper_radius)
            )

            wobble *= taper

    x = base_x + wobble * perpendicular[0]
    y = base_y + wobble * perpendicular[1]
    z = np.full_like(sample_s, -depth)
    return list(zip(x, y, z))
