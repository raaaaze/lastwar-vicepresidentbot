import pyautogui  # Automates mouse and keyboard actions
import time  # Handles time delays
import re  # For regular expressions to process text
import pytesseract  # OCR (Optical Character Recognition) for reading text from images
import keyboard  # Listens for keyboard input to stop script
import threading  # Allows running keyboard listener separately from main loop
from PIL import Image  # Handles image processing
import cv2  # OpenCV for advanced image processing
import numpy as np  # Handles arrays for image manipulation
from datetime import datetime  # Manages timestamps for logging

# Global variable to track whether the script should stop
stop_script = False

# Function to listen for 's' key and stop the script
def listen_for_stop():
    global stop_script
    keyboard.wait("s")  # Wait until 's' key is pressed
    stop_script = True  # Set stop flag to True
    print("\n[SYSTEM] Stop key detected. Exiting script...")

# Start the key listener in a separate thread so it runs in the background
threading.Thread(target=listen_for_stop, daemon=True).start()

# Function to log actions (prints messages and writes them to a log file)
def log_action(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time
    log_message = f"[{timestamp}] {message}"  # Format log message
    print(log_message)  # Print message to console
    with open("stale_roles_log.txt", "a") as log_file:
        log_file.write(log_message + "\n")  # Append message to log file

# Function to convert HH:mm:ss time format to total minutes
def time_to_minutes(time_str):
    hours, minutes, sec = map(int, time_str.split(':'))  # Split into hours, minutes, seconds
    return hours * 60 + minutes + sec / 60  # Convert to total minutes

# Function to sanitize and fix OCR (Optical Character Recognition) text strings
def text_sanitization(text):
    if not text:
        return ''
    # Fix improperly formatted times (e.g., missing leading zeros)
    text = re.sub(r'^\d+:(\d{1,3}):(\d{1,3})', r'00:\1:\2', text)
    return text


def check_and_navigate_to_role_screen():
    global stop_script
    if stop_script: return False  # Stop if 's' was pressed

    # Take a screenshot of a specific region where a unique element of the role selection screen appears
    region = (20, 54, 196, 58)  # Adjust coordinates as needed
    screenshot = pyautogui.screenshot(region=region)

    # Convert to grayscale and process for OCR
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    # Extract text using OCR
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, config=custom_config).strip()
    #print(text)
    text = re.sub(r'#\d+', '#116', text)  # Replace any # followed by numbers with #116
    text = re.sub(r'[^#0-9a-zA-Z ]', '', text)  # Keep only allowed characters
    # Check if the text matches expected elements of the role selection screen
    if "#116" in text:
        #log_action("Role selection screen detected.")
        return True  # Already on the correct screen
    else:
        log_action("Not on role selection screen. Checking intermediate screen...")
        pyautogui.click(564, 866)  # Click Bluestacks back button
        time.sleep(1)
        # Read another screen first to determine next steps
        region_secondary = (135, 423, 241, 70)  # Main Page
        screenshot_secondary = pyautogui.screenshot(region=region_secondary)
        gray_secondary = cv2.cvtColor(np.array(screenshot_secondary), cv2.COLOR_BGR2GRAY)
        _, thresh_secondary = cv2.threshold(gray_secondary, 180, 255, cv2.THRESH_BINARY)
        text_secondary = pytesseract.image_to_string(thresh_secondary, config=custom_config).strip()
        #print(screenshot_secondary)
        if "Quit" in text_secondary:  # Adjust expected text
            log_action("Detected intermediate screen. Proceeding...")
            pyautogui.click(185, 568)  # Click Cancel
            time.sleep(1)
            pyautogui.click(51, 93)  # Click Profile
            time.sleep(1)
            pyautogui.click(365, 512)  # Click Role Selection
            time.sleep(2)
        else:
            log_action("Intermediate screen not detected. Navigating manually...")
            pyautogui.click(564, 866)  # Click Bluestacks back button
            time.sleep(1)
            pyautogui.click(51, 93)  # Click Profile
            time.sleep(1)
            pyautogui.click(365, 512)  # Click Role Selection
            time.sleep(2)
    return check_and_navigate_to_role_screen()


