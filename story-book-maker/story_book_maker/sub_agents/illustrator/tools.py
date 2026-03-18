import base64
import json

from google.genai import types
from openai import OpenAI
from google.adk.tools.tool_context import ToolContext


async def generate_page_image(tool_context: ToolContext):
    """State에 저장된 현재 페이지의 일러스트 이미지를 1장 생성합니다."""

    current_page = tool_context.state.get("current_page_data")

    if not current_page:
        return {"status": "error", "message": "current_page_data가 없습니다."}

    if isinstance(current_page, str):
        current_page = json.loads(current_page)

    page_number = current_page.get("page_number", 0)
    text = current_page.get("text", "")
    visual_description = current_page.get("visual_description", "")
    filename = f"page_{page_number}.png"

    existing_artifacts = await tool_context.list_artifacts()
    if filename in existing_artifacts:
        return {
            "page_number": page_number,
            "text": text,
            "visual_description": visual_description,
            "filename": filename,
            "status": "already_exists",
        }

    image_prompt = (
        "Children's storybook illustration, warm and cute watercolor style. "
        f"Scene description: {visual_description}. "
        "The style should be gentle, colorful, and suitable for young children aged 4-8."
    )

    client = OpenAI()

    try:
        image = client.images.generate(
            model="gpt-image-1",
            prompt=image_prompt,
            n=1,
            size="1024x1024",
        )
        image_bytes = base64.b64decode(image.data[0].b64_json)
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

    return {
        "page_number": page_number,
        "text": text,
        "visual_description": visual_description,
        "filename": filename,
        "status": "completed",
    }
