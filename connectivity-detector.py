import RPi.GPIO as GPIO
import time
import subprocess
import re

LED_RED = 14
LED_YELLOW = 15
LED_GREEN = 18

GPIO.setmode (GPIO.BCM)
GPIO.setup (LED_RED, GPIO.OUT)
GPIO.setup (LED_GREEN, GPIO.OUT)
GPIO.setup (LED_YELLOW, GPIO.OUT)

cmd = ['ping', '-c 1', 'google.de']
cmd2 = ['cat', '/proc/net/wireless']

time_pattern = re.compile(r'time=([\d.]+)\s*ms')

def extract_level(text):
    pattern = r'wlan0:\s+(\d+\.)\s+-\d+\.\s+-\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None
    

def getLevel(text):
    index = text.find("0000")
    newindex = index + 13
    return text[newindex:newindex+2]

while True:
    result = subprocess.run(cmd2, capture_output=True, text=True)
    output = result.stdout.strip()
    # matches = time_pattern.findall(output)
    matches = getLevel(output)
    print(matches)
    # if matches:
    time_in_ms = float(matches)
    print(f'Time: {time_in_ms}')
    if time_in_ms < 55:
        GPIO.output(LED_GREEN, True)
        GPIO.output(LED_RED, False)
        GPIO.output(LED_YELLOW, False)
    if (time_in_ms <= 60 and time_in_ms >= 55):
        GPIO.output(LED_YELLOW, True)
        GPIO.output(LED_RED, False)
        GPIO.output(LED_GREEN, False)
    if time_in_ms > 60:
        GPIO.output(LED_RED, True)
        GPIO.output(LED_GREEN, False)
        GPIO.output(LED_YELLOW, False)
    # else:
    #     print('Time not found in the input string.')
    time.sleep(1)
