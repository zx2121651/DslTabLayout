import time

class ScraperPresenter:
    """
    The Presenter in the MVP pattern.
    Orchestrates the Model and the View.
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view

    def run(self):
        """
        Runs the main application logic.
        """
        self.view.show_message("--- 考试宝题库智能提取脚本启动 (MVP版) ---")

        try:
            self.model.initialize_driver()

            if not self.model.login_and_navigate():
                self.view.show_error("登录或导航失败，程序终止。")
                return

            if not self.model.switch_to_recite_mode():
                self.view.show_error("切换模式失败，程序终止。")
                return

            question_counter = 1
            while True:
                self.view.show_message(f"\n--- 开始处理第 {question_counter} 题 ---")

                # Get the element for the current question
                question_element = self.model.get_current_question_element()
                if not question_element:
                    self.view.show_message("无法找到题目，任务结束。")
                    break

                # Extract data from the element
                extracted_data = self.model.extract_data_from_element(question_element)

                if extracted_data and "error" not in extracted_data:
                    self.view.show_data(extracted_data)
                    self.model.save_data(extracted_data, question_counter)
                else:
                    self.view.show_message("未能从图片中提取有效数据，跳过此题。")

                # Navigate to the next question
                if not self.model.go_to_next_question(question_element):
                    break # Loop breaks if there's no next question

                question_counter += 1

        except Exception as e:
            self.view.show_error(f"发生未知错误: {e}")
        finally:
            self.model.close_driver()
            self.view.show_success("脚本执行完毕。")
