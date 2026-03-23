import base64
import io
import json
import os
from typing import Any

from google.genai import types  # type: ignore[import-unresolved]
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat
from google.adk.tools.tool_context import ToolContext  # type: ignore[import-unresolved]


def _font_candidates_by_style(font_style: str) -> list[str]:
    style = (font_style or "").lower()
    if style == "bold":
        return [
            "C:/Windows/Fonts/malgunbd.ttf",
            "C:/Windows/Fonts/NanumGothicBold.ttf",
            "C:/Windows/Fonts/malgun.ttf",
        ]
    if style == "cute":
        return [
            "C:/Windows/Fonts/NanumPen.ttf",
            "C:/Windows/Fonts/NanumGothic.ttf",
            "C:/Windows/Fonts/malgun.ttf",
        ]
    return [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
    ]


def _load_korean_font(size: int, font_style: str) -> ImageFont.ImageFont:
    font_candidates = _font_candidates_by_style(font_style)
    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int
) -> list[str]:
    if not text:
        return []

    # 한국어 문장 특성상 공백 기준 분할이 부정확할 수 있어 문자 단위로 줄바꿈
    chars = list(text)
    if not chars:
        return [text]

    lines: list[str] = []
    current = chars[0]
    for ch in chars[1:]:
        candidate = f"{current}{ch}"
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = ch
    lines.append(current)
    return lines


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sanitize_run_id(value: str) -> str:
    """파일명으로 안전한 run id 문자열로 정규화합니다."""
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_"))
    return cleaned[:48] if cleaned else "run"


def _parse_hex_rgba(color_hex: str, fallback: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    value = (color_hex or "").strip().lstrip("#")
    try:
        if len(value) == 6:
            return (
                int(value[0:2], 16),
                int(value[2:4], 16),
                int(value[4:6], 16),
                255,
            )
        if len(value) == 8:
            return (
                int(value[0:2], 16),
                int(value[2:4], 16),
                int(value[4:6], 16),
                int(value[6:8], 16),
            )
    except Exception:
        return fallback
    return fallback


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    outputs = getattr(response, "output", None) or []
    for item in outputs:
        contents = getattr(item, "content", None) or []
        for content in contents:
            text = getattr(content, "text", None)
            if text:
                return text
    return ""


def _recommend_text_layout(
    client: OpenAI, image_bytes: bytes, story_text: str, visual_description: str
) -> dict[str, Any]:
    default_layout = {
        "x_ratio": 0.5,
        "y_ratio": 0.88,
        "max_width_ratio": 0.82,
        "font_size": 34,
        "font_style": "regular",
        "text_color": "#FFFFFF",
        "stroke_color": "#111111",
        "stroke_width": 2,
        "align": "center",
    }

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = (
        "You are a typography layout assistant for children's storybook pages.\n"
        "Given the image and Korean story text, choose an appropriate text position and style.\n"
        "Return ONLY JSON with fields:\n"
        "x_ratio (0.1-0.9), y_ratio (0.1-0.95), max_width_ratio (0.4-0.95),\n"
        "font_size (20-64), font_style (regular|bold|cute),\n"
        "text_color (#RRGGBB), stroke_color (#RRGGBB), stroke_width (0-4), align (left|center|right).\n"
        "Do not include markdown or explanations.\n"
        f"Story text: {story_text}\n"
        f"Visual context: {visual_description}\n"
    )

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{image_b64}",
                        },
                    ],
                }
            ],
            temperature=0,
        )
        raw_text = _extract_response_text(response).strip()
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            default_layout.update(parsed)
    except Exception:
        pass

    default_layout["x_ratio"] = _clamp(float(default_layout.get("x_ratio", 0.5)), 0.1, 0.9)
    default_layout["y_ratio"] = _clamp(float(default_layout.get("y_ratio", 0.88)), 0.1, 0.95)
    default_layout["max_width_ratio"] = _clamp(
        float(default_layout.get("max_width_ratio", 0.82)), 0.4, 0.95
    )
    default_layout["font_size"] = int(_clamp(float(default_layout.get("font_size", 34)), 20, 64))
    default_layout["stroke_width"] = int(_clamp(float(default_layout.get("stroke_width", 2)), 0, 4))
    default_layout["font_style"] = str(default_layout.get("font_style", "regular"))
    default_layout["text_color"] = str(default_layout.get("text_color", "#FFFFFF"))
    default_layout["stroke_color"] = str(default_layout.get("stroke_color", "#111111"))
    align = str(default_layout.get("align", "center")).lower()
    default_layout["align"] = align if align in ("left", "center", "right") else "center"
    return default_layout


