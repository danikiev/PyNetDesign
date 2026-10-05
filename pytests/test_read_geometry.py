import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

from pynetdesign.modelling.io import read_geometry

# Sample files shipped with the repository, resolved from this file rather than from
# the working directory, so that the tests pass wherever pytest is invoked from
REPO_ROOT = Path(__file__).resolve().parents[1]

# Define paths to existing sample files with expected values
EXISTING_FILES = [
    (str(REPO_ROOT / "data/stations/local_geometry.txt"), None, "m/s", "velocity","local"),
    (str(REPO_ROOT / "data/stations/global_geometry.txt"), None, "m/s^2", "acceleration","global")
]

@pytest.fixture(params=[
    ("""Name Latitude(WGS84) Longitude(WGS84) Elevation NoiseLevel(m/s^2) GaugeLength=1.5(m)
    A    37.7749        -122.4194        10.5       0.001
    B    34.0522        -118.2437        20.0       0.002
    C    40.7128        -74.0060         15.3       0.0015
    """, 1.5, "m/s^2", "acceleration","global"),
    ("""Name Latitude(WGS84) Longitude(WGS84) Elevation(m) NoiseLevel(1/s) GaugeLength=2.0(cm)
    D    35.6895        139.6917         12.0       0.0005
    E    51.5074        -0.1278          25.0       0.0008
    """, 0.02, "1/s", "strain rate","global"),
    ("""Name Latitude(WGS84) Longitude(WGS84) Elevation(ft) NoiseLevel(m) GaugeLength=3.5(ft)
    F    -33.8688       151.2093         5.0        0.003
    G    48.8566        2.3522           18.0       0.0012
    """, 1.0668, "m", "displacement","global")
] + EXISTING_FILES)

def sample_geometry_file(request):
    """Creates temporary sample geometry files for testing or uses existing files."""
    if isinstance(request.param, tuple):
        file_path, expected_gauge_length, expected_noise_unit, expected_noise_type, expected_coordinate_system = request.param
    else:
        file_path = request.param
        expected_gauge_length = None
        expected_noise_unit = None
        expected_noise_type = None

    if os.path.exists(file_path):
        yield file_path, expected_gauge_length, expected_noise_unit, expected_noise_type, expected_coordinate_system
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        temp_file.write(file_path)
        temp_file.close()
        yield temp_file.name, expected_gauge_length, expected_noise_unit, expected_noise_type, expected_coordinate_system
        os.remove(temp_file.name)  # Cleanup after test

def test_read_geometry(sample_geometry_file):
    """Test the read_geometry function with multiple sample files."""
    file_path, expected_gauge_length, expected_noise_unit, expected_noise_type, expected_coordinate_system = sample_geometry_file
    df = read_geometry(file_path)

    # Check if DataFrame is not empty
    assert isinstance(df, pd.DataFrame), "The function should return a DataFrame."
    assert not df.empty, "DataFrame should not be empty."

    # Check expected columns exist
    expected_columns = {'Name', 'X', 'Y', 'Z', 'NoiseLevel'}
    assert expected_columns.issubset(df.columns), f"Missing expected columns: {expected_columns - set(df.columns)}"

    # Check metadata
    assert df.attrs['_is_combined'] is False, "Geometry should not be marked as combined."    
    #assert 'gauge_length' in df.attrs, "Gauge length should be present in attributes."
    assert 'noise_unit' in df.attrs, "Noise unit should be present in attributes."
    assert 'noise_type' in df.attrs, "Noise type should be present in attributes."
    assert 'coordinate_system' in df.attrs, "Coordinate system should be present in attributes."

    # Check specific expected values if provided
    if expected_gauge_length is not None:
        assert df.attrs['gauge_length'] == pytest.approx(expected_gauge_length, rel=1e-3), "Gauge length is incorrect."
    if expected_noise_unit is not None:
        assert df.attrs['noise_unit'] == expected_noise_unit, "Noise unit is incorrect."
    if expected_noise_type is not None:
        assert df.attrs['noise_type'] == expected_noise_type, "Noise type is incorrect."
    if expected_coordinate_system is not None:
        assert df.attrs['coordinate_system'] == expected_coordinate_system, "Coordinate system is incorrect."