# Function to remove stale roles based on timer detected using OCR
def remove_stale_roles(left, top, width, height, message, x, y):
    global stop_script
    if stop_script: return False  # Stop if 's' was pressed

    if not check_and_navigate_to_role_screen():
        return  # Exit if unable to navigate

    # Take a screenshot of the specified region
    region = (left, top, width, height)
    screenshot = pyautogui.screenshot(region=region)

    # Convert screenshot to grayscale for better OCR accuracy
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

    # Resize image to improve OCR accuracy
    resized = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # Apply thresholding to make text more distinct
    _, thresh = cv2.threshold(resized, 180, 255, cv2.THRESH_BINARY)

    # Extract text using OCR (only digits and colons are allowed)
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789:'
    text = pytesseract.image_to_string(thresh, config=custom_config).replace('\n', '').replace(' ', '')

    log_action(f"Raw OCR Text for {message}: {text}")  # Log raw OCR output
    text = text_sanitization(text)  # Fix formatting errors
    log_action(f"Sanitized OCR Text for {message}: {text}")  # Log sanitized text

    # Regex pattern to extract HH:mm:ss format times
    pattern = r'(\d{1,3}):(\d{1,3}):(\d{1,3})'
    matches = re.findall(pattern, text)

    threshold_minutes = 5.2  # Minimum time before removing a role

    if not matches:
        log_action(f"{message} Screenshot returned no valid time. Text: {text}")
        return True  # Continue execution

    # Extract hours, minutes, seconds from OCR result
    h, m, s = matches[0]
    clean_time = f"{h[-2:].zfill(2)}:{m[-2:].zfill(2)}:{s[-2:].zfill(2)}"
    log_action(f"Cleaned Time for {message}: {clean_time}")

    # Convert extracted time to total minutes
    total_minutes = time_to_minutes(clean_time)
    #print(total_minutes)

    # If the role is stale (greater than threshold), remove it
    if total_minutes >= threshold_minutes:
        log_action(f"{clean_time} {message} is greater than {threshold_minutes} minutes. Removing...")
        pyautogui.click(x, y)  # Click on the role
        time.sleep(0.6)
        pyautogui.click(197, 835)  # Confirm remove
        time.sleep(0.6)
        pyautogui.click(192, 564)  # Confirm again
        time.sleep(0.6)
        pyautogui.click(245, 941)  # Exit
        time.sleep(0.6)
        pyautogui.click(245, 941)  # Double exit
        time.sleep(0.6)

    return True  # Continue execution

# Function to refresh the list of applicants
def refresh_positions():
    global stop_script
    if stop_script: return  # Stop if 's' was pressed

    pyautogui.click(47, 928)  # Click refresh button
    time.sleep(1.3)
    pyautogui.click(390, 511)  # Click confirmation
    time.sleep(3)

    if not check_and_navigate_to_role_screen():
        return  # Exit if unable to navigate

    time.sleep(3)

    # Scroll through applicants list
    pyautogui.moveTo(278, 1048)
    pyautogui.mouseDown()
    pyautogui.moveTo(2208, 870, duration=0.5)
    pyautogui.mouseUp()
    time.sleep(0.3)

# Function to approve all applicants in the list
def approve_applicant_list(x, y):
    global stop_script
    if stop_script: return False  # Stop if 's' was pressed

    if not check_and_navigate_to_role_screen():
        return  # Exit if unable to navigate

    time.sleep(0.45)
    pyautogui.click(x, y)  # Click on applicant
    time.sleep(0.6)
    pyautogui.click(461, 834)  # Click approve button
    time.sleep(0.45)

    # Scroll through the list of applicants
    for _ in range(3):
        pyautogui.moveTo(189, 235)
        pyautogui.mouseDown()
        pyautogui.moveTo(189, 700, duration=0.18)
        pyautogui.mouseUp()
        time.sleep(0.15)

    # Click approve on multiple applicants
    for _ in range(4):
        pyautogui.click(388, 253)
        time.sleep(0.25)

    pyautogui.click(257, 940)  # Exit screen
    time.sleep(0.25)
    pyautogui.click(257, 940)  # Double exit
    time.sleep(0.45)

    return True  # Continue execution

# Main script logic
def main():
    global stop_script
    log_action("Script started. Press 's' to stop.")

    if not check_and_navigate_to_role_screen():
        return  # Exit if unable to navigate

    # Define coordinates for applicant approval
    coordinates = [(270, 524), (432, 534), (114, 719), (279, 733), (431, 729)]

    # Define coordinates for checking stale roles
    staleRoleCoordinates = [
        (218, 418, 112, 172, 'Secretary of Strategy', 277, 547),
        (364, 423, 116, 171, 'Secretary of Security', 422, 555),
        (59, 617, 116, 179, 'Secretary of Development', 119, 746),
        (205, 614, 112, 172, 'Secretary of Science', 264, 756),
        (373, 616, 117, 175, 'Secretary of Interior', 425, 754),
    ]

    time.sleep(3)  # Delay before execution starts
    i = 9

    while not stop_script:  # Loop runs until 's' is pressed
        i += 1
        for x, y in coordinates:
            if not approve_applicant_list(x, y):
                return  # Exit if stopped

        if i % 3 == 0:
            refresh_positions()
            for left, top, width, height, message, x, y in staleRoleCoordinates:
                if not remove_stale_roles(left, top, width, height, message, x, y):
                    return  # Exit if stopped

        time.sleep(4)  # Short delay between cycles

    log_action("Script stopped.")

if __name__ == "__main__":
    main()
