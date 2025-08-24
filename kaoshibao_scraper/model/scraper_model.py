import os
import time
import json
import random
import sys
from io import BytesIO

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image
import google.generativeai as genai

class ScraperModel:
    """
    Handles all business logic for the scraper.
    - Browser interaction (Selenium)
    - AI data extraction (Gemini)
    - File I/O
    """

    def __init__(self, config, view):
        self.config = config
        self.view = view
        self.driver = None
        self.wait = None
        self._configure_ai()

    def _configure_ai(self):
        try:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        except Exception as e:
            self.view.show_error(f"Google Gemini AI 配置失败: {e}")
            sys.exit(1)

    def initialize_driver(self):
        self.view.show_message("正在初始化浏览器驱动...")
        try:
            # This part needs to be adapted by the user for their specific fingerprint browser.
            self.view.show_message("注意：当前为演示模式。请根据您的指纹浏览器文档修改此部分代码。")
            self.driver = webdriver.Chrome(options=webdriver.ChromeOptions())
            self.wait = WebDriverWait(self.driver, 20)
            self.view.show_message("浏览器驱动初始化成功。")
        except Exception as e:
            self.view.show_error(f"无法初始化WebDriver: {e}")
            sys.exit(1)

    def login_and_navigate(self):
        try:
            self.view.show_message("正在导航至登录页面...")
            self.driver.get("https://www.kaoshibao.com/login")

            self.view.show_message("正在输入登录信息...")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='请输入手机号']"))).send_keys(self.config.KAOSHIBAO_USERNAME)
            self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']").send_keys(self.config.KAOSHIBAO_PASSWORD)
            self.driver.find_element(By.CSS_SELECTOR, "button.login-btn").click()

            self.view.show_message("登录成功，等待页面跳转...")
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "header-avator-img")))

            self.view.show_message(f"导航至目标题库页面: {self.config.START_URL}")
            self.driver.get(self.config.START_URL)
            return True
        except TimeoutException as e:
            self.view.show_error(f"登录或导航失败（超时）: {e}")
            return False

    def switch_to_recite_mode(self):
        try:
            self.view.show_message("正在切换至“背题模式”...")
            recite_mode_button_selector = "//div[contains(text(), '背题模式')]"
            self.wait.until(EC.element_to_be_clickable((By.XPATH, recite_mode_button_selector))).click()

            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "analysis-container")))
            self.view.show_message("已成功切换到“背题模式”。")
            return True
        except TimeoutException:
            self.view.show_error("切换“背题模式”失败（超时）。")
            return False

    def get_current_question_element(self):
        try:
            question_container_selector = "div.question-container"
            return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, question_container_selector)))
        except TimeoutException:
            self.view.show_error("无法在页面上找到题目容器。")
            return None

    def _parse_with_ai(self, image: Image.Image) -> dict | None:
        self.view.show_message("正在将截图发送至AI进行解析...")
        prompt = """
        你是一个专业的题库数据分析专家。你的任务是严格、准确地从给出的题目截图中提取信息，并以指定的JSON格式返回。
        请严格按照以下JSON格式返回：
        {
          "question_body": "题干内容",
          "options": ["A. 选项一", "B. 选项二"],
          "correct_answer": "A",
          "analysis": "答案解析内容"
        }
        """
        try:
            response = self.vision_model.generate_content([prompt, image], stream=False)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            self.view.show_message("AI解析成功。")
            return json.loads(cleaned_response)
        except Exception as e:
            self.view.show_error(f"AI视觉模型解析失败: {e}")
            return None

    def extract_data_from_element(self, element) -> dict | None:
        try:
            self.view.show_message("正在对题目区域进行截图...")
            png_data = element.screenshot_as_png
            image = Image.open(BytesIO(png_data))
            return self._parse_with_ai(image)
        except Exception as e:
            self.view.show_error(f"截图或图像处理失败: {e}")
            return None

    def save_data(self, data, question_counter):
        try:
            os.makedirs(self.config.DATA_OUTPUT_DIR, exist_ok=True)
            filename = f"question_{question_counter}_{int(time.time())}.json"
            filepath = os.path.join(self.config.DATA_OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.view.show_message(f"成功提取并保存数据至: {filepath}")
        except Exception as e:
            self.view.show_error(f"保存文件失败: {e}")

    def go_to_next_question(self, old_element):
        try:
            delay = random.uniform(2.5, 5.0)
            self.view.show_message(f"拟人化延迟 {delay:.2f} 秒...")
            time.sleep(delay)

            self.view.show_message("正在查找“下一题”按钮...")
            next_button = self.driver.find_element(By.XPATH, "//span[contains(text(), '下一题')]")

            if next_button and next_button.is_displayed() and next_button.is_enabled():
                self.view.show_message("点击“下一题”...")
                next_button.click()
                self.wait.until(EC.staleness_of(old_element))
                return True
            else:
                self.view.show_message("未找到可点击的“下一题”按钮，任务可能已完成。")
                return False
        except (NoSuchElementException, TimeoutException):
            self.view.show_message("无法找到“下一题”按钮或页面未加载，任务结束。")
            return False

    def close_driver(self):
        if self.driver:
            self.view.show_message("正在关闭浏览器...")
            self.driver.quit()
            self.driver = None
            self.view.show_message("浏览器已关闭。")
