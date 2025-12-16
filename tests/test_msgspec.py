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
