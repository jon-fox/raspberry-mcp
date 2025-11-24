# sweep_loopback.py  (TX=GPIO17 pin11, RX=GPIO27 pin13)
# sudo systemctl start pigpiod
import pigpio
import time

TX, RX = 17, 27
FREQS = [36000, 38000, 40000]  # try common carriers
DUTY = 200  # stronger drive (0-255)
BURST = 0.5  # seconds on
GAPS = 0.3
REPS = 6

pi = pigpio.pi()
assert pi.connected, "Start pigpio: sudo systemctl start pigpiod"
pi.set_mode(TX, pigpio.OUTPUT)
pi.set_mode(RX, pigpio.INPUT)
pi.set_pull_up_down(RX, pigpio.PUD_UP)


def measure():
    edges = 0

    def cbf(g, level, t):
        nonlocal edges
        if level == 0:
            edges += 1

    cb = pi.callback(RX, pigpio.EITHER_EDGE, cbf)
    for f in FREQS:
        pi.set_PWM_frequency(TX, f)
        print(f"Testing {f/1000:.0f} kHz ...")
        for _ in range(REPS):
            pi.set_PWM_dutycycle(TX, DUTY)
            time.sleep(BURST)
            pi.set_PWM_dutycycle(TX, 0)
            time.sleep(GAPS)
        print("  edges:", edges)
    cb.cancel()
    pi.set_PWM_dutycycle(TX, 0)
    return edges


e = measure()
pi.stop()
print("RESULT:", "PASS" if e > 0 else "FAIL")
