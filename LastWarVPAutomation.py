import pyautogui
import time
import re
import pytesseract
from PIL import Image
import cv2
import numpy as np


# Start script on server's position selection screen.
# NOTE: if conquerors buff is enabled, scroll down before running.

# Function to convert HH:mm:ss to total minutes
def time_to_minutes(time_str):
    hours, minutes, _ = map(int, time_str.split(':'))
    return hours * 60 + minutes


def text_sanitization(time_str):
    if not time_str:
        return ''
    if time_str[:3].isdigit():
        time_str = time_str[1:]  # Remove extra leading digit
    parts = time_str.split(':')
    if len(parts) > 2 and len(parts[2]) > 2:
        parts[2] = parts[2][:2]  # Remove extra trailing digit
    return ':'.join(parts)


def remove_stale_roles(left, top, width, height, message, x, y):
    # Define the region to capture (left, top, width, height)
    region = (left, top, width, height)

    # Capture the screen region
    screenshot = pyautogui.screenshot(region=region)
    # Convert to grayscale for processing
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
    # Resize for better OCR accuracy
    resized = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    # Threshold to remove background noise
    _, thresh = cv2.threshold(resized, 180, 255, cv2.THRESH_BINARY)

    # Save processed image for debugging
    cv2.imwrite(f'debug_processed_{message}.png', thresh)

    # OCR configuration to focus on numbers and colons
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789:'
    # Extract text
    text = pytesseract.image_to_string(thresh, config=custom_config)
    # Clean up OCR result
    text = text.replace('\n', '').replace(' ', '')
    print(f"[DEBUG] Raw OCR Text for {message}: {text}")

    # Flexible pattern to handle extra digits
    pattern = r'(\d{1,3}):(\d{1,3}):(\d{1,3})'
    matches = re.findall(pattern, text)

    # Threshold in minutes
    threshold_minutes = 6

    if not matches:
        print(f"{message} Screenshot returned no valid time. Text: {text}")
    else:
        # Process first match (assuming it's the correct time)
        h, m, s = matches[0]
        # Take only last two digits if extra digits exist, pad to 2 digits
        h = h[-2:].zfill(2)
        m = m[-2:].zfill(2)
        s = s[-2:].zfill(2)
        clean_time = f"{h}:{m}:{s}"
        print(f"[DEBUG] Cleaned Time for {message}: {clean_time}")

        # Convert to total minutes
        total_minutes = time_to_minutes(clean_time)
        if total_minutes >= threshold_minutes:
            print(f"{clean_time} {message} is greater than {threshold_minutes} minutes. Removing...")
            pyautogui.click(x, y)  # Click title card
            time.sleep(0.6)
            pyautogui.click(197, 835)  # Click dismiss
            time.sleep(0.6)
            pyautogui.click(192, 564)  # Click Confirm
            time.sleep(0.6)
            # Exit position card
            exitX, exitY = 245, 941
            pyautogui.click(exitX, exitY)
            time.sleep(0.6)
            pyautogui.click(exitX, exitY)
            time.sleep(0.6)
        else:
            print(f"{clean_time} {message} is less than {threshold_minutes} minutes.")



def refresh_positions():
    # Click back arrow button to exit position card screen
    pyautogui.click(47, 928)
    time.sleep(1.3)
    # Click back into capitol
    pyautogui.click(390, 511)
    time.sleep(1)
    # Scroll down to re-center screen
    pyautogui.moveTo(278, 1048)
    pyautogui.mouseDown()
    pyautogui.moveTo(2208, 870, duration=0.5)
    # Release the mouse button
    pyautogui.mouseUp()
    time.sleep(.3)


def approve_applicant_list(x, y):
    # Click the position card from given coordinates.
    # click the approve button location a few times. Then exit out of the position card.
    clickSeconds1 = .65
    clickSeconds2 = .35

    # click position card
    pyautogui.click(x, y)
    time.sleep(clickSeconds1)
    # click list button
    listX = 461
    listY = 834
    pyautogui.click(listX, listY)
    time.sleep(clickSeconds1)
    # scroll up twice to avoid approving players lower in the queue
    pyautogui.moveTo(207, 235)
    pyautogui.mouseDown()
    pyautogui.moveTo(213, 361, duration=0.15)
    pyautogui.mouseUp()
    time.sleep(.15)
    pyautogui.moveTo(207, 235)
    pyautogui.mouseDown()
    pyautogui.moveTo(213, 361, duration=0.18)
    pyautogui.mouseUp()
    time.sleep(.3)
    # click approve
    approveX = 388
    approveY = 253
    for i in range(3):
        pyautogui.click(approveX, approveY)
        time.sleep(clickSeconds2)
    # exit position card
    exitX = 257
    exitY = 940
    pyautogui.click(exitX, exitY)
    time.sleep(clickSeconds2)
    pyautogui.click(exitX, exitY)
    time.sleep(clickSeconds1)
    return True


def main():
    # Conquerors Buff includes two additional position cards. Set to False if conquerors buff is disabled.
    conquerorsBuff = False
    # list of coordinates for each position card, ordered Mil Cmdr to Sec Interior top left to bottom right
    if conquerorsBuff:
        coordinates = [
            (2109, 441),  # Military Commander
            (2316, 425),  # Administration Commander
            (2212, 677),  # Secretary of Strategy...
            (2396, 636),
            (2053, 973),
            (2209, 850),
            # Note, a player liking the bot's profile makes a permanent screen appear. This may be exitited via the "Awesome" button.
            (2383, 955)
        ]

        staleRoleCoordinates = [
            (2083, 485, 77, 24, 'Military Commander', 2109, 441),
            (2293, 485, 77, 24, 'Administrative Commander', 2316, 425),
            (2184, 718, 106, 27, 'Secretary of Strategy', 2212, 677),
            (2366, 718, 106, 27, 'Secretary of Security', 2396, 636),
            (2002, 951, 106, 27, 'Secretary of Development', 2053, 973),
            (2184, 951, 106, 27, 'Secretary of Science', 2209, 850)
        ]
    else:
        coordinates = [
            (270, 524),  # Secretary of Strategy...
            (432, 534),
            (114, 719),
            (279, 733),
            (431, 729)
            # Note, a player liking the bot's profile makes a permanent screen appear. This may be exitited via the 'Awesome' button.

        ]
        staleRoleCoordinates = [
            (218, 418, 112, 172, 'Secretary of Strategy', 277, 547),
            (364, 423, 116, 171, 'Secretary of Security', 422, 555),
            (59, 617, 116, 179, 'Secretary of Development', 119, 746),
            (205, 614, 112, 172, 'Secretary of Science', 264, 756),
            (373, 616, 117, 175, 'Secretary of Interior', 425, 754),
        ]
    time.sleep(5)  # giving time to get screen ready
    i = 9
    while True:
        i += 1
        # Iterate through the positions and approve all
        for x, y in coordinates:
            action = approve_applicant_list(x, y)
        if i % 5 == 0:
            refresh_positions()
            # Iterate through positions to check for stale activity
            for left, top, width, height, message, x, y in staleRoleCoordinates:
                remove_stale_roles(left, top, width, height, message, x, y)
        time.sleep(4)  # giving operator time to stop the script


if __name__ == "__main__":
    main()
