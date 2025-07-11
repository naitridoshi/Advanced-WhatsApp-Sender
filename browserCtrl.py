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
                            # Fallback to JavaScript
                            try:
                                self.__driver.execute_script("arguments[0].textContent = arguments[1];", textBox, self.text)
                                self.__driver.execute_script("arguments[0].innerText = arguments[1];", textBox, self.text)
                                log.debug("Text set using JavaScript")
                            except Exception as e3:
                                log.debug(f"JavaScript method failed: {e3}")
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
                        
                        # Try multiple possible selectors for the attachment button
                        attach_selectors = [
                            '//span[@data-icon="attach-menu-plus"]',
                            '//span[@data-icon="attach-menu"]',
                            '//div[@title="Attach"]',
                            '//div[contains(@aria-label, "Attach")]',
                            '//div[@role="button"][contains(@aria-label, "Attach")]',
                            '#main > footer > div.x1n2onr6.xhtitgo.x9f619.x78zum5.x1q0g3np.xuk3077.xjbqb8w.x1wiwyrm.xvc5jky.x11t971q.xquzyny.xnpuxes.copyable-area > div > span > div > div._ak1r > div > div.x100vrsf.x1vqgdyp.x78zum5.x6s0dn4.xpvyfi4 > button > span'
                        ]
                        
                        attach_btn = None
                        for selector in attach_selectors:
                            try:
                                attach_btn = WebDriverWait(self.__driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                log.debug(f"Found attachment button with selector: {selector}")
                                break
                            except:
                                continue
                        
                        if attach_btn is None:
                            raise Exception("No attachment button found with any selector")
                        
                        attach_btn.click()
                    except Exception as e:
                        log.error(f"Attachment button not found for {num}: {e}")
                        # Fallback: always try to send text only
                        fallback_text = self.text if self.text.strip() else "Attachment could not be sent"
                        log.info(f"Falling back to sending text only for {num}")
                        # Wait for text input element - try multiple selectors
                        try:
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC
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
                            self.__driver.execute_script("arguments[0].textContent = arguments[1];", textBox, fallback_text)
                            self.__driver.execute_script("arguments[0].innerText = arguments[1];", textBox, fallback_text)
                            log.debug("Text set using JavaScript")
                        except Exception as e:
                            log.debug(f"JavaScript method failed: {e}")
                            try:
                                self.copyToClipboard(fallback_text)
                                textBox.send_keys(Keys.CONTROL, 'v')
                                log.debug("Text set using clipboard paste")
                            except Exception as e2:
                                log.debug(f"Clipboard method failed: {e2}")
                                textBox.send_keys(fallback_text)
                                log.debug("Text set using direct typing")
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
                    # Wait for file input element
                    try:
                        attch = WebDriverWait(self.__driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'))
                        )
                        attch.send_keys(self.path)
                    except Exception as e:
                        log.error(f"File input not found for {num}: {e}")
                        continue
                    time.sleep(2)
                    # Wait for caption textbox
                    try:
                        # Try multiple possible selectors for the caption textbox
                        caption_selectors = [
                            '//div[@role="textbox"]',
                            '//div[@contenteditable="true"][@data-tab="10"]',
                            '//div[@contenteditable="true"][@data-tab="6"]',
                            '//div[contains(@class, "copyable-text")]//div[@contenteditable="true"]',
                            '//div[@title="Type a message"]'
                        ]
                        
                        caption = None
                        for selector in caption_selectors:
                            try:
                                caption = WebDriverWait(self.__driver, 3).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                log.debug(f"Found caption textbox with selector: {selector}")
                                break
                            except:
                                continue
                        
                        if caption is None:
                            raise Exception("No caption textbox found with any selector")
                            
                    except Exception as e:
                        log.error(f"Caption textbox not found for {num}: {e}")
                        continue
                    if self.text != '' and self.text != ' ':
                        log.debug(f"Setting caption text: {self.text}")
                        
                        # Method 1: Try using JavaScript to set the text directly
                        try:
                            self.__driver.execute_script("arguments[0].textContent = arguments[1];", caption, self.text)
                            self.__driver.execute_script("arguments[0].innerText = arguments[1];", caption, self.text)
                            log.debug("Caption text set using JavaScript")
                        except Exception as e:
                            log.debug(f"JavaScript method failed: {e}")
                            # Method 2: Fallback to clipboard paste
                            try:
                                self.copyToClipboard(self.text)
                                caption.send_keys(Keys.CONTROL, 'v')
                                log.debug("Caption text set using clipboard paste")
                            except Exception as e2:
                                log.debug(f"Clipboard method failed: {e2}")
                                # Method 3: Type the text character by character
                                caption.send_keys(self.text)
                                log.debug("Caption text set using direct typing")
                        
                        time.sleep(1)
                    try:
                        caption.send_keys(Keys.RETURN)
                    except Exception:
                        caption.send_keys(Keys.ENTER)
                    f += 1
                    self.lcdNumber_wa.emit(f)
                    logtxt = f"Number::{num} => Sent"
                    self.wa.emit(f"{num}")
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
