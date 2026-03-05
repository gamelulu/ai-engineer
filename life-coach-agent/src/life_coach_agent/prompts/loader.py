from pathlib import Path
from typing import Iterable


_BASE_DIR = Path(__file__).resolve().parent


def _normalize_name(name: str) -> str:
    """`foo` 또는 `foo.md` 같은 이름을 `foo.md`로 정규화."""
    return name if name.endswith(".md") else f"{name}.md"


def load_prompt(name: str) -> str:
    """단일 프롬프트 파일을 불러온다.

    - `name`에는 확장자를 생략해도 되고(`system_prompt`),
      `.md`를 포함해도 된다(`system_prompt.md`).
    - 기준 디렉터리는 `prompts/` 폴더이다.
    """
    filename = _normalize_name(name)
    path = _BASE_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def load_prompts(names: Iterable[str]) -> str:
    """여러 프롬프트 파일을 순서대로 불러와 하나의 문자열로 합친다."""
    parts = [load_prompt(name).strip() for name in names]
    # 각 프롬프트 사이에 빈 줄 하나 삽입
    return "\n\n".join(part for part in parts if part)

