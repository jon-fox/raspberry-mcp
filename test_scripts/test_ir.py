# sudo apt update
# sudo apt install python3-rpi.gpio

import RPi.GPIO as GPIO, time

PIN = 17  # GPIO17 (pin 11)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Point a TV remote at the sensor and press buttons… Ctrl+C to stop.")
try:
    while True:
        if GPIO.input(PIN) == 0:  # active low
            print("IR activity")
            while GPIO.input(PIN) == 0:
                pass
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()
