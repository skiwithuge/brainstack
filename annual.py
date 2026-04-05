# annual.py
import sys
import logging
from src.llm.annual_service import run_annual_summarizer

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    run_annual_summarizer(target_date)
