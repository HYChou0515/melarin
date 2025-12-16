def test_msgspec():
    import melarin
    import datetime as dt

    msg = [
        0,
        0.75,
        1 + 0.5j,
        1 - 0.5j,
        dt.datetime(2024, 1, 1, 12, 0, 0),
        dt.timedelta(days=5, hours=3),
    ]
    buf = melarin.enc(msg)
    msg2 = melarin.dec(buf)
    assert msg == msg2


def test_numpy():
    import melarin
    import numpy as np

    msg = {
        "a": np.arange(10),
        "b": np.float128(1.5),
        "c": np.uint8(7),
        "d": 123.4,
        "e": np.array([[1, 2, 3], [4, 5, 6], ["7", "8", "9"]]),
    }
    buf = melarin.enc(msg)
    msg2 = melarin.dec(buf)

    for key in msg:
        assert np.all(msg[key] == msg2[key])


def test_pandas():
    import melarin
    import pandas as pd
    import numpy as np

    msg = {
        "a": pd.DataFrame(
            np.arange(12).reshape(3, 4), columns=list("ABCD"), index=list("xyz")
        ),
        "c": pd.Series(np.arange(12), name="series"),
    }
    buf = melarin.enc(msg)
    msg2 = melarin.dec(buf)

    for key in msg:
        if isinstance(msg[key], pd.Series):
            pd.testing.assert_series_equal(msg[key], msg2[key])
        else:
            pd.testing.assert_frame_equal(msg[key], msg2[key])
