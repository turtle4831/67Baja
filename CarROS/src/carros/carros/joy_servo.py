"""Pi GPIO: analog joystick VRy (via ADS1115) drives a servo on GP17. Record, then replay.

The stick is analog (GND / VCC / VRx / VRy / SW). A Pi 4 GPIO cannot read VRy.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import io
import os
import struct
import time

SERVO_GPIO = 17
I2C_SLAVE = 0x0703
ADS1115_ADDR = 0x48
MIN_US = 500
MAX_US = 2500
SERVO_LO = 1000
SERVO_HI = 2000


def clamp_us(us):
    if us <= 0:
        return 0
    return max(MIN_US, min(MAX_US, int(round(us))))


def analog_to_us(frac, lo=SERVO_LO, hi=SERVO_HI, dead=0.05):
    """Map 0..1 joystick fraction to servo pulse us. Deadzone around center."""
    frac = min(1.0, max(0.0, float(frac)))
    if abs(frac - 0.5) < dead:
        frac = 0.5
    return int(round(lo + frac * (hi - lo)))


def format_rows(rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['t', 'us'])
    for t, us in rows:
        w.writerow([f'{t:.4f}', f'{us:.1f}'])
    return buf.getvalue()


def parse_rows(text):
    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        rows.append((float(row['t']), float(row['us'])))
    return rows


def read_csv_file(path):
    with open(path, newline='') as f:
        return parse_rows(f.read())


def write_csv_file(path, rows):
    with open(path, 'w', newline='') as f:
        f.write(format_rows(rows))


def replay_rows(rows, set_us, clock=time.monotonic, sleep=time.sleep):
    if not rows:
        return
    t0 = clock()
    for t, us in rows:
        wait = t - (clock() - t0)
        if wait > 0:
            sleep(wait)
        set_us(us)


def _open_lgpio():
    try:
        import lgpio
    except ImportError as e:
        raise SystemExit('python3-lgpio is missing; on the Pi: sudo apt install python3-lgpio') from e
    return lgpio, lgpio.gpiochip_open(0)


class Servo:
    def __init__(self, lgpio, handle, gpio=SERVO_GPIO):
        self._lgpio = lgpio
        self._h = handle
        self._gpio = gpio
        self._on = False
        lgpio.gpio_claim_output(handle, gpio)

    def set_us(self, us):
        width = clamp_us(us)
        self._lgpio.tx_servo(self._h, self._gpio, width)
        self._on = width > 0

    def off(self):
        # tx_servo(0) errors if no pulse was ever started.
        if self._on:
            self._lgpio.tx_servo(self._h, self._gpio, 0)
            self._on = False


class Ads1115:
    """AIN0 vs GND, continuous, ±4.096 V. ponytail: no smbus, just /dev/i2c-1."""

    def __init__(self, bus=1, addr=ADS1115_ADDR):
        path = f'/dev/i2c-{bus}'
        try:
            self.fd = os.open(path, os.O_RDWR)
        except OSError as e:
            raise SystemExit(f'cannot open {path}: {e}') from e
        try:
            fcntl.ioctl(self.fd, I2C_SLAVE, addr)
            # config: AIN0/GND, PGA 4.096V, continuous, 128 SPS, comparator off
            os.write(self.fd, bytes([0x01, 0x42, 0x83]))
            os.write(self.fd, b'\x00')
            time.sleep(0.01)
            if len(os.read(self.fd, 2)) != 2:
                raise OSError('short read')
        except OSError as e:
            os.close(self.fd)
            raise SystemExit(_no_adc_msg(e)) from e

    def fraction(self, vref=3.3):
        os.write(self.fd, b'\x00')
        data = os.read(self.fd, 2)
        raw = struct.unpack('>h', data)[0]
        volts = raw * 4.096 / 32767.0
        return min(1.0, max(0.0, volts / vref))

    def close(self):
        os.close(self.fd)


def _no_adc_msg(err):
    return (
        f'no ADS1115 on I2C ({err}).\n'
        'This joystick VRy is analog. A Pi 4 GPIO cannot read it — unplug VRy from GP18\n'
        '(full-scale 5V can damage that pin).\n'
        'Wire VRy to ADS1115 A0, joystick VCC to 3.3V (not 5V), ADS1115 SDA/SCL to GP2/GP3.\n'
        'Servo stays on GP17. See README.'
    )


def record(path, seconds, servo_gpio, i2c_addr):
    joy = Ads1115(addr=i2c_addr)
    lgpio, handle = _open_lgpio()
    servo = None
    rows = []
    t0 = time.monotonic()
    deadline = (t0 + seconds) if seconds else None
    try:
        servo = Servo(lgpio, handle, servo_gpio)
        print(f'recording VRy -> GP{servo_gpio} to {path} (Ctrl+C to stop)', flush=True)
        last_log = 0.0
        while True:
            now = time.monotonic()
            if deadline is not None and now >= deadline:
                break
            us = analog_to_us(joy.fraction())
            t = now - t0
            servo.set_us(us)
            rows.append((t, us))
            if t - last_log >= 0.5:
                print(f'  t={t:.1f}s  {us} us', flush=True)
                last_log = t
            time.sleep(0.02)
    except KeyboardInterrupt:
        print()
    finally:
        write_csv_file(path, rows)
        if servo is not None:
            servo.off()
        joy.close()
        lgpio.gpiochip_close(handle)
        print(f'wrote {len(rows)} samples to {path}')


def replay(path, servo_gpio):
    rows = read_csv_file(path)
    if not rows:
        raise SystemExit(f'{path} has no samples')
    lgpio, handle = _open_lgpio()
    servo = Servo(lgpio, handle, servo_gpio)
    print(f'replaying {len(rows)} samples from {path} on GP{servo_gpio}', flush=True)
    try:
        replay_rows(rows, servo.set_us)
    except KeyboardInterrupt:
        print()
    finally:
        servo.off()
        lgpio.gpiochip_close(handle)


def main(argv=None):
    p = argparse.ArgumentParser(description='Record analog joystick VRy to a servo, then replay it.')
    p.add_argument('mode', choices=['record', 'replay'])
    p.add_argument('--file', default='joy_servo.csv')
    p.add_argument('--servo', type=int, default=SERVO_GPIO)
    p.add_argument('--i2c-addr', type=lambda s: int(s, 0), default=ADS1115_ADDR)
    p.add_argument('--seconds', type=float, default=0, help='record duration; 0 = until Ctrl+C')
    args = p.parse_args(argv)
    if args.mode == 'record':
        record(args.file, args.seconds, args.servo, args.i2c_addr)
    else:
        replay(args.file, args.servo)


if __name__ == '__main__':
    main()
