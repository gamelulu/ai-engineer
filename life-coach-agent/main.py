import sys
from pathlib import Path

import dotenv

dotenv.load_dotenv()

# src/ 디렉터리를 Python path 에 추가
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from life_coach_agent.app import run  # type: ignore

run()
