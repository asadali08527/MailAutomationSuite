from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

from urllib.parse import urlparse, parse_qs

import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up the Chrome WebDriver
service = Service('C:\\Users\\91706\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')  # Update the path to your chromedriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=service, options=options)

try:
    # Launch the email URL
    url = "https://privateemail.com/appsuite/#!!&app=io.ox/mail&folder=default0/INBOX&storeLocale=true"
    driver.get(url)
    logging.info("Launched the email URL")

    # Wait for the page to load
    wait = WebDriverWait(driver, 20)

    # Log in to the email account (add your credentials here)
    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#txtMailbox")))
    password = driver.find_element(By.CSS_SELECTOR, "#txtPwd")
    username.send_keys("")
    password.send_keys("")
    logging.info("Entered login credentials")

    try:
        overlay_close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".reject-btn-container button")))
        overlay_close_button.click()
        logging.info("Closed overlay or cookie consent banner")
    except TimeoutException:
        logging.info("No overlay or cookie consent banner found")

    # Click the login button
    try:
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnLogin")))
        login_button.click()
        logging.info("Clicked login button")
    except ElementClickInterceptedException:
        logging.warning("Login button click intercepted, using JavaScript to click instead")
        driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "#btnLogin"))
        logging.info("Clicked login button using JavaScript")
    
    # Wait for the inbox to load
    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[2]/div[1]/div/div/div/div[4]/div[3]/div[1]/div[3]/ul[2]")))
    logging.info("Inbox loaded successfully")
    # Check unread emails and reply
    email_index = 40  # Start with the given index
    while True:
        try:
            
            # Locate the unread email
            email_xpath = f"/html/body/div[3]/div[2]/div[1]/div/div/div/div[4]/div[3]/div[1]/div[3]/ul[2]/li[{email_index}]"
            email_element = driver.find_element(By.XPATH, email_xpath)
            try:
                # Scroll into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", email_element)
                time.sleep(0.5)
                email_element.click()
            except ElementClickInterceptedException:
                # Fall back to JavaScript click
                logging.warning("Element click intercepted. Trying JavaScript click.")
                driver.execute_script("arguments[0].click();", email_element)
                logging.info(f"Opened email at index {email_index} using JavaScript")

            # # Click on "Reply All"
            # reply_all_xpath = "/html/body/div[3]/div[2]/div[1]/div/div/div/div[4]/div[3]/div[2]/div[1]/div/div[2]/article/header/div[6]/ul/li[2]/a"
            # reply_all_button = wait.until(EC.element_to_be_clickable((By.XPATH, reply_all_xpath)))
            # reply_all_button.click()
            # logging.info("Clicked Reply All button")
            
            # # Handle the popup asking to compose email without external images
            # compose_without_images_selector = "body > div.modal.flex.in > div > div > div.modal-footer > button.btn.btn-primary"
            # try:
            #     # Wait for the modal to appear and be clickable
            #     compose_without_images_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, compose_without_images_selector)))
            #     time.sleep(1)  # Small delay to ensure modal is fully loaded
            #     driver.execute_script("arguments[0].click();", compose_without_images_button)
            #     logging.info("Selected 'Compose email without external images'")
            # except TimeoutException:
            #     logging.error("Compose email without external images button not found. Attempting to close modal and retry.")
            #     try:
            #         # Close any open modal and retry
            #         modal_close_button = driver.find_element(By.XPATH, "//div[@class='modal-dialog']//button[contains(@class, 'close')]")
            #         modal_close_button.click()
            #         logging.info("Closed blocking modal dialog")
            #     except NoSuchElementException:
            #         logging.error("No modal close button found.")
            #     email_index += 1
            #     continue
         # Locate the email address to be copied
            try:
                # Wait until the <iframe> is present and switch to it
                iframe_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.body iframe.mail-detail-frame")))
                driver.switch_to.frame(iframe_element)
                
                # Now locate the email address within the iframe
                email_address_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='mailto:']")))
                # Extracting the email address without additional URL parameters
                email_href = email_address_element.get_attribute("href").replace("mailto:", "")
                parsed_url = urlparse(email_href)
                email_address = parsed_url.path
                logging.info(f"Copied email address: {email_address}")
               
                # Switch back to the default content after extracting the email
                driver.switch_to.default_content()

            except (TimeoutException, NoSuchElementException):
                logging.warning("Unable to locate email address using the iframe approach. Trying an alternative approach.")
                
                # Switch back to the default content in case of failure in the iframe
                driver.switch_to.default_content()
                
                # Fallback JavaScript approach to find 'mailto' links within the document
                email_addresses = driver.execute_script("""
                    let mailtoLinks = document.querySelectorAll("a[href^='mailto:']");
                    return Array.from(mailtoLinks).map(a => a.getAttribute('href').replace('mailto:', ''));
                """)
                
                if email_addresses:
                    email_address = email_addresses[0]  # Pick the first email found
                    logging.info(f"Copied email address using JavaScript: {email_address}")
                else:
                    logging.error("Unable to locate email address with JavaScript either. Skipping to the next email.")
                    email_index += 1
            # Click on "Forward"
            forward_xpath = "//*[@id='window-0']/div/div[4]/div[3]/div[2]/div[1]/div/div[2]/article/header/div[6]/ul/li[3]/a"
            forward_button = wait.until(EC.element_to_be_clickable((By.XPATH, forward_xpath)))
            forward_button.click()
            logging.info("Clicked Forward button")

            # Handle the popup asking to compose email without external images
            compose_without_images_selector = "body > div.modal.flex.in > div > div > div.modal-footer > button.btn.btn-primary"
            try:
                compose_without_images_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, compose_without_images_selector)))
                time.sleep(1)  # Small delay to ensure modal is fully loaded
                driver.execute_script("arguments[0].click();", compose_without_images_button)
                logging.info("Selected 'Compose email without external images'")
            except TimeoutException:
                logging.error("Compose email without external images button not found. Attempting to close modal and retry.")
                try:
                    modal_close_button = driver.find_element(By.XPATH, "//div[@class='modal-dialog']//button[contains(@class, 'close')]")
                    modal_close_button.click()
                    logging.info("Closed blocking modal dialog")
                except NoSuchElementException:
                    logging.error("No modal close button found.")
                email_index += 1
                continue

            try:
                # Locate the "To" input box and paste the email
                # Ensure that the element is clickable and interactable
                to_input_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.token-input.tt-input[placeholder='To']")))
                
                # Scroll the element into view to ensure visibility (if needed)
                driver.execute_script("arguments[0].scrollIntoView(true);", to_input_box)
                
                # Click the input box to ensure focus
                to_input_box.click()
                
                # Use ActionChains to paste the email address into the 'To' field
                actions = ActionChains(driver)
                actions.move_to_element(to_input_box).click().send_keys(email_address).perform()

                # Log success
                logging.info("Successfully pasted the email address into the 'To' input box.")
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Failed to locate the 'To' input box or paste the email. Error: {str(e)}")
            # # Enter the copied email address in the "To" input box
            # to_input_xpath = "//*[@id='1732724834535133-tokenfield']"
            # to_input_box = wait.until(EC.presence_of_element_located((By.XPATH, to_input_xpath)))
            # to_input_box.send_keys(email_address)
            # logging.info(f"Pasted email address in To field: {email_address}")

            # Wait for the compose window to be available
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".window-container.io-ox-mail-compose-window")))
            logging.info("Compose window opened successfully")

            # Switch to the iframe for the email editor
            compose_frame = wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@id, 'mce_') and @title='Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help']")))
            logging.info("Switched to the compose email iframe")

            # Locate the body of the email and enter text
            email_body = driver.find_element(By.CSS_SELECTOR, "body#tinymce")
            email_body.click()
            email_body.clear()
            message = (
                ""
            )
            email_body.send_keys(message)
            logging.info("Entered reply message")

            # Switch back to the default content
            driver.switch_to.default_content()

            # Click on the Send button
            send_button_xpath = "/html/body/div[3]/div[5]/div/div[2]/div/div[5]/div/button"
            send_button = driver.find_element(By.XPATH, send_button_xpath)
            # send_button.click()
            logging.info("Clicked Send button")

            # Wait for the email to be sent
            time.sleep(2)  # Adjust as needed

            # Move to the next email
            email_index += 1

        except NoSuchElementException:
            logging.info("No more unread emails found.")
            break
        except TimeoutException:
            logging.error("Element not found within the expected time. Skipping to the next email.")
            email_index += 1
        

finally:
    # Close the browser
    driver.quit()
    logging.info("Closed the browser")
