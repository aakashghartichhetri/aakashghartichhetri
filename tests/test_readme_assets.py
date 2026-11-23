from pathlib import Path
import unittest
import re

ROOT=Path(__file__).resolve().parents[1]
README=(ROOT/'README.md').read_text(encoding='utf-8')

class ProfileIntegrity(unittest.TestCase):
    def test_relative_image_assets_exist(self):
        references = re.findall(r'(?:src|srcset)="(\./assets/[^\"]+)"', README)
        self.assertGreaterEqual(len(references), 4)
        for asset in references:
            with self.subTest(asset=asset):
                self.assertTrue((ROOT / asset[2:]).is_file())

    def test_featured_repositories_are_linked(self):
        for repo in ('resurrection','echo','event-horizon','omega','Translify','Accessibility-Copilot-Team11-CTP-Hackathon'):
            with self.subTest(repo=repo):
                self.assertIn(f'https://github.com/aakashghartichhetri/{repo}',README)

    def test_reduced_motion_fallback(self):
        self.assertIn('(prefers-reduced-motion: reduce)', README)

    def test_profile_actions_workflow_present(self):
        self.assertTrue((ROOT/'.github/workflows/profile-dynamics.yml').is_file())

if __name__=='__main__': unittest.main()
