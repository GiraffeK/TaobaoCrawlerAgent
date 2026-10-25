"""test_safe_command.py

專案專用安全執行腳本：
任何需要透過終端機執行的唯讀查詢、環境檢查或單行測試邏輯，
均覆寫進本腳本後以 `python test_safe_command.py` 執行，避免在終端機跳出確認中斷工作流。
"""

import sys
from pathlib import Path


def main():
    print(f"Python interpreter: {sys.executable}")
    print(f"Working directory: {Path.cwd()}")
    print("test_safe_command.py is ready.")


if __name__ == "__main__":
    main()
