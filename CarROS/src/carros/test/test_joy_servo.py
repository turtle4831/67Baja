from carros.joy_servo import analog_to_us, clamp_us, format_rows, parse_rows, replay_rows


def test_clamp_us():
    assert clamp_us(0) == 0
    assert clamp_us(1500) == 1500
    assert clamp_us(100) == 500
    assert clamp_us(4000) == 2500


def test_analog_to_us():
    assert analog_to_us(0.0) == 1000
    assert analog_to_us(1.0) == 2000
    assert analog_to_us(0.5) == 1500
    assert analog_to_us(0.52) == 1500  # deadzone
    assert analog_to_us(0.9) == 1900


def test_csv_roundtrip():
    rows = [(0.0, 1500.0), (0.02, 1600.5)]
    assert parse_rows(format_rows(rows)) == rows


def test_replay_follows_timestamps():
    sent = []
    now = [0.0]

    def clock():
        return now[0]

    def sleep(dt):
        now[0] += dt

    def set_us(us):
        sent.append((now[0], us))

    replay_rows([(0.0, 1500), (0.1, 1600), (0.25, 1400)], set_us, clock=clock, sleep=sleep)
    assert sent == [(0.0, 1500), (0.1, 1600), (0.25, 1400)]
