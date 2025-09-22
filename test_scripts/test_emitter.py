try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available - this script requires GPIO support (Linux/Raspberry Pi)")
    exit(1)
import time

PIN = 17  # GPIO17 (pin 11)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

print("Blinking LED...")
for i in range(10):
    GPIO.output(PIN, 1)
    time.sleep(1)
    GPIO.output(PIN, 0)
    time.sleep(1)

GPIO.cleanup()
