import json

class CliView:
    """
    Handles all command-line output for the application.
    """

    def show_message(self, message: str):
        """Displays a standard informational message."""
        print(f"[INFO] {message}")

    def show_error(self, message: str):
        """Displays an error message."""
        print(f"[错误] {message}")

    def show_success(self, message: str):
        """Displays a success message."""
        print(f"[成功] {message}")

    def show_data(self, data: dict | None):
        """
        Displays the extracted data in a readable format.

        Args:
            data: The dictionary of extracted data.
        """
        if data:
            print("[数据预览] ---")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            print("---")
        else:
            self.show_message("本次未提取到数据。")

    def get_input(self, prompt: str) -> str:
        """Gets input from the user."""
        return input(prompt)
