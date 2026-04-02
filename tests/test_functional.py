import unittest
import os
import shutil
from src.core.config import NOTES_DIR
from src.storage.notes import save_note, get_daily_folder

class TestFunctionalPipeline(unittest.TestCase):

    def test_save_note_pipeline(self):
        """
        Functionally tests the markdown saving procedure. 
        It asserts that directories and files are deterministically created as expected.
        """
        folder = get_daily_folder()
        self.assertTrue(os.path.exists(folder))
        
        content_str = "Agentic functional test note content"
        filename = save_note(content_str)
        
        self.assertTrue(filename.endswith("_note.md"))
        
        filepath = os.path.join(folder, filename)
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertEqual(content, content_str)
            
            
        # Clean up
        os.remove(filepath)

    def test_parser_success(self):
        from src.llm.parser import split_and_save_briefing
        from src.core.locales import LOCALES
        import src.core.config
        
        original_lang = src.core.config.APP_LANGUAGE
        
        try:
            # Test English parsing
            src.core.config.APP_LANGUAGE = "en"
            hen = LOCALES["en"]["headers"]
            raw_en = f"## {hen[0]}\nA\n## {hen[1]}\nB\n## {hen[2]}\nC\n## {hen[3]}\nD"
            res_en = split_and_save_briefing(raw_en, ".", "TESTDATE_EN")
            self.assertEqual(len(res_en), 4)
            for f in res_en:
                self.assertTrue(os.path.exists(f))
                os.remove(f)

            # Test Italian parsing
            src.core.config.APP_LANGUAGE = "it"
            hit = LOCALES["it"]["headers"]
            raw_it = f"## {hit[0]}\nA\n## {hit[1]}\nB\n## {hit[2]}\nC\n## {hit[3]}\nD"
            res_it = split_and_save_briefing(raw_it, ".", "TESTDATE_IT")
            self.assertEqual(len(res_it), 4)
            for f in res_it:
                self.assertTrue(os.path.exists(f))
                os.remove(f)
        finally:
            src.core.config.APP_LANGUAGE = original_lang

    def test_parser_failsafe(self):
        from src.llm.parser import split_and_save_briefing
        raw_text = "Missing all the headers! Uh oh!"
        res = split_and_save_briefing(raw_text, ".", "TESTDATE")
        self.assertEqual(len(res), 1)
        self.assertTrue(os.path.exists(res[0]))
        os.remove(res[0])

if __name__ == '__main__':
    unittest.main()
