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
        
        filepath = os.path.join(folder, "raw", filename)
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
        import tempfile
        
        original_lang = src.core.config.APP_LANGUAGE
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Test English parsing
                src.core.config.APP_LANGUAGE = "en"
                hen = LOCALES["en"]["headers"]
                raw_en = f"## {hen[0]}\nA\n## {hen[1]}\nB\n## {hen[2]}\nC\n## {hen[3]}\nD"
                res_en = split_and_save_briefing(raw_en, tmpdir, "TESTDATE_EN")
                self.assertEqual(len(res_en), 4)

                # Test Italian parsing
                src.core.config.APP_LANGUAGE = "it"
                hit = LOCALES["it"]["headers"]
                raw_it = f"## {hit[0]}\nA\n## {hit[1]}\nB\n## {hit[2]}\nC\n## {hit[3]}\nD"
                res_it = split_and_save_briefing(raw_it, tmpdir, "TESTDATE_IT")
                self.assertEqual(len(res_it), 4)
        finally:
            src.core.config.APP_LANGUAGE = original_lang

    def test_parser_failsafe(self):
        from src.llm.parser import split_and_save_briefing
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_text = "Missing all the headers! Uh oh!"
            res = split_and_save_briefing(raw_text, tmpdir, "TESTDATE")
            self.assertEqual(len(res), 1)


class TestWikiService(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        # Patch MEMORY_DIR to point to our temp directory
        import src.core.config as cfg
        self._orig_memory_dir = cfg.MEMORY_DIR
        cfg.MEMORY_DIR = self.tmpdir
        import src.llm.wiki_service as ws
        ws.MEMORY_DIR = self.tmpdir

    def tearDown(self):
        import src.core.config as cfg
        import src.llm.wiki_service as ws
        cfg.MEMORY_DIR = self._orig_memory_dir
        ws.MEMORY_DIR = self._orig_memory_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_wiki_init(self):
        """Asserts all 4 core wiki pages are created when memory dir is empty."""
        from src.llm.wiki_service import init_memory
        init_memory()
        for page in ("index.md", "goals.md", "patterns.md", "open_loops.md", "log.md"):
            self.assertTrue(os.path.exists(os.path.join(self.tmpdir, page)),
                            f"Missing wiki page: {page}")

    def test_wiki_init_idempotent(self):
        """Calling init_memory twice must not overwrite existing pages."""
        from src.llm.wiki_service import init_memory
        init_memory()
        page_path = os.path.join(self.tmpdir, "goals.md")
        with open(page_path, "w") as f:
            f.write("CUSTOM CONTENT")
        init_memory()
        with open(page_path) as f:
            self.assertEqual(f.read(), "CUSTOM CONTENT")

    def test_stale_loop_detection(self):
        """Asserts stale loop detection only flags items older than threshold."""
        import src.llm.wiki_service as ws
        from datetime import datetime, timedelta
        
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        new_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        content = (
            "---\nlast_updated: 2026-01-01\n---\n\n# Open Loops\n\n"
            f"- [{old_date}] Buy milk\n"
            f"- [{new_date}] Call dentist\n"
            f"- [CLOSED {new_date}] ~~Old closed item~~\n"
        )
        with open(os.path.join(self.tmpdir, "open_loops.md"), "w") as f:
            f.write(content)

        stale = ws.get_stale_loops(threshold_days=7)
        self.assertEqual(len(stale), 1)
        self.assertIn("Buy milk", stale[0])

    def test_wiki_guard(self):
        """Asserts update is aborted when LLM response is suspiciously short."""
        import src.llm.wiki_service as ws
        
        original_content = "x" * 1000
        short_response = "x" * 100  # < 50% of original

        page_path = os.path.join(self.tmpdir, "goals.md")
        with open(page_path, "w") as f:
            f.write(original_content)

        result = ws._write_page("goals.md", short_response, original_content)
        self.assertFalse(result)

        # File should be unchanged
        with open(page_path) as f:
            self.assertEqual(f.read(), original_content)


class TestWebAuth(unittest.TestCase):
    def setUp(self):
        from src.web.server import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_unauthenticated_redirects(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers.get("location"), "/login")

    def test_login_page_renders(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Brainstack", response.text)
        self.assertIn("form", response.text.lower())

    def test_failed_login(self):
        response = self.client.post("/login", data={"username": "wrong", "password": "pwd"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid", response.text)

    def test_successful_login(self):
        import src.core.config
        response = self.client.post("/login", data={"username": "admin", "password": src.core.config.WEB_PASSWORD}, follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn("session_id", response.cookies)

if __name__ == '__main__':
    unittest.main()

