import os
import re
import logging

logger = logging.getLogger(__name__)

def split_and_save_briefing(raw_text: str, folder_path: str, date_str: str) -> list[str]:
    """
    Attempts to split the raw Gemini markdown into 4 distinct files based on predefined boundaries.
    Falls back to saving a single file if headers are missing or malformed by the LLM.
    Returns a list of saved filenames.
    """
    
    # Non-greedy search to safely grab content between strict markdown headers
    pattern = r"## 1\. Lineage(.*?)## 2\. Actions(.*?)## 3\. Creative Drafts(.*?)## 4\. Analyst Assessment(.*)"
    
    match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        logger.info("Parser successfully identified all 4 Second Brain headers.")
        
        lineage_content = match.group(1).strip()
        actions_content = match.group(2).strip()
        drafts_content = match.group(3).strip()
        analysis_content = match.group(4).strip()
        
        files_saved = []
        
        p1 = os.path.join(folder_path, f"{date_str}_lineage.md")
        with open(p1, "w", encoding="utf-8") as f:
            f.write("## 1. Lineage\n\n" + lineage_content)
        files_saved.append(p1)
            
        p2 = os.path.join(folder_path, f"{date_str}_actions.md")
        with open(p2, "w", encoding="utf-8") as f:
            f.write("## 2. Actions\n\n" + actions_content)
        files_saved.append(p2)
            
        p3 = os.path.join(folder_path, f"{date_str}_drafts.md")
        with open(p3, "w", encoding="utf-8") as f:
            f.write("## 3. Creative Drafts\n\n" + drafts_content)
        files_saved.append(p3)
            
        p4 = os.path.join(folder_path, f"{date_str}_analysis.md")
        with open(p4, "w", encoding="utf-8") as f:
            f.write("## 4. Analyst Assessment\n\n" + analysis_content)
        files_saved.append(p4)
            
        return files_saved
    else:
        logger.warning("Parser failed to find all 4 required headers. Executing fallback.")
        fallback_path = os.path.join(folder_path, f"{date_str}_Fallback_Briefing.md")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        return [fallback_path]
