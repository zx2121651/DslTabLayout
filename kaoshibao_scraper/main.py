import sys

# --- App Components ---
from model.scraper_model import ScraperModel
from view.cli_view import CliView
from presenter.scraper_presenter import ScraperPresenter

def main():
    """
    Main entry point for the application.
    Initializes MVP components and runs the application.
    """
    # --- Configuration ---
    try:
        import config
    except ImportError:
        print("错误：配置文件 `config.py` 未找到。")
        print("请将 `config.py.example` 复制为 `config.py` 并填入您的配置信息。")
        sys.exit(1)

    # --- Initialization of MVP components ---
    view = CliView()
    model = ScraperModel(config, view)
    presenter = ScraperPresenter(model, view)

    # --- Run the application ---
    presenter.run()

if __name__ == "__main__":
    main()
