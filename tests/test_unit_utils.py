import pytest

from pepys_import.utils import unit_utils
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location


@pytest.mark.parametrize(
    "input,actual_result",
    [
        pytest.param(50, 50, id="float"),
        pytest.param("75", 75, id="string"),
        pytest.param(-20, 340, id="negative angle"),
        pytest.param(500, 140, id="angle above 360"),
    ],
)
def test_convert_abs_angle_valid(input, actual_result):
    errors = []
    error_type = "test"

    result = unit_utils.convert_absolute_angle(input, 0, errors, error_type)

    assert result == actual_result * unit_registry.degree


def test_convert_abs_angle_invalid():
    errors = []
    error_type = "test"

    result = unit_utils.convert_absolute_angle("blah", 0, errors, error_type)

    assert result is False
    assert len(errors) == 1
    assert "Error in angle value" in errors[0]["test"]


@pytest.mark.parametrize(
    "input,units,actual_result",
    [
        pytest.param(
            20, unit_registry.knots, 20 * unit_registry.knots, id="float knots"
        ),
        pytest.param(
            "50", unit_registry.knots, 50 * unit_registry.knots, id="string knots"
        ),
        pytest.param(
            2.8,
            (unit_registry.metre / unit_registry.second),
            2.8 * (unit_registry.metre / unit_registry.second),
            id="mps",
        ),
    ],
)
def test_convert_speed_valid(input, units, actual_result):
    errors = []
    error_type = "test"

    result = unit_utils.convert_speed(input, units, 0, errors, error_type)

    assert result == actual_result


def test_convert_speed_invalid():
    errors = []
    error_type = "test"

    result = unit_utils.convert_speed(
        "blah", unit_registry.knots, 0, errors, error_type
    )

    assert result is False
    assert len(errors) == 1
    assert "Error in speed value" in errors[0]["test"]


def test_extract_points():
    loc = Location()
    loc.set_latitude_decimal_degrees(26.3)
    loc.set_longitude_decimal_degrees(-40.7)

    lon_rads, lat_rads = unit_utils.extract_points(loc)

    assert lon_rads == -0.7103490055616922
    assert lat_rads == 0.4590215932745087


@pytest.mark.parametrize(
    "input,units,actual_result",
    [
        pytest.param(
            340, unit_registry.hertz, 340 * unit_registry.hertz, id="float hertz"
        ),
        pytest.param(
            "50", unit_registry.hertz, 50 * unit_registry.hertz, id="string hertz"
        ),
    ],
)
def test_convert_frequency_valid(input, units, actual_result):
    errors = []
    error_type = "test"

    result = unit_utils.convert_frequency(input, units, 0, errors, error_type)

    assert result == actual_result


def test_convert_frequency_invalid():
    errors = []
    error_type = "test"

    result = unit_utils.convert_frequency(
        "blah", unit_registry.hertz, 0, errors, error_type
    )

    assert result is False
    assert len(errors) == 1
    assert "Error in frequency value" in errors[0]["test"]


@pytest.mark.parametrize(
    "input,units,actual_result",
    [
        pytest.param(
            2.5, unit_registry.kilometre, 2.5 * unit_registry.kilometre, id="float km"
        ),
        pytest.param(
            "50", unit_registry.metre, 50 * unit_registry.metre, id="string metre"
        ),
    ],
)
def test_convert_distance_valid(input, units, actual_result):
    errors = []
    error_type = "test"

    result = unit_utils.convert_distance(input, units, 0, errors, error_type)

    assert result == actual_result


def test_convert_distance_invalid():
    errors = []
    error_type = "test"

    result = unit_utils.convert_distance(
        "blah", unit_registry.metre, 0, errors, error_type
    )

    assert result is False
    assert len(errors) == 1
    assert "Error in distance value" in errors[0]["test"]


def test_dist_between_two_points():
    loc1 = Location()
    loc1.set_latitude_decimal_degrees(30.5)
    loc1.set_longitude_decimal_degrees(-67.2)

    loc2 = Location()
    loc2.set_latitude_decimal_degrees(60.7)
    loc2.set_longitude_decimal_degrees(153.2)

    result = unit_utils.distance_between_two_points_haversine(loc1, loc2)

    # TODO Fix distance_between_two_points_haversine and update this
    # test


def test_bearing_between_two_points():
    loc1 = Location()
    loc1.set_latitude_decimal_degrees(30.5)
    loc1.set_longitude_decimal_degrees(-67.2)

    loc2 = Location()
    loc2.set_latitude_decimal_degrees(60.7)
    loc2.set_longitude_decimal_degrees(153.2)

    result = unit_utils.bearing_between_two_points(loc1, loc2)

    assert result == pytest.approx(341.3645)
