import time
import logging
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC, wait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class EmailAutomation:
    def __init__(self, driver_path, email_url, username, password):
        self.service = Service(driver_path)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.wait = WebDriverWait(self.driver, 20)
        self.email_url = email_url
        self.username = username
        self.password = password

    def launch_email(self):
        self.driver.get(self.email_url)
        logging.info("Launched the email URL")

    def login(self):
        try:
            username_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#txtMailbox")))
            password_field = self.driver.find_element(By.CSS_SELECTOR, "#txtPwd")
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            logging.info("Entered login credentials")

            login_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnLogin")))
            login_button.click()
            logging.info("Clicked login button")
            # Wait for the inbox to load
            wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[2]/div[1]/div/div/div/div[4]/div[3]/div[1]/div[3]/ul[2]")))
            logging.info("Inbox loaded successfully")
        except ElementClickInterceptedException:
            logging.warning("Login button click intercepted, using JavaScript to click instead")
            self.driver.execute_script("arguments[0].click();", self.driver.find_element(By.CSS_SELECTOR, "#btnLogin"))
            logging.info("Clicked login button using JavaScript")
        except TimeoutException:
            logging.error("Login elements not found within the expected time")

    def close_overlay(self):
        try:
            overlay_close_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".reject-btn-container button")))
            overlay_close_button.click()
            logging.info("Closed overlay or cookie consent banner")
        except TimeoutException:
            logging.info("No overlay or cookie consent banner found")

    def process_emails(self, start_index=40):
        email_index = start_index
        while True:
            try:
                email_element = self._get_email_element(email_index)
                self._open_email(email_element, email_index)
                email_address = self._extract_email_address()
                if email_address:
                    self._forward_email(email_address)
                email_index += 1
            except NoSuchElementException:
                logging.info("No more unread emails found.")
                break
            except TimeoutException:
                logging.error("Element not found within the expected time. Skipping to the next email.")
                email_index += 1

    def _get_email_element(self, email_index):
        email_xpath = f"/html/body/div[3]/div[2]/div[1]/div/div/div/div[4]/div[3]/div[1]/div[3]/ul[2]/li[{email_index}]"
        return self.driver.find_element(By.XPATH, email_xpath)

    def _open_email(self, email_element, email_index):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", email_element)
            time.sleep(0.5)
            email_element.click()
        except ElementClickInterceptedException:
            logging.warning("Element click intercepted. Trying JavaScript click.")
            self.driver.execute_script("arguments[0].click();", email_element)
        logging.info(f"Opened email at index {email_index}")

    def _extract_email_address(self):
        try:
            iframe_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.body iframe.mail-detail-frame")))
            self.driver.switch_to.frame(iframe_element)
            email_address_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='mailto:']")))
            email_href = email_address_element.get_attribute("href").replace("mailto:", "")
            parsed_url = urlparse(email_href)
            email_address = parsed_url.path
            logging.info(f"Copied email address: {email_address}")
            self.driver.switch_to.default_content()
            return email_address
        except (TimeoutException, NoSuchElementException):
            logging.warning("Unable to locate email address using the iframe approach. Trying an alternative approach.")
            self.driver.switch_to.default_content()
            email_addresses = self.driver.execute_script(
                """
                let mailtoLinks = document.querySelectorAll("a[href^='mailto:']");
                return Array.from(mailtoLinks).map(a => a.getAttribute('href').replace('mailto:', ''));
                """
            )
            if email_addresses:
                email_address = email_addresses[0]
                logging.info(f"Copied email address using JavaScript: {email_address}")
                return email_address
            logging.error("Unable to locate email address with JavaScript either. Skipping to the next email.")
            return None

    def close(self):
        self.driver.quit()
        logging.info("Closed the browser")

    def _reply_all(self, email_address):
        try:
            reply_all_xpath = "/html/body/div[3]/div[2]/div[1]/div/div/div/div[4]/div[3]/div[2]/div[1]/div/div[2]/article/header/div[6]/ul/li[2]/a"
            reply_all_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, reply_all_xpath)))
            reply_all_button.click()
            logging.info("Clicked Reply All button")
            self._handle_compose_without_images()
            self._enter_recipient_email(email_address)
            self._compose_email_message()
            self._send_email()
        except TimeoutException:
            logging.error("Failed to reply all")

    def _handle_compose_without_images(self):
        compose_without_images_selector = "body > div.modal.flex.in > div > div > div.modal-footer > button.btn.btn-primary"
        try:
            compose_without_images_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, compose_without_images_selector)))
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", compose_without_images_button)
            logging.info("Selected 'Compose email without external images'")
        except TimeoutException:
            logging.error(
                "Compose email without external images button not found. Attempting to close modal and retry.")
            try:
                modal_close_button = self.driver.find_element(By.XPATH,
                                                              "//div[@class='modal-dialog']//button[contains(@class, 'close')]")
                modal_close_button.click()
                logging.info("Closed blocking modal dialog")
            except NoSuchElementException:
                logging.error("No modal close button found.")

    def _enter_recipient_email(self, email_address):
        try:
            to_input_box = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.token-input.tt-input[placeholder='To']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", to_input_box)
            to_input_box.click()
            actions = ActionChains(self.driver)
            actions.move_to_element(to_input_box).click().send_keys(email_address).perform()
            logging.info("Successfully pasted the email address into the 'To' input box.")
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Failed to locate the 'To' input box or paste the email. Error: {str(e)}")

    def _compose_email_message(self):
        try:
            compose_frame = self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,
                                                                                       "//iframe[contains(@id, 'mce_') and @title='Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help']")))
            email_body = self.driver.find_element(By.CSS_SELECTOR, "body#tinymce")
            email_body.click()
            email_body.clear()
            message = (
                ""
            )
            email_body.send_keys(message)
            logging.info("Entered reply message")
            self.driver.switch_to.default_content()
        except (TimeoutException, NoSuchElementException):
            logging.error("Failed to compose the email message")

    def _send_email(self):
        try:
            send_button_xpath = "/html/body/div[3]/div[5]/div/div[2]/div/div[5]/div/button"
            send_button = self.driver.find_element(By.XPATH, send_button_xpath)
            # send_button.click()
            logging.info("Clicked Send button")
            time.sleep(2)  # Adjust as needed
        except NoSuchElementException:
            logging.error("Send button not found")


if __name__ == "__main__":
    DRIVER_PATH = 'C:\\Users\\91706\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe'
    EMAIL_URL = "https://privateemail.com/appsuite/#!!&app=io.ox/mail&folder=default0/INBOX&storeLocale=true"
    USERNAME = ""
    PASSWORD = ""

    email_automation = EmailAutomation(DRIVER_PATH, EMAIL_URL, USERNAME, PASSWORD)
    try:
        email_automation.launch_email()
        email_automation.close_overlay()
        email_automation.login()
        email_automation.process_emails()
    finally:
        email_automation.close()