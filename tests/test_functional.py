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

if __name__ == '__main__':
    unittest.main()
