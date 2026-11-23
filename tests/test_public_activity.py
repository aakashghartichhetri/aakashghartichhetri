from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import unittest
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'update_public_activity.py'
spec = importlib.util.spec_from_file_location('profile_activity', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ActivityTests(unittest.TestCase):
    def test_renders_actual_fields_and_valid_xml(self):
        u = {'public_repos': 8}
        e = [{'type':'PushEvent','repo':{'name':'example/repo'},'created_at':'2026-11-22T21:00:00Z','payload':{}}]
        xml = module.render_svg(u,e,datetime(2026,11,22,tzinfo=timezone.utc))
        ET.fromstring(xml)
        self.assertIn('Pushed changes',xml)
        self.assertIn('example/repo',xml)
        self.assertIn('22 Nov 2026',xml)
        self.assertIn('>8<',xml)
    def test_escapes_untrusted_metadata(self):
        e = [{'type':'IssuesEvent','repo':{'name':'org/repo<&foo'},'payload':{'action':'opened'},'created_at':'2026-11-21T11:00:00Z'}]
        xml = module.render_svg({'public_repos':1},e,datetime.now(timezone.utc))
        ET.fromstring(xml)
        self.assertIn('&lt;&amp;',xml)
        self.assertNotIn('org/repo<&',xml)
    def test_empty_events_are_not_faked(self):
        xml = module.render_svg({'public_repos':0}, [], datetime.now(timezone.utc))
        self.assertIn('No recent public activity available',xml)
    def test_missing_repo_count_rejected(self):
        with self.assertRaises(ValueError):
            module.render_svg({'public_repos':'many'}, [],datetime.now(timezone.utc))
    def test_long_text_truncated(self):
        self.assertLessEqual(len(module.one_line('A'*200)), 62)

if __name__ == '__main__':
    unittest.main()
