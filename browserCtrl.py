from PyQt5.QtCore import pyqtSignal, QThread
from selenium import webdriver
import json
import os
import platform
import time
import random
import pyperclip
import subprocess
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
if platform.system().lower() == 'windows':
    from subprocess import CREATE_NO_WINDOW
else:
    CREATE_NO_WINDOW = 0
import chromedriver_autoinstaller
from appLog import log


try:
    log.info("browserCTRL start to dl")
    chromedriver_autoinstaller.install()
except:
    log.exception("")
CHROME = 1
FIREFOX = 2


class Web(QThread):
    __URL = 'https://web.whatsapp.com/'
    driverNum = 0
    lcdNumber_reviewed = pyqtSignal(int)
    lcdNumber_nwa = pyqtSignal(int)
    lcdNumber_wa = pyqtSignal(int)
    LogBox = pyqtSignal(str)
    wa = pyqtSignal(str)
    nwa = pyqtSignal(str)
    EndWork = pyqtSignal(str)

    def __init__(self, parent=None, counter_start=0, step='A', numList=None, sleepMin=3, sleepMax=6, text='', path='',
                 Remember=False, browser=1):
        super(Web, self).__init__(parent)
        self.counter_start = counter_start
        self.Numbers = numList
        self.step = step
        self.sleepMin = sleepMin
        self.sleepMax = sleepMax
        self.text = text
        self.path = path
        self.remember = Remember
        self.isRunning = True
        try:
            if not os.path.exists('./temp/cache'):
                os.makedirs('temp/cache/')
        except:
            os.makedirs('./temp/cache/')
        # Save Session Section
        self.__platform = platform.system().lower()
        if self.__platform != 'windows' and self.__platform != 'linux':
            raise OSError('Only Windows and Linux are supported for now.')

        self.__browser_choice = 0
        self.__browser_options = None
        self.__browser_user_dir = None
        self.__driver = None
        self.service = Service()
        self.service.creation_flags = CREATE_NO_WINDOW
        if browser == 1:
            self.set_browser(CHROME)
        elif browser == 2:
            self.set_browser(FIREFOX)

        self.__init_browser()

    def driverBk(self):
        """Initialize browser with proper user data directory for session persistence"""
        option = webdriver.ChromeOptions()
        option.add_argument("--disable-notifications")
        option.add_argument("--disable-blink-features=AutomationControlled")
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        option.add_experimental_option('useAutomationExtension', False)
        
        # Create a dedicated user data directory for this application
        user_data_dir = os.path.join(os.getcwd(), 'temp', 'chrome_profile')
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        
        option.add_argument(f"--user-data-dir={user_data_dir}")
        
        try:
            self.__driver = webdriver.Chrome(options=option, service=self.service)
            log.debug("webDriver with user data directory")
        except Exception as e:
            log.exception(f"Chrome initialization error: {e}")
            try:
                # Fallback without user data directory
                option = webdriver.ChromeOptions()
                option.add_argument("--disable-notifications")
                self.__driver = webdriver.Chrome(options=option, service=self.service)
                log.debug("webDriver fallback")
            except:
                log.exception("Chrome fallback failed")
                try:
                    self.__driver = webdriver.Firefox()
                except:
                    pass
        
        try:
            self.__driver.set_window_position(0, 0)
            self.__driver.set_window_size(1080, 840)
        except:
            pass

    def is_logged_in(self):
        status = self.__driver.execute_script(
            "if (document.querySelector('*[data-icon=new-chat-outline]') !== null) { return true } else { return false }"
        )
        return status

    def copyToClipboard(self, text):
        """Copy text to clipboard using platform-appropriate method"""
        try:
            # Try pyperclip first (works on most platforms)
            pyperclip.copy(text)
            log.debug(f"Text copied to clipboard using pyperclip: {text}")
        except Exception as e:
            log.debug(f"pyperclip failed: {e}")
            try:
                # Try platform-specific commands
                if platform.system().lower() == 'darwin':  # macOS
                    subprocess.run(["pbcopy"], input=text, text=True, check=True)
                elif platform.system().lower() == 'linux':  # Linux
                    subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
                elif platform.system().lower() == 'windows':  # Windows
                    subprocess.run(["clip"], input=text, text=True, check=True)
                else:
                    # Fallback to pyperclip again
                    pyperclip.copy(text)
                log.debug(f"Text copied to clipboard using platform command: {text}")
            except Exception as e2:
                log.error(f"All clipboard methods failed: {e2}")
                # Last resort: try pyperclip one more time
                try:
                    pyperclip.copy(text)
                except:
                    log.error("Failed to copy text to clipboard")

    def ANALYZ(self):
        try:
            log.debug("analyz")
            if self.remember:
                log.debug("remember")
                cacheList = os.listdir('temp/cache/')
                if len(cacheList) != 0:
                    self.access_by_file(f"./temp/cache/{cacheList[0]}")
                    log.debug('recover')
                else:
                    self.driverBk()
                    self.__driver.get(self.__URL)
            else:
                log.debug("! remember !")
                self.driverBk()
                self.__driver.get(self.__URL)

            while True:
                log.debug("Login Check")
                time.sleep(1)
                if self.is_logged_in():
                    log.debug("login")
                    logtxt = "Login Success"
                    self.LogBox.emit(logtxt)
                    
                    # Save session if remember is enabled and no cached session exists
                    if self.remember:
                        cacheList = os.listdir('temp/cache/')
                        if len(cacheList) == 0:
                            try:
                                # Save the current session using a simpler approach
                                # Just save the user data directory path for future use
                                session_info = {
                                    "user_data_dir": os.path.join(os.getcwd(), 'temp', 'chrome_profile'),
                                    "timestamp": int(time.time())
                                }
                                session_file = f"./temp/cache/session_{int(time.time())}.json"
                                with open(session_file, 'w') as f:
                                    json.dump(session_info, f, indent=4)
                                log.debug(f"Session info saved to {session_file}")
                            except Exception as e:
                                log.error(f"Failed to save session: {e}")
                    
                    break
            log.debug("thread:", self.counter_start)
            i = 0
            f = 0
            nf = 0
            for num in self.Numbers:
                logtxt = ""
                try:
                    # Check if browser is still connected
                    try:
                        self.__driver.current_url
                    except Exception as e:
                        log.error(f"Browser disconnected: {e}")
                        break
                    
                    time.sleep(3)
                    if i == 0:
                        execu = f"""
                                var a = document.createElement('a');
                                var link = document.createTextNode("hiding");
                                a.appendChild(link);
                                a.href = "https://wa.me/{num}";
                                document.head.appendChild(a);
                                """
                        try:
                            self.__driver.execute_script(execu)
                        except:
                            log.exception("error")
                    else:
                        element = self.__driver.find_element(By.XPATH, '/html/head/a')
                        self.__driver.execute_script(f"arguments[0].setAttribute('href','https://wa.me/{num}');",
                                                     element)
                    user = self.__driver.find_element(By.XPATH, '/html/head/a')
                    self.__driver.execute_script("arguments[0].click();", user)
                    time.sleep(2)
                    sourceWeb = self.__driver.page_source
                    if "Phone number shared via url is invalid" in sourceWeb:
                        log.debug(f"Not Found {num}")
                        nf += 1
                        self.lcdNumber_nwa.emit(nf)
                        logtxt = f"Number::{num} => Not Find!"
                        self.nwa.emit(f"{num}")
                    else:
                        log.debug(f"find {num}")
                        f += 1
                        self.lcdNumber_wa.emit(f)
                        logtxt = f"Number::{num} => Find."
                        self.wa.emit(f"{num}")
                except:
                    logtxt = f"Number::{num} Error !"
                    continue
                finally:
                    i += 1
                    log.debug(i)
                    self.lcdNumber_reviewed.emit(i)
                    self.LogBox.emit(logtxt)
            time.sleep(2)
            log.debug("end")
            self.EndWork.emit("-- analysis completed --")
            self.isRunning = False
            self.__driver.quit()
        except:
            log.exception("Analyz ->:")

    def SendTEXT(self):
        log.debug("sent text")
        if self.remember:
            cacheList = os.listdir('temp/cache/')
            if len(cacheList) != 0:
                self.access_by_file(f"./temp/cache/{cacheList[0]}")
                log.debug('recover')
            else:
                self.driverBk()
                self.__driver.get(self.__URL)
        else:
            self.driverBk()
            self.__driver.get(self.__URL)
        time.sleep(2)
        while True:
            time.sleep(1)
            if self.is_logged_in():
                log.debug("login")
                logtxt = "Login Success"
                self.LogBox.emit(logtxt)
                
                # Save session if remember is enabled and no cached session exists
                if self.remember:
                    cacheList = os.listdir('temp/cache/')
                    if len(cacheList) == 0:
                        try:
                            # Save the current session using a simpler approach
                            # Just save the user data directory path for future use
                            session_info = {
                                "user_data_dir": os.path.join(os.getcwd(), 'temp', 'chrome_profile'),
                                "timestamp": int(time.time())
                            }
                            session_file = f"./temp/cache/session_{int(time.time())}.json"
                            with open(session_file, 'w') as f:
                                json.dump(session_info, f, indent=4)
                            log.debug(f"Session info saved to {session_file}")
                        except Exception as e:
                            log.error(f"Failed to save session: {e}")
                
                break
        i = 0
        f = 0
        nf = 0
        from random import randint
        log.debug(self.Numbers)
        for num in self.Numbers:
            logtxt = ""
            try:
                time.sleep(3)
                if i == 0:
                    execu = f"""
                            var a = document.createElement('a');
                            var link = document.createTextNode("hiding");
                            a.appendChild(link);
                            a.href = "https://wa.me/{num}";
                            document.head.appendChild(a);
                            """
                    try:
                        self.__driver.execute_script(execu)
                    except Exception as e:
                        log.exception(f"Error creating link: {e}")
                        logtxt = "ERROR !"
                        break
                else:
                    element = self.__driver.find_element(By.XPATH, '/html/head/a')
                    self.__driver.execute_script(
                        f"arguments[0].setAttribute('href','https://wa.me/{num}');", element)
                user = self.__driver.find_element(By.XPATH, '/html/head/a')
                self.__driver.execute_script("arguments[0].click();", user)
                time.sleep(2)
                sourceWeb = self.__driver.page_source
                if "Phone number shared via url is invalid" in sourceWeb:
                    log.debug(f"Not Found {num}")
                    nf += 1
                    self.lcdNumber_nwa.emit(nf)
                    logtxt = f"Number::{num} => No Send!"
                    self.nwa.emit(f"{num}")
                else:
                    log.debug(f"find {num}")
                    time.sleep(2)
                    # Wait for text input element - try multiple selectors
                    try:
                        from selenium.webdriver.support.ui import WebDriverWait
                        from selenium.webdriver.support import expected_conditions as EC
                        
                        # Try multiple possible selectors for the text input
                        text_input_selectors = [
                            '//div[@title="Type a message"]',
                            '//div[@contenteditable="true"][@data-tab="10"]',
                            '//div[@contenteditable="true"][@data-tab="6"]',
                            '//div[@role="textbox"]',
                            '//div[contains(@class, "copyable-text")]//div[@contenteditable="true"]',
                            '//div[@data-tab="10"]//div[@contenteditable="true"]',
                            '//div[@data-tab="6"]//div[@contenteditable="true"]'
                        ]
                        
                        textBox = None
                        for selector in text_input_selectors:
                            try:
                                textBox = WebDriverWait(self.__driver, 3).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                log.debug(f"Found text input with selector: {selector}")
                                break
                            except:
                                continue
                        
                        if textBox is None:
                            raise Exception("No text input element found with any selector")
                            
                    except Exception as e:
                        log.error(f"Text input not found for {num}: {e}")
                        continue
                    time.sleep(1)
                    log.debug(f"Setting text in textbox: {self.text}")
                    textBox.clear()
                    time.sleep(0.5)
                    # Primary: type the text character by character
                    try:
                        textBox.send_keys(self.text)
                        log.debug("Text set using direct typing")
                    except Exception as e:
                        log.debug(f"Direct typing failed: {e}")
                        # Fallback to clipboard paste
                        try:
                            self.copyToClipboard(self.text)
                            textBox.send_keys(Keys.CONTROL, 'v')
                            log.debug("Text set using clipboard paste")
                        except Exception as e2:
                            log.debug(f"Clipboard method failed: {e2}")
                            # Last fallback: try send_keys again
                            try:
                                textBox.send_keys(self.text)
                                log.debug("Text set using direct typing (last fallback)")
                            except Exception as e3:
                                log.debug(f"Final send_keys failed: {e3}")
                    time.sleep(1)
                    # Verify the text was set correctly
                    try:
                        pasted_text = textBox.get_attribute('textContent') or textBox.get_attribute('innerText') or ''
                        log.debug(f"Text in textbox after setting: '{pasted_text}'")
                    except:
                        log.debug("Could not verify text content")
                    log.debug("Sending message")
                    # Send the message with a single key press
                    try:
                        textBox.send_keys(Keys.RETURN)
                        log.debug("Message sent with RETURN key")
                    except Exception as e:
                        log.debug(f"RETURN failed, trying ENTER: {e}")
                        textBox.send_keys(Keys.ENTER)
                        log.debug("Message sent with ENTER key")
                    
                    # Wait a bit longer to ensure the message is sent
                    time.sleep(2)
                    f += 1
                    self.lcdNumber_wa.emit(f)
                    logtxt = f"Number::{num} => Sent."
                    self.wa.emit(f"{num}")
                    log.debug(f"Message sent successfully to {num}")
                time.sleep(randint(self.sleepMin, self.sleepMax))
            except:
                logtxt = f"Error To Number = {num} "
                continue
            finally:
                i += 1
                self.lcdNumber_reviewed.emit(i)
                self.LogBox.emit(logtxt)
        log.debug("end msg")
        self.EndWork.emit("-- Send Message completed --")
        self.stop()
        self.isRunning = False

    def SendIMG(self):
        log.debug("sent img")
        if self.remember:
            cacheList = os.listdir('temp/cache/')
            if len(cacheList) != 0:
                self.access_by_file(f"./temp/cache/{cacheList[0]}")
                log.debug('recover')
            else:
                self.driverBk()
                self.__driver.get(self.__URL)
        else:
            self.driverBk()
            self.__driver.get(self.__URL)
        time.sleep(2)
        while True:
            time.sleep(1)
            if self.is_logged_in():
                log.debug("login")
                logtxt = "Login Success"
                self.LogBox.emit(logtxt)
                
                # Save session if remember is enabled and no cached session exists
                if self.remember:
                    cacheList = os.listdir('temp/cache/')
                    if len(cacheList) == 0:
                        try:
                            # Save the current session using a simpler approach
                            # Just save the user data directory path for future use
                            session_info = {
                                "user_data_dir": os.path.join(os.getcwd(), 'temp', 'chrome_profile'),
                                "timestamp": int(time.time())
                            }
                            session_file = f"./temp/cache/session_{int(time.time())}.json"
                            with open(session_file, 'w') as f:
                                json.dump(session_info, f, indent=4)
                            log.debug(f"Session info saved to {session_file}")
                        except Exception as e:
                            log.error(f"Failed to save session: {e}")
                
                break
        i = 0
        f = 0
        nf = 0
        from random import randint
        log.debug(self.Numbers)
        for num in self.Numbers:
            logtxt = ""
            try:
                time.sleep(3)
                if i == 0:
                    execu = f"""
                            var a = document.createElement('a');
                            var link = document.createTextNode("hiding");
                            a.appendChild(link);
                            a.href = "https://wa.me/{num}";
                            document.head.appendChild(a);
                            """
                    try:
                        self.__driver.execute_script(execu)
                    except:
                        log.exception("error img")
                        logtxt = "ERROR !"
                        break
                else:
                    element = self.__driver.find_element(By.XPATH, '/html/head/a')
                    self.__driver.execute_script(f"arguments[0].setAttribute('href','https://wa.me/{num}');", element)
                user = self.__driver.find_element(By.XPATH, '/html/head/a')
                self.__driver.execute_script("arguments[0].click();", user)
                time.sleep(2)
                sourceWeb = self.__driver.page_source
                if "Phone number shared via url is invalid" in sourceWeb:
                    log.debug(f"Not Found {num}")
                    nf += 1
                    self.lcdNumber_nwa.emit(nf)
                    logtxt = f"Number::{num} => No Send"
                    self.nwa.emit(f"{num}")
                else:
                    log.debug(f"find {num}")
                    time.sleep(2)
                    # Wait for the attachment button to be present before clicking
                    try:
                        from selenium.webdriver.support.ui import WebDriverWait
                        from selenium.webdriver.support import expected_conditions as EC
                        
                        log.debug(f"Starting attachment button search for {num}")
                        
                        # Try multiple possible selectors for the attachment button
                        attach_selectors = [
                            '//button[@title="Attach"]',
                            '//span[contains(@class, "attach")]',
                            '//div[contains(@class, "attach")]',
                            '//button[contains(@class, "attach")]'
                        ]
                        
                        attach_btn = None
                        for i, selector in enumerate(attach_selectors):
                            try:
                                log.debug(f"Trying attachment selector {i+1}/{len(attach_selectors)}: {selector}")
                                attach_btn = WebDriverWait(self.__driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                log.debug(f"Found attachment button with selector: {selector}")
                                break
                            except Exception as e:
                                log.debug(f"Selector {i+1} failed: {str(e)}")
                                continue
                        
                        if attach_btn is None:
                            # Try to find any attachment-related elements for debugging
                            log.debug("No attachment button found, searching for any attachment-related elements...")
                            try:
                                current_url = self.__driver.current_url
                                log.debug(f"Current page URL: {current_url}")
                                
                                # Check if we're still on the correct page
                                if "wa.me" not in current_url:
                                    log.error(f"Not on WhatsApp chat page. Current URL: {current_url}")
                                
                                all_attach_elements = self.__driver.find_elements(By.XPATH, "//*[contains(text(), 'Attach') or contains(@aria-label, 'Attach') or contains(@title, 'Attach') or contains(@class, 'attach')]")
                                log.debug(f"Found {len(all_attach_elements)} attachment-related elements")
                                for i, elem in enumerate(all_attach_elements[:5]):  # Log first 5 elements
                                    try:
                                        tag_name = elem.tag_name
                                        aria_label = elem.get_attribute('aria-label') or 'N/A'
                                        title = elem.get_attribute('title') or 'N/A'
                                        class_name = elem.get_attribute('class') or 'N/A'
                                        log.debug(f"Element {i+1}: tag={tag_name}, aria-label='{aria_label}', title='{title}', class='{class_name}'")
                                    except:
                                        log.debug(f"Element {i+1}: Could not get attributes")
                                
                                # Also check for any buttons in the footer area
                                footer_buttons = self.__driver.find_elements(By.XPATH, "//footer//button | //footer//div[@role='button']")
                                log.debug(f"Found {len(footer_buttons)} buttons in footer area")
                                for i, btn in enumerate(footer_buttons[:3]):  # Log first 3 footer buttons
                                    try:
                                        tag_name = btn.tag_name
                                        aria_label = btn.get_attribute('aria-label') or 'N/A'
                                        title = btn.get_attribute('title') or 'N/A'
                                        class_name = btn.get_attribute('class') or 'N/A'
                                        log.debug(f"Footer button {i+1}: tag={tag_name}, aria-label='{aria_label}', title='{title}', class='{class_name}'")
                                    except:
                                        log.debug(f"Footer button {i+1}: Could not get attributes")
                                        
                            except Exception as e:
                                log.debug(f"Error searching for attachment elements: {e}")
                            
                            raise Exception("No attachment button found with any selector")
                        
                        log.debug("Clicking attachment button...")
                        attach_btn.click()
                        log.debug("Attachment button clicked successfully")
                        
                    except Exception as e:
                        log.error(f"Attachment button not found for {num}: {e}")
                        # Fallback: always try to send text only
                        fallback_text = self.text if self.text.strip() else "Attachment could not be sent"
                        log.info(f"Falling back to sending text only for {num}")
                        # Wait for text input element - try multiple selectors
                        try:
                            text_input_selectors = [
                                '//div[@title="Type a message"]',
                                '//div[@contenteditable="true"][@data-tab="10"]',
                                '//div[@contenteditable="true"][@data-tab="6"]',
                                '//div[@role="textbox"]',
                                '//div[contains(@class, "copyable-text")]//div[@contenteditable="true"]',
                                '//div[@data-tab="10"]//div[@contenteditable="true"]',
                                '//div[@data-tab="6"]//div[@contenteditable="true"]'
                            ]
                            textBox = None
                            for selector in text_input_selectors:
                                try:
                                    textBox = WebDriverWait(self.__driver, 3).until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                    log.debug(f"Found text input with selector: {selector}")
                                    break
                                except:
                                    continue
                            if textBox is None:
                                raise Exception("No text input element found with any selector")
                        except Exception as e:
                            log.error(f"Text input not found for {num}: {e}")
                            continue
                        time.sleep(1)
                        log.debug(f"Setting text in textbox: {fallback_text}")
                        textBox.clear()
                        time.sleep(0.5)
                        try:
                            # Remove JavaScript fallback, use clipboard then send_keys again
                            self.copyToClipboard(fallback_text)
                            textBox.send_keys(Keys.CONTROL, 'v')
                            log.debug("Text set using clipboard paste")
                        except Exception as e2:
                            log.debug(f"Clipboard method failed: {e2}")
                            try:
                                textBox.send_keys(fallback_text)
                                log.debug("Text set using direct typing (last fallback)")
                            except Exception as e3:
                                log.debug(f"Final send_keys failed: {e3}")
                        time.sleep(1)
                        try:
                            pasted_text = textBox.get_attribute('textContent') or textBox.get_attribute('innerText') or ''
                            log.debug(f"Text in textbox after setting: '{pasted_text}'")
                        except:
                            log.debug("Could not verify text content")
                        log.debug("Sending message")
                        try:
                            textBox.send_keys(Keys.RETURN)
                            log.debug("Message sent with RETURN key")
                        except Exception as e:
                            log.debug(f"RETURN failed, trying ENTER: {e}")
                            textBox.send_keys(Keys.ENTER)
                            log.debug("Message sent with ENTER key")
                        time.sleep(2)
                        f += 1
                        self.lcdNumber_wa.emit(f)
                        logtxt = f"Number::{num} => Sent (text only fallback)."
                        self.wa.emit(f"{num}")
                        log.debug(f"Message sent successfully to {num} (text only fallback)")
                        continue
                    time.sleep(2)
                    # Wait for file input element - try multiple selectors and methods
                    try:
                        log.debug(f"Starting file input search for {num}")
                        
                        # Try multiple possible selectors for the file input
                        file_input_selectors = [
                            '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
                            '//input[@type="file"]',
                            '//input[contains(@accept, "image")]',
                            '//input[@accept="*/*"]'
                        ]
                        
                        attch = None
                        for i, selector in enumerate(file_input_selectors):
                            try:
                                log.debug(f"Trying file input selector {i+1}/{len(file_input_selectors)}: {selector}")
                                attch = WebDriverWait(self.__driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                log.debug(f"Found file input with selector: {selector}")
                                break
                            except Exception as e:
                                log.debug(f"File input selector {i+1} failed: {str(e)}")
                                continue
                        
                        if attch is None:
                            # Try to find any file input elements for debugging
                            log.debug("No file input found, searching for any file input elements...")
                            try:
                                all_file_inputs = self.__driver.find_elements(By.XPATH, "//input[@type='file']")
                                log.debug(f"Found {len(all_file_inputs)} file input elements")
                                for i, elem in enumerate(all_file_inputs[:3]):  # Log first 3 elements
                                    try:
                                        accept_attr = elem.get_attribute('accept') or 'N/A'
                                        id_attr = elem.get_attribute('id') or 'N/A'
                                        class_attr = elem.get_attribute('class') or 'N/A'
                                        log.debug(f"File input {i+1}: accept='{accept_attr}', id='{id_attr}', class='{class_attr}'")
                                    except:
                                        log.debug(f"File input {i+1}: Could not get attributes")
                            except Exception as e:
                                log.debug(f"Error searching for file input elements: {e}")
                            
                            raise Exception("No file input element found with any selector")
                        
                        # Ensure the path is absolute and exists
                        if not os.path.isabs(self.path):
                            self.path = os.path.abspath(self.path)
                        
                        if not os.path.exists(self.path):
                            raise Exception(f"Image file not found: {self.path}")
                        
                        # Check file size and other properties
                        try:
                            file_size = os.path.getsize(self.path)
                            file_size_mb = file_size / (1024 * 1024)
                            log.debug(f"File size: {file_size_mb:.2f} MB")
                            
                            if file_size_mb > 16:
                                log.warning(f"File size ({file_size_mb:.2f} MB) is larger than WhatsApp's 16MB limit")
                            
                            # Check file extension
                            file_ext = os.path.splitext(self.path)[1].lower()
                            log.debug(f"File extension: {file_ext}")
                            
                            supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                            if file_ext not in supported_extensions:
                                log.warning(f"File extension {file_ext} might not be supported by WhatsApp")
                                
                        except Exception as e:
                            log.debug(f"Error checking file properties: {e}")
                        
                        log.debug(f"Sending file path to input: {self.path}")
                        log.debug(f"File input element found: tag={attch.tag_name}, accept={attch.get_attribute('accept')}")
                        
                        attch.send_keys(self.path)
                        log.debug("File path sent to input successfully")
                        
                        # Wait a bit and check if the file was processed
                        time.sleep(3)
                        log.debug("Checking if file was processed...")
                        
                        # Try to find any upload progress indicators or error messages
                        try:
                            progress_elements = self.__driver.find_elements(By.XPATH, "//*[contains(@class, 'progress') or contains(@class, 'upload') or contains(@class, 'loading')]")
                            if progress_elements:
                                log.debug(f"Found {len(progress_elements)} progress/upload elements")
                            
                            error_elements = self.__driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'failed') or contains(text(), 'Failed')]")
                            if error_elements:
                                log.debug(f"Found {len(error_elements)} potential error elements")
                                for i, elem in enumerate(error_elements[:2]):
                                    try:
                                        error_text = elem.text
                                        log.debug(f"Error element {i+1}: {error_text}")
                                    except:
                                        pass
                            
                            # Check for file validation errors
                            validation_errors = self.__driver.find_elements(By.XPATH, "//*[contains(text(), 'file') or contains(text(), 'File') or contains(text(), 'size') or contains(text(), 'format')]")
                            if validation_errors:
                                log.debug(f"Found {len(validation_errors)} potential validation elements")
                                for i, elem in enumerate(validation_errors[:3]):
                                    try:
                                        validation_text = elem.text
                                        if validation_text.strip():
                                            log.debug(f"Validation element {i+1}: {validation_text}")
                                    except:
                                        pass
                            
                            # Check if the image preview is visible (indicates successful upload)
                            image_previews = self.__driver.find_elements(By.XPATH, "//img[contains(@class, 'preview') or contains(@class, 'image') or contains(@class, 'media')]")
                            if image_previews:
                                log.debug(f"Found {len(image_previews)} image preview elements - file upload appears successful")
                            else:
                                log.debug("No image preview elements found - file upload may have failed")
                                
                        except Exception as e:
                            log.debug(f"Error checking for progress/error elements: {e}")
                        
                    except Exception as e:
                        log.error(f"File input not found or failed for {num}: {e}")
                        # Fallback: try to send text only
                        fallback_text = self.text if self.text.strip() else "Image could not be sent"
                        log.info(f"Falling back to sending text only for {num}")
                        # Wait for text input element - try multiple selectors
                        try:
                            text_input_selectors = [
                                '//div[@title="Type a message"]',
                                '//div[@contenteditable="true"][@data-tab="10"]',
                                '//div[@contenteditable="true"][@data-tab="6"]',
                                '//div[@role="textbox"]',
                                '//div[contains(@class, "copyable-text")]//div[@contenteditable="true"]',
                                '//div[@data-tab="10"]//div[@contenteditable="true"]',
                                '//div[@data-tab="6"]//div[@contenteditable="true"]'
                            ]
                            textBox = None
                            for selector in text_input_selectors:
                                try:
                                    textBox = WebDriverWait(self.__driver, 3).until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                    log.debug(f"Found text input with selector: {selector}")
                                    break
                                except:
                                    continue
                            if textBox is None:
                                raise Exception("No text input element found with any selector")
                        except Exception as e:
                            log.error(f"Text input not found for {num}: {e}")
                            continue
                        time.sleep(1)
                        log.debug(f"Setting text in textbox: {fallback_text}")
                        textBox.clear()
                        time.sleep(0.5)
                        try:
                            # Remove JavaScript fallback, use clipboard then send_keys again
                            self.copyToClipboard(fallback_text)
                            textBox.send_keys(Keys.CONTROL, 'v')
                            log.debug("Text set using clipboard paste")
                        except Exception as e2:
                            log.debug(f"Clipboard method failed: {e2}")
                            try:
                                textBox.send_keys(fallback_text)
                                log.debug("Text set using direct typing (last fallback)")
                            except Exception as e3:
                                log.debug(f"Final send_keys failed: {e3}")
                        time.sleep(1)
                        try:
                            pasted_text = textBox.get_attribute('textContent') or textBox.get_attribute('innerText') or ''
                            log.debug(f"Text in textbox after setting: '{pasted_text}'")
                        except:
                            log.debug("Could not verify text content")
                        log.debug("Sending message")
                        try:
                            textBox.send_keys(Keys.RETURN)
                            log.debug("Message sent with RETURN key")
                        except Exception as e:
                            log.debug(f"RETURN failed, trying ENTER: {e}")
                            textBox.send_keys(Keys.ENTER)
                            log.debug("Message sent with ENTER key")
                        time.sleep(2)
                        f += 1
                        self.lcdNumber_wa.emit(f)
                        logtxt = f"Number::{num} => Sent (text only fallback)."
                        self.wa.emit(f"{num}")
                        log.debug(f"Message sent successfully to {num} (text only fallback)")
                        continue
                    time.sleep(2)
                    # Wait for caption textbox
                    try:
                        log.debug(f"Starting caption textbox search for {num}")
                        
                        # Try multiple possible selectors for the caption textbox
                        caption_selectors = [
                            '//div[@role="textbox"]',
                            '//div[@contenteditable="true"][@data-tab="10"]',
                            '//div[@contenteditable="true"][@data-tab="6"]',
                            '//div[contains(@class, "copyable-text")]//div[@contenteditable="true"]',
                            '//div[@title="Type a message"]'
                        ]
                        
                        caption = None
                        for i, selector in enumerate(caption_selectors):
                            try:
                                log.debug(f"Trying caption selector {i+1}/{len(caption_selectors)}: {selector}")
                                caption = WebDriverWait(self.__driver, 3).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                log.debug(f"Found caption textbox with selector: {selector}")
                                break
                            except Exception as e:
                                log.debug(f"Caption selector {i+1} failed: {str(e)}")
                                continue
                        
                        if caption is None:
                            # Try to find any textbox elements for debugging
                            log.debug("No caption textbox found, searching for any textbox elements...")
                            try:
                                all_textboxes = self.__driver.find_elements(By.XPATH, "//div[@contenteditable='true'] | //div[@role='textbox']")
                                log.debug(f"Found {len(all_textboxes)} textbox elements")
                                for i, elem in enumerate(all_textboxes[:3]):  # Log first 3 elements
                                    try:
                                        role_attr = elem.get_attribute('role') or 'N/A'
                                        data_tab = elem.get_attribute('data-tab') or 'N/A'
                                        class_attr = elem.get_attribute('class') or 'N/A'
                                        title_attr = elem.get_attribute('title') or 'N/A'
                                        log.debug(f"Textbox {i+1}: role='{role_attr}', data-tab='{data_tab}', class='{class_attr}', title='{title_attr}'")
                                    except:
                                        log.debug(f"Textbox {i+1}: Could not get attributes")
                            except Exception as e:
                                log.debug(f"Error searching for textbox elements: {e}")
                            
                            raise Exception("No caption textbox found with any selector")
                            
                    except Exception as e:
                        log.error(f"Caption textbox not found for {num}: {e}")
                        continue
                    if self.text != '' and self.text != ' ':
                        # Clean the caption text first
                        cleaned_caption = self.clean_caption_text(self.text)
                        log.debug(f"Setting cleaned caption text: {cleaned_caption[:100]}...")
                        
                        # Method 1: Try using JavaScript to set the text (bypasses ChromeDriver limitations)
                        try:
                            log.debug("Attempting to set caption using JavaScript...")
                            # More robust JavaScript method that handles Unicode better
                            js_code = """
                            var element = arguments[0];
                            var text = arguments[1];
                            
                            // Clear the element first
                            element.textContent = '';
                            element.innerText = '';
                            
                            // Set the text content
                            element.textContent = text;
                            element.innerText = text;
                            
                            // Trigger multiple events to ensure WhatsApp recognizes the change
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                            element.dispatchEvent(new Event('keyup', { bubbles: true }));
                            
                            // Also try setting the value property if it exists
                            if (element.value !== undefined) {
                                element.value = text;
                            }
                            
                            return element.textContent || element.innerText || '';
                            """
                            result = self.__driver.execute_script(js_code, caption, cleaned_caption)
                            log.debug(f"Caption text set using JavaScript, result length: {len(result) if result else 0}")
                        except Exception as e:
                            log.debug(f"JavaScript method failed: {e}")
                            # Method 2: Try using clipboard paste
                            try:
                                log.debug("Attempting to set caption using clipboard paste...")
                                self.copyToClipboard(cleaned_caption)
                                caption.send_keys(Keys.CONTROL, 'v')
                                log.debug("Caption text set using clipboard paste")
                            except Exception as e2:
                                log.debug(f"Clipboard method failed: {e2}")
                                # Method 3: Try direct typing with cleaned text
                                try:
                                    log.debug("Attempting to set caption using direct typing...")
                                    caption.send_keys(cleaned_caption)
                                    log.debug("Caption text set using direct typing")
                                except Exception as e3:
                                    log.debug(f"Direct typing failed: {e3}")
                                    # Method 4: Try character by character typing
                                    try:
                                        log.debug("Attempting to set caption character by character...")
                                        # Remove character limit - send the full text
                                        for char in cleaned_caption:
                                            try:
                                                caption.send_keys(char)
                                            except Exception as char_error:
                                                log.debug(f"Character typing failed at character: {char_error}")
                                                break
                                        log.debug("Caption text set character by character")
                                    except Exception as e4:
                                        log.debug(f"Character by character typing failed: {e4}")
                        
                        time.sleep(1)
                        
                        # Verify the caption was set (skip verification if ChromeDriver has Unicode issues)
                        try:
                            # Use JavaScript to get the text content to avoid ChromeDriver Unicode issues
                            caption_text = self.__driver.execute_script("return arguments[0].textContent || arguments[0].innerText || '';", caption)
                            log.debug(f"Caption text after setting: '{caption_text[:100]}...'")
                            if not caption_text.strip():
                                log.warning("Caption appears to be empty after setting - trying alternative method")
                                # Try setting focus and typing again
                                caption.click()
                                time.sleep(0.5)
                                # Try clipboard method again
                                try:
                                    self.copyToClipboard(cleaned_caption)
                                    caption.send_keys(Keys.CONTROL, 'v')
                                    log.debug("Caption text set using clipboard paste (retry)")
                                except Exception as retry_e:
                                    log.debug(f"Clipboard retry failed: {retry_e}")
                                    # Try direct typing as last resort
                                    try:
                                        caption.send_keys(cleaned_caption)
                                        log.debug("Caption text set using direct typing (retry)")
                                    except Exception as type_e:
                                        log.debug(f"Direct typing retry failed: {type_e}")
                        except Exception as e:
                            log.debug(f"Could not verify caption text: {e}")
                            # Don't fail here - the text might have been set successfully but we can't verify it
                            log.info("Caption verification failed, but proceeding with send attempt")
                    
                    # Send the message
                    log.debug("Attempting to send the message...")
                    try:
                        log.debug("Trying to send with RETURN key...")
                        caption.send_keys(Keys.RETURN)
                        log.debug("Message sent with RETURN key")
                    except Exception as e:
                        log.debug(f"RETURN failed, trying ENTER: {e}")
                        try:
                            caption.send_keys(Keys.ENTER)
                            log.debug("Message sent with ENTER key")
                        except Exception as e2:
                            log.debug(f"ENTER also failed: {e2}")
                            # Try clicking a send button as last resort
                            try:
                                send_buttons = self.__driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Send') or contains(@title, 'Send') or contains(@class, 'send')]")
                                if send_buttons:
                                    log.debug(f"Found {len(send_buttons)} send buttons, clicking first one...")
                                    send_buttons[0].click()
                                    log.debug("Message sent by clicking send button")
                                else:
                                    log.debug("No send buttons found")
                            except Exception as e3:
                                log.debug(f"Send button click failed: {e3}")
                    
                    log.debug("Message sending attempt completed")
                    
                    # If we have text but couldn't set it as caption, try sending it as a separate message
                    caption_was_set = False
                    try:
                        caption_was_set = bool(caption_text and caption_text.strip())
                    except:
                        caption_was_set = False
                    
                    if self.text and self.text.strip() and not caption_was_set:
                        log.info("Caption appears to be empty, attempting to send text as separate message...")
                        try:
                            # Wait a bit for the image to be sent
                            time.sleep(2)
                            
                            # Find the text input again
                            text_input_selectors = [
                                '//div[@title="Type a message"]',
                                '//div[@contenteditable="true"][@data-tab="10"]',
                                '//div[@contenteditable="true"][@data-tab="6"]',
                                '//div[@role="textbox"]',
                                '//div[contains(@class, "copyable-text")]//div[@contenteditable="true"]'
                            ]
                            
                            textBox = None
                            for selector in text_input_selectors:
                                try:
                                    textBox = WebDriverWait(self.__driver, 3).until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                    log.debug(f"Found text input for separate message with selector: {selector}")
                                    break
                                except:
                                    continue
                            
                            if textBox:
                                # Set the text using clipboard method
                                self.copyToClipboard(cleaned_caption)
                                textBox.send_keys(Keys.CONTROL, 'v')
                                time.sleep(1)
                                
                                # Send the text message
                                textBox.send_keys(Keys.RETURN)
                                log.debug("Separate text message sent successfully")
                                time.sleep(2)
                            else:
                                log.warning("Could not find text input for separate message")
                                
                        except Exception as e:
                            log.error(f"Failed to send separate text message: {e}")
                    
                    f += 1
                    self.lcdNumber_wa.emit(f)
                    logtxt = f"Number::{num} => Sent"
                    self.wa.emit(f"{num}")
                    log.debug(f"Message sent successfully to {num}")
                time.sleep(randint(self.sleepMin, self.sleepMax))
            except:
                logtxt = f"Error To Number = {num} "
                log.exception("Error sendIMG")
                continue
            finally:
                i += 1
                self.lcdNumber_reviewed.emit(i)
                self.LogBox.emit(logtxt)
        self.EndWork.emit("-- Send Image completed --")
        self.stop()
        self.isRunning = False

    def addAcc(self):
        try:
            log.debug("Add Account")
            if self.remember:
                if self.path == '':
                    cacheName = str(random.randint(1, 9999999))
                    self.path = cacheName
                self.save_profile(self.get_active_session(),
                                  f"./temp/cache/{self.path}")
                log.debug('File saved.')
            log.debug("thread:", self.counter_start)
            self.EndWork.emit("-- Add Account completed --")
            self.isRunning = False
        except:
            log.exception("Add Account ->:")

    def run(self):
        while self.isRunning == True:
            if self.step == 'A':
                self.ANALYZ()
            elif self.step == 'M':
                self.SendTEXT()
            elif self.step == 'I':
                self.SendIMG()
            elif self.step == 'Add':
                self.addAcc()

    def stop(self):
        self.isRunning = False
        log.debug('stopping thread...')
        try:
            self.__driver.quit()
        except:
            pass
        # self.terminate()

    def __init_browser(self):
        if self.__browser_choice == CHROME:
            self.__browser_options = webdriver.ChromeOptions()

            if self.__platform == 'windows':
                self.__browser_user_dir = os.path.join(os.environ['USERPROFILE'],
                                                       'Appdata', 'Local', 'Google', 'Chrome', 'User Data')
            elif self.__platform == 'linux':
                self.__browser_user_dir = os.path.join(
                    os.environ['HOME'], '.config', 'google-chrome')

        elif self.__browser_choice == FIREFOX:
            self.__browser_options = webdriver.FirefoxOptions()

            if self.__platform == 'windows':
                self.__browser_user_dir = os.path.join(
                    os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
                self.__browser_profile_list = os.listdir(
                    self.__browser_user_dir)
            elif self.__platform == 'linux':
                self.__browser_user_dir = os.path.join(
                    os.environ['HOME'], '.mozilla', 'firefox')

        self.__browser_options.headless = True
        self.__refresh_profile_list()

    def __refresh_profile_list(self):
        if self.__browser_choice == CHROME:
            self.__browser_profile_list = ['']
            for profile_dir in os.listdir(self.__browser_user_dir):
                if 'profile' in profile_dir.lower():
                    if profile_dir != 'System Profile':
                        self.__browser_profile_list.append(profile_dir)
        elif self.__browser_choice == FIREFOX:
            # TODO: consider reading out the profiles.ini
            self.__browser_profile_list = []
            for profile_dir in os.listdir(self.__browser_user_dir):
                if not profile_dir.endswith('.default'):
                    if os.path.isdir(os.path.join(self.__browser_user_dir, profile_dir)):
                        self.__browser_profile_list.append(profile_dir)

    def __get_indexed_db(self):
        self.__driver.execute_script('window.waScript = {};'
                                     'window.waScript.waSession = undefined;'
                                     'function getAllObjects() {'
                                     'window.waScript.dbName = "wawc";'
                                     'window.waScript.osName = "user";'
                                     'window.waScript.db = undefined;'
                                     'window.waScript.transaction = undefined;'
                                     'window.waScript.objectStore = undefined;'
                                     'window.waScript.getAllRequest = undefined;'
                                     'window.waScript.request = indexedDB.open(window.waScript.dbName);'
                                     'window.waScript.request.onsuccess = function(event) {'
                                     'window.waScript.db = event.target.result;'
                                     'window.waScript.transaction = window.waScript.db.transaction('
                                     'window.waScript.osName);'
                                     'window.waScript.objectStore = window.waScript.transaction.objectStore('
                                     'window.waScript.osName);'
                                     'window.waScript.getAllRequest = window.waScript.objectStore.getAll();'
                                     'window.waScript.getAllRequest.onsuccess = function(getAllEvent) {'
                                     'window.waScript.waSession = getAllEvent.target.result;'
                                     '};'
                                     '};'
                                     '}'
                                     'getAllObjects();')
        while not self.__driver.execute_script('return window.waScript.waSession != undefined;'):
            time.sleep(1)
        wa_session_list = self.__driver.execute_script(
            'return window.waScript.waSession;')
        return wa_session_list

    def __get_profile_storage(self, profile_name=None):
        self.__refresh_profile_list()

        if profile_name is not None and profile_name not in self.__browser_profile_list:
            raise ValueError(
                'The specified profile_name was not found. Make sure the name is correct.')

        if profile_name is None:
            self.__start_visible_session()
        else:
            self.__start_invisible_session(profile_name)

        indexed_db = self.__get_indexed_db()

        self.__driver.quit()

        return indexed_db

    def __start_session(self, options, profile_name=None, wait_for_login=True):
        if profile_name is None:
            if self.__browser_choice == CHROME:
                self.__driver = webdriver.Chrome(options=options, service=self.service)
                self.__driver.set_window_position(0, 0)
                self.__driver.set_window_size(670, 800)
            elif self.__browser_choice == FIREFOX:
                self.__driver = webdriver.Firefox(options=options)

            self.__driver.get(self.__URL)

            if wait_for_login:
                verified_wa_profile_list = False
                while not verified_wa_profile_list:
                    time.sleep(1)
                    verified_wa_profile_list = False
                    for object_store_obj in self.__get_indexed_db():
                        if 'WASecretBundle' in object_store_obj['key']:
                            verified_wa_profile_list = True
                            break
        else:
            if self.__browser_choice == CHROME:
                options.add_argument(
                    'user-data-dir=%s' % os.path.join(self.__browser_user_dir, profile_name))
                self.__driver = webdriver.Chrome(options=options, service=self.service)
            elif self.__browser_choice == FIREFOX:
                fire_profile = webdriver.FirefoxProfile(
                    os.path.join(self.__browser_user_dir, profile_name))
                self.__driver = webdriver.Firefox(
                    fire_profile, options=options)

            self.__driver.get(self.__URL)

    def __start_visible_session(self, profile_name=None, wait_for_login=True):
        options = self.__browser_options
        options.headless = False
        self.__refresh_profile_list()

        if profile_name is not None and profile_name not in self.__browser_profile_list:
            raise ValueError(
                'The specified profile_name was not found. Make sure the name is correct.')

        self.__start_session(options, profile_name, wait_for_login)

    def __start_invisible_session(self, profile_name=None):
        self.__refresh_profile_list()
        if profile_name is not None and profile_name not in self.__browser_profile_list:
            raise ValueError(
                'The specified profile_name was not found. Make sure the name is correct.')

        self.__start_session(self.__browser_options, profile_name)

    def set_browser(self, browser):
        if type(browser) == str:
            if browser.lower() == 'chrome':
                self.__browser_choice = CHROME
            elif browser.lower() == 'firefox':
                self.__browser_choice = FIREFOX
            else:
                raise ValueError(
                    'The specified browser is invalid. Try to use "chrome" or "firefox" instead.')
        else:
            if browser == CHROME:
                pass
            elif browser == FIREFOX:
                pass
            else:
                raise ValueError(
                    'Browser type invalid. Try to use WaWebSession.CHROME or WaWebSession.FIREFOX instead.')

            self.__browser_choice = browser

    def get_active_session(self, use_profile=None):
        profile_storage_dict = {}
        use_profile_list = []
        self.__refresh_profile_list()

        if use_profile and use_profile not in self.__browser_profile_list:
            raise ValueError('Profile does not exist: %s', use_profile)
        elif use_profile is None:
            return self.__get_profile_storage()
        elif use_profile and use_profile in self.__browser_profile_list:
            use_profile_list.append(use_profile)
        elif type(use_profile) == list:
            use_profile_list.extend(self.__browser_profile_list)
        else:
            raise ValueError(
                "Invalid profile provided. Make sure you provided a list of profiles or a profile name.")

        for profile in use_profile_list:
            profile_storage_dict[profile] = self.__get_profile_storage(profile)

        return profile_storage_dict

    def create_new_session(self):
        return self.__get_profile_storage()

    def access_by_obj(self, wa_profile_list):
        verified_wa_profile_list = False
        for object_store_obj in wa_profile_list:
            if 'WASecretBundle' in object_store_obj['key']:
                verified_wa_profile_list = True
                break

        if not verified_wa_profile_list:
            raise ValueError(
                'This is not a valid profile list. Make sure you only pass one session to this method.')

        self.__start_visible_session(wait_for_login=False)
        self.__driver.execute_script('window.waScript = {};'
                                     'window.waScript.insertDone = 0;'
                                     'window.waScript.jsonObj = undefined;'
                                     'window.waScript.setAllObjects = function (_jsonObj) {'
                                     'window.waScript.jsonObj = _jsonObj;'
                                     'window.waScript.dbName = "wawc";'
                                     'window.waScript.osName = "user";'
                                     'window.waScript.db;'
                                     'window.waScript.transaction;'
                                     'window.waScript.objectStore;'
                                     'window.waScript.clearRequest;'
                                     'window.waScript.addRequest;'
                                     'window.waScript.request = indexedDB.open(window.waScript.dbName);'
                                     'window.waScript.request.onsuccess = function(event) {'
                                     'window.waScript.db = event.target.result;'
                                     'window.waScript.transaction = window.waScript.db.transaction('
                                     'window.waScript.osName, "readwrite");'
                                     'window.waScript.objectStore = window.waScript.transaction.objectStore('
                                     'window.waScript.osName);'
                                     'window.waScript.clearRequest = window.waScript.objectStore.clear();'
                                     'window.waScript.clearRequest.onsuccess = function(clearEvent) {'
                                     'for (var i=0; i<window.waScript.jsonObj.length; i++) {'
                                     'window.waScript.addRequest = window.waScript.objectStore.add('
                                     'window.waScript.jsonObj[i]);'
                                     'window.waScript.addRequest.onsuccess = function(addEvent) {'
                                     'window.waScript.insertDone++;'
                                     '};'
                                     '}'
                                     '};'
                                     '};'
                                     '}')
        self.__driver.execute_script(
            'window.waScript.setAllObjects(arguments[0]);', wa_profile_list)

        while not self.__driver.execute_script(
                'return (window.waScript.insertDone == window.waScript.jsonObj.length);'):
            time.sleep(1)

        self.__driver.refresh()

        # while True:
        #     try:
        #         _ = self.__driver.window_handles
        #         time.sleep(1)
        #     except WebDriverException:
        #         break

    def access_by_file(self, profile_file):
        profile_file = os.path.normpath(profile_file)

        if os.path.isfile(profile_file):
            with open(profile_file, 'r') as file:
                session_info = json.load(file)

            # Check if this is the new format (with user_data_dir)
            if 'user_data_dir' in session_info:
                log.debug(f"Loading session from user data directory: {session_info['user_data_dir']}")
                # Use the saved user data directory
                option = webdriver.ChromeOptions()
                option.add_argument("--disable-notifications")
                option.add_argument("--disable-blink-features=AutomationControlled")
                option.add_experimental_option("excludeSwitches", ["enable-automation"])
                option.add_experimental_option('useAutomationExtension', False)
                option.add_argument(f"--user-data-dir={session_info['user_data_dir']}")
                
                try:
                    self.__driver = webdriver.Chrome(options=option, service=self.service)
                    self.__driver.set_window_position(0, 0)
                    self.__driver.set_window_size(1080, 840)
                    self.__driver.get(self.__URL)
                    log.debug("Session loaded successfully from user data directory")
                except Exception as e:
                    log.error(f"Failed to load session: {e}")
                    # Fallback to normal browser initialization
                    self.driverBk()
                    self.__driver.get(self.__URL)
            else:
                # Handle old format (WhatsApp session data)
                wa_profile_list = session_info
                verified_wa_profile_list = False
                for object_store_obj in wa_profile_list:
                    if 'WASecretBundle' in object_store_obj['key']:
                        verified_wa_profile_list = True
                        break
                if verified_wa_profile_list:
                    self.access_by_obj(wa_profile_list)
                else:
                    raise ValueError('There might be multiple profiles stored in this file.'
                                     ' Make sure you only pass one WaSession file to this method.')
        else:
            raise FileNotFoundError(
                'Make sure you pass a valid WaSession file to this method.')

    def save_profile(self, wa_profile_list, file_path):
        file_path = os.path.normpath(file_path)

        verified_wa_profile_list = False
        for object_store_obj in wa_profile_list:
            if 'key' in object_store_obj:
                if 'WASecretBundle' in object_store_obj['key']:
                    verified_wa_profile_list = True
                    break
        if verified_wa_profile_list:
            with open(file_path, 'w') as file:
                json.dump(wa_profile_list, file, indent=4)
        else:
            saved_profiles = 0
            for profile_name in wa_profile_list.keys():
                profile_storage = wa_profile_list[profile_name]
                verified_wa_profile_list = False
                for object_store_obj in profile_storage:
                    if 'key' in object_store_obj:
                        if 'WASecretBundle' in object_store_obj['key']:
                            verified_wa_profile_list = True
                            break
                if verified_wa_profile_list:
                    single_profile_name = os.path.basename(
                        file_path) + '-' + profile_name
                    self.save_profile(profile_storage, os.path.join(
                        os.path.dirname(file_path), single_profile_name))
                    saved_profiles += 1
            if saved_profiles > 0:
                pass
            else:
                raise ValueError(
                    'Could not find any profiles in the list. Make sure to specified file path is correct.')

    def clean_caption_text(self, text):
        """Clean HTML tags and special characters from caption text while preserving formatting"""
        import re
        import html
        import unicodedata
        
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize Unicode characters to handle special characters better
        text = unicodedata.normalize('NFKC', text)
        
        # Replace HTML line breaks with actual newlines
        text = text.replace('<br>', '\n')
        text = text.replace('<br/>', '\n')
        text = text.replace('<br />', '\n')
        
        # Replace paragraph tags with double newlines to preserve spacing
        text = text.replace('</p>', '\n\n')
        text = text.replace('<p>', '')
        
        # Replace list items with proper formatting
        text = text.replace('<li>', '• ')
        text = text.replace('</li>', '\n')
        text = text.replace('<ul>', '\n')
        text = text.replace('</ul>', '\n')
        text = text.replace('<ol>', '\n')
        text = text.replace('</ol>', '\n')
        
        # Replace heading tags with proper formatting
        text = text.replace('<h1>', '\n')
        text = text.replace('</h1>', '\n')
        text = text.replace('<h2>', '\n')
        text = text.replace('</h2>', '\n')
        text = text.replace('<h3>', '\n')
        text = text.replace('</h3>', '\n')
        text = text.replace('<h4>', '\n')
        text = text.replace('</h4>', '\n')
        text = text.replace('<h5>', '\n')
        text = text.replace('</h5>', '\n')
        text = text.replace('<h6>', '\n')
        text = text.replace('</h6>', '\n')
        
        # Remove other HTML tags but preserve their content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Clean up multiple consecutive newlines (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace but preserve internal formatting
        text = text.strip()
        
        # Ensure the text is properly encoded for clipboard operations
        try:
            # Test if the text can be encoded/decoded properly
            text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            # If there are encoding issues, try to fix them
            log.warning("Unicode encoding issues detected, attempting to fix...")
            # Remove or replace problematic characters
            text = ''.join(char for char in text if ord(char) < 0x10000)  # Keep only BMP characters
        
        # Don't limit length - let WhatsApp handle it
        # if len(text) > 1000:
        #     text = text[:1000] + "..."
        
        log.debug(f"Cleaned caption text length: {len(text)} characters")
        log.debug(f"Cleaned caption preview: {text[:200]}...")
        return text
