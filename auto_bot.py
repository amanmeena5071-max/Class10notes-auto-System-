import json
import os
from pathlib import Path
from datetime import datetime, timezone

NOTES_DIR = Path("notes")
QUEUE_FILE = Path("chapters.json")
MODEL = "gemini-2.5-flash"


def load_queue():
    with QUEUE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue):
    with QUEUE_FILE.open("w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def get_next_chapter(queue):
    for chapter in queue:
        if chapter["status"] == "pending":
            return chapter
    return None


def generate_notes(chapter):
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert CBSE Class 10 teacher.

Create comprehensive original study notes.

Subject: {chapter['subject']}
Chapter: {chapter['chapter']}
Teaching approach: {chapter['style']}

Requirements:
1. Use simple, student-friendly English.
2. Follow the current CBSE/NCERT syllabus.
3. Include all important chapter topics.
4. Explain definitions and concepts clearly.
5. Include examples, formulas and diagrams where relevant.
6. Include a chapter summary.
7. Include 5 question-answer pairs.
8. Include 10 MCQs with correct answers.
9. Include 3 relevant PYQ-style questions.
10. Never invent official previous-year questions.
11. Do not imitate any named teacher's distinctive style.
12. Use original explanations.

Return a complete, clean HTML document.
Use CSS for attractive, mobile-friendly formatting.
Do not use Markdown code fences.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    result = response.text

    if not result or "<html" not in result.lower():
        raise RuntimeError("AI did not return valid HTML")

    return result


def main():
    queue = load_queue()
    chapter = get_next_chapter(queue)

    if chapter is None:
        print("All chapters completed!")
        return

    print("Generating:", chapter["chapter"])

    html = generate_notes(chapter)

    NOTES_DIR.mkdir(exist_ok=True)

    output_file = NOTES_DIR / f"{chapter['id']}.html"
    output_file.write_text(html, encoding="utf-8")

    chapter["status"] = "completed"
    chapter["completed_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    save_queue(queue)

    print("SUCCESS:", output_file)


if __name__ == "__main__":
    main()
