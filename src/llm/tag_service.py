import os
import re
import glob
import logging
from google import genai

from src.core.config import GEMINI_API_KEY, NOTES_DIR
from src.core.locales import LOCALES
import src.core.config as _cfg

logger = logging.getLogger(__name__)


def extract_tags(text: str) -> list[str]:
    """Calls the LLM with a focused prompt to extract 3-5 tags from the given text.
    Returns an empty list on failure."""
    locale = LOCALES.get(_cfg.APP_LANGUAGE, LOCALES["en"])
    system_prompt = locale["memory_prompts"]["tags"]

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_cfg.LLM_MODEL,
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1
            )
        )
        raw = response.text.strip()
        tags = [t.strip().lower().replace(" ", "-") for t in raw.split(",") if t.strip()]
        # Sanitize: keep only alphanumeric and hyphens, max 10 tags
        tags = [re.sub(r"[^a-z0-9\-]", "", t) for t in tags if t]
        tags = [t for t in tags if t][:10]
        logger.info(f"Tag extraction returned: {tags}")
        return tags
    except Exception as e:
        logger.warning(f"Tag extraction failed (non-fatal): {e}")
        return []


def inject_tags(file_paths: list[str], tags: list[str]) -> None:
    """Injects tags into YAML frontmatter of each file."""
    if not tags:
        return

    tags_line = f"tags: [{', '.join(tags)}]"

    for fpath in file_paths:
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith("---"):
                # File has existing frontmatter — inject tags before closing ---
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    # Remove existing tags line if present
                    frontmatter = re.sub(r"\ntags:.*\n", "\n", frontmatter)
                    frontmatter = frontmatter.rstrip("\n") + f"\n{tags_line}\n"
                    content = f"---{frontmatter}---{parts[2]}"
            else:
                # No frontmatter — prepend one
                content = f"---\n{tags_line}\n---\n\n{content}"

            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.debug(f"Injected tags into {os.path.basename(fpath)}")
        except Exception as e:
            logger.warning(f"Failed to inject tags into {fpath}: {e}")


def _parse_frontmatter_tags(filepath: str) -> list[str]:
    """Extracts tags from a file's YAML frontmatter using simple regex."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(2048)  # Only need beginning of file

        if not content.startswith("---"):
            return []

        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            return []

        frontmatter = fm_match.group(1)
        tags_match = re.search(r"^tags:\s*\[([^\]]*)\]", frontmatter, re.MULTILINE)
        if not tags_match:
            return []

        raw_tags = tags_match.group(1)
        return [t.strip() for t in raw_tags.split(",") if t.strip()]
    except Exception:
        return []


def collect_tag_frequency(folder_paths: list[str]) -> dict[str, int]:
    """Scans a list of date folders for .md files and counts tag frequency."""
    freq: dict[str, int] = {}

    for folder in folder_paths:
        if not os.path.isdir(folder):
            continue
        for md_file in glob.glob(os.path.join(folder, "*.md")):
            tags = _parse_frontmatter_tags(md_file)
            for tag in tags:
                freq[tag] = freq.get(tag, 0) + 1

    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def collect_all_tags() -> dict[str, list[dict]]:
    """Scans all date folders in NOTES_DIR and builds a reverse index:
    {tag_name: [{date, filename, file_path}, ...]}
    Sorted by tag frequency (descending)."""
    index: dict[str, list[dict]] = {}

    if not os.path.exists(NOTES_DIR):
        return index

    for entry in sorted(os.listdir(NOTES_DIR), reverse=True):
        folder = os.path.join(NOTES_DIR, entry)
        if not (os.path.isdir(folder) and re.match(r"^\d{4}-\d{2}-\d{2}$", entry)):
            continue

        for md_file in glob.glob(os.path.join(folder, "*.md")):
            tags = _parse_frontmatter_tags(md_file)
            if not tags:
                continue

            fname = os.path.basename(md_file)
            for tag in tags:
                if tag not in index:
                    index[tag] = []
                index[tag].append({
                    "date": entry,
                    "filename": fname,
                    "file_path": f"{entry}/{fname}",
                })

    # Sort by number of artifacts (descending)
    return dict(sorted(index.items(), key=lambda x: len(x[1]), reverse=True))