def _overlay_story_text(
    image_bytes: bytes, story_text: str, visual_description: str, client: OpenAI
) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(image)

    width, height = image.size
    min_dim = min(width, height)
    padding = max(8, int(min_dim * 0.03))

    layout = _recommend_text_layout(
        client=client,
        image_bytes=image_bytes,
        story_text=story_text,
        visual_description=visual_description,
    )

    # 해상도에 비례해 폰트/외곽선을 자동 스케일링
    scale_ratio = min_dim / 1024.0
    scaled_font_size = int(layout["font_size"] * scale_ratio)
    scaled_font_size = int(_clamp(scaled_font_size, 12, max(22, int(min_dim * 0.09))))
    scaled_stroke_width = int(
        _clamp(
            layout["stroke_width"] * (min_dim / 512.0),
            0,
            max(1, int(min_dim * 0.01)),
        )
    )

    # 텍스트 영역/줄 수를 해상도에 맞춰 자동 제한
    text_area_width = int(width * layout["max_width_ratio"])
    text_area_width = int(_clamp(text_area_width, width * 0.5, width - (padding * 2)))
    max_lines = int(_clamp(int(height / 85), 2, 5))

    font = _load_korean_font(size=scaled_font_size, font_style=layout["font_style"])
    lines = _wrap_text(draw, story_text, font, text_area_width)
    lines = lines[:max_lines]

    line_height = int(max(14, scaled_font_size * 1.35))
    total_text_height = max(line_height * len(lines), line_height)

    # 세로 공간 초과 시 폰트를 단계적으로 줄여 맞춘다.
    max_text_height = int(height * 0.42)
    while total_text_height > max_text_height and scaled_font_size > 10:
        scaled_font_size -= 1
        line_height = int(max(12, scaled_font_size * 1.35))
        font = _load_korean_font(size=scaled_font_size, font_style=layout["font_style"])
        lines = _wrap_text(draw, story_text, font, text_area_width)[:max_lines]
        total_text_height = max(line_height * len(lines), line_height)

    # 텍스트 블록의 실제 크기 추정
    max_line_width = 0
    for line in lines:
        line_width = draw.textbbox((0, 0), line, font=font)[2]
        if line_width > max_line_width:
            max_line_width = line_width
    block_width = max(1, max_line_width)
    block_height = max(1, total_text_height)

    preferred_center = (
        int(width * layout["x_ratio"]),
        int(height * layout["y_ratio"]),
    )

    def _find_best_position_by_blank_area() -> tuple[int, int]:
        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)

        def _score_box(left: int, top: int) -> float:
            right = left + block_width
            bottom = top + block_height
            crop_gray = gray.crop((left, top, right, bottom))
            crop_edges = edges.crop((left, top, right, bottom))

            stat_gray = ImageStat.Stat(crop_gray)
            stat_edges = ImageStat.Stat(crop_edges)

            # 복잡도(에지 + 밝기 분산)가 낮을수록 텍스트 배치에 유리
            edge_mean = stat_edges.mean[0] if stat_edges.mean else 0.0
            gray_std = stat_gray.stddev[0] if stat_gray.stddev else 0.0

            # 화면 중앙 부근을 약간 선호
            cx = left + (block_width // 2)
            cy = top + (block_height // 2)
            dist_center = (
                abs(cx - width / 2) / max(1.0, width / 2)
                + abs(cy - height / 2) / max(1.0, height / 2)
            )
            return (edge_mean * 0.75) + (gray_std * 0.25) + (dist_center * 2.0)

        # 전역 후보 + 모델 추천 중심 후보를 함께 평가
        x_candidates = [
            padding,
            int((width - block_width) * 0.25),
            int((width - block_width) * 0.5),
            int((width - block_width) * 0.75),
            width - block_width - padding,
        ]
        y_candidates = [
            padding,
            int((height - block_height) * 0.2),
            int((height - block_height) * 0.4),
            int((height - block_height) * 0.6),
            int((height - block_height) * 0.8),
            height - block_height - padding,
        ]

        pref_left = int(preferred_center[0] - block_width / 2)
        pref_top = int(preferred_center[1] - block_height / 2)
        x_candidates.extend([pref_left - 20, pref_left, pref_left + 20])
        y_candidates.extend([pref_top - 20, pref_top, pref_top + 20])

        best_score = float("inf")
        best_pos = (padding, padding)

        for left in x_candidates:
            for top in y_candidates:
                clamped_left = int(_clamp(left, padding, width - block_width - padding))
                clamped_top = int(_clamp(top, padding, height - block_height - padding))
                score = _score_box(clamped_left, clamped_top)
                if score < best_score:
                    best_score = score
                    best_pos = (clamped_left, clamped_top)

        return best_pos

    x_start, y_start = _find_best_position_by_blank_area()

    # 배치된 영역 평균 밝기를 기준으로 글자색 자동 선택
    gray = image.convert("L")
    region = gray.crop(
        (x_start, y_start, x_start + block_width, y_start + block_height)
    )
    region_mean = ImageStat.Stat(region).mean[0] if ImageStat.Stat(region).mean else 128
    if region_mean >= 145:
        fill = (20, 20, 20, 255)
        stroke_fill = (245, 245, 245, 255)
    else:
        fill = (255, 255, 255, 255)
        stroke_fill = (20, 20, 20, 255)
    stroke_width = scaled_stroke_width

    align = layout["align"]
    for idx, line in enumerate(lines):
        line_width = draw.textbbox((0, 0), line, font=font)[2]
        if align == "left":
            x = x_start
        elif align == "right":
            x = x_start + block_width - line_width
        else:
            x = x_start + int((block_width - line_width) / 2)
        y = y_start + idx * line_height
        x = max(padding, min(width - line_width - padding, x))
        y = max(padding, min(height - line_height - padding, y))
        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG")
    return output.getvalue()


async def generate_image_for_page(page_number: int, tool_context: ToolContext):
    """지정된 페이지의 일러스트 이미지를 생성합니다.

    Args:
        page_number: 생성할 페이지 번호 (1-5)
    """
    story_data = tool_context.state.get("story_data")

    if not story_data:
        return {
            "status": "error",
            "message": "State에 story_data가 없습니다. StoryWriterAgent가 먼저 실행되어야 합니다.",
        }

    if not isinstance(story_data, dict):
        try:
            story_data = json.loads(story_data)
        except Exception:
            try:
                story_data = story_data.model_dump()
            except Exception:
                return {"status": "error", "message": "story_data 형식을 해석할 수 없습니다."}

    pages = story_data.get("pages", [])
    page = next((p for p in pages if p.get("page_number") == page_number), None)

    if not page:
        return {"status": "error", "message": f"{page_number}페이지를 찾을 수 없습니다."}

    text = page.get("text", "")
    visual_description = page.get("visual_description", "")
    run_id_raw = tool_context.state.get("current_run_id") or tool_context.invocation_id
    run_id = _sanitize_run_id(str(run_id_raw))
    filename = f"page_{page_number}_{run_id}.png"

    image_prompt = (
        "Children's storybook illustration, warm and cute watercolor style. "
        f"Scene description: {visual_description}. "
        "The style should be gentle, colorful, and suitable for young children aged 4-8. "
        "Keep enough visual space at the bottom for story caption text."
    )

    client = OpenAI()

    try:
        image = client.images.generate(
            model="dall-e-2",
            prompt=image_prompt,
            n=1,
            size="256x256",
            response_format="b64_json",
        )
        image_bytes = base64.b64decode(image.data[0].b64_json)
        image_bytes = _overlay_story_text(
            image_bytes=image_bytes,
            story_text=text,
            visual_description=visual_description,
            client=client,
        )
    except Exception as e:
        return {
            "page_number": page_number,
            "text": text,
            "visual_description": visual_description,
            "filename": filename,
            "status": "error",
            "error": str(e),
        }

    artifact = types.Part(
        inline_data=types.Blob(
            mime_type="image/png",
            data=image_bytes,
        )
    )

    await tool_context.save_artifact(filename=filename, artifact=artifact)

    tool_context.state[f"image_page_{page_number}"] = {
        "filename": filename,
        "run_id": run_id,
        "status": "completed",
    }

    return {
        "page_number": page_number,
        "text": text,
        "visual_description": visual_description,
        "filename": filename,
        "status": "completed",
    }
