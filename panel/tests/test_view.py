from view import category_color, centroid, components_frame, ndvi_frame


def test_ndvi_frame_sorts_and_parses_dates():
    frame = ndvi_frame(
        {
            "ndvi": [
                {"period": "2020-02-01", "ndvi_mean": 0.7},
                {"period": "2020-01-01", "ndvi_mean": 0.8},
            ]
        }
    )
    assert list(frame["ndvi_mean"]) == [0.8, 0.7]


def test_ndvi_frame_handles_empty_series():
    assert ndvi_frame({"ndvi": []}).empty


def test_components_frame_skips_private_keys():
    frame = components_frame({"permanencia": {"puntaje": 90}, "_sensor": "s2"})
    assert list(frame["componente"]) == ["permanencia"]


def test_category_color_has_neutral_default():
    assert category_color("Alta") != category_color("Baja")
    assert category_color("otro") == category_color("Insuficiente")


def test_centroid_of_polygon():
    feature = {
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]}
    }
    lat, lon = centroid(feature)
    assert 0 < lat < 2 and 0 < lon < 2
