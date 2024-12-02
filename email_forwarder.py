import logging
import time

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from email_automation import EmailAutomation


class EmailForwarder(EmailAutomation):
    def _forward_email(self, email_address):
        try:
            forward_xpath = "//*[@id='window-0']/div/div[4]/div[3]/div[2]/div[1]/div/div[2]/article/header/div[6]/ul/li[3]/a"
            forward_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, forward_xpath)))
            forward_button.click()
            logging.info("Clicked Forward button")

            self._handle_compose_without_images()
            self._enter_recipient_email(email_address)
            self._compose_email_message()
            self._send_email()
        except TimeoutException:
            logging.error("Failed to forward email")

    def _handle_compose_without_images(self):
        compose_without_images_selector = "body > div.modal.flex.in > div > div > div.modal-footer > button.btn.btn-primary"
        try:
            compose_without_images_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, compose_without_images_selector)))
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", compose_without_images_button)
            logging.info("Selected 'Compose email without external images'")
        except TimeoutException:
            logging.error("Compose email without external images button not found. Attempting to close modal and retry.")
            try:
                modal_close_button = self.driver.find_element(By.XPATH, "//div[@class='modal-dialog']//button[contains(@class, 'close')]")
                modal_close_button.click()
                logging.info("Closed blocking modal dialog")
            except NoSuchElementException:
                logging.error("No modal close button found.")

    def _enter_recipient_email(self, email_address):
        try:
            to_input_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.token-input.tt-input[placeholder='To']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", to_input_box)
            to_input_box.click()
            actions = ActionChains(self.driver)
            actions.move_to_element(to_input_box).click().send_keys(email_address).perform()
            logging.info("Successfully pasted the email address into the 'To' input box.")
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Failed to locate the 'To' input box or paste the email. Error: {str(e)}")

    def _compose_email_message(self):
        try:
            compose_frame = self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@id, 'mce_') and @title='Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help']")))
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
            send_button.click()
            logging.info("Clicked Send button")
            time.sleep(2)  # Adjust as needed
        except NoSuchElementException:
            logging.error("Send button not found")


if __name__ == "__main__":
    DRIVER_PATH = 'C:\\Users\\91706\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe'
    EMAIL_URL = "https://privateemail.com/appsuite/#!!&app=io.ox/mail&folder=default0/INBOX&storeLocale=true"
    USERNAME = ""
    PASSWORD = ""

    email_forwarder = EmailForwarder(DRIVER_PATH, EMAIL_URL, USERNAME, PASSWORD)
    try:
        email_forwarder.launch_email()
        email_forwarder.close_overlay()
        email_forwarder.login()
        email_forwarder.process_emails()
    finally:
        email_forwarder.close()