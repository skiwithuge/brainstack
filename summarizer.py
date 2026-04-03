# summarizer.py
import sys
import logging
from src.llm.summarizer_service import run_summarizer

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    run_summarizer(target_date)
