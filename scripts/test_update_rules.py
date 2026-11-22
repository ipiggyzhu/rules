import contextlib
import io
import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

import converter


class RuleUpdateTests(unittest.TestCase):
    def test_identical_update_preserves_files_and_same_size_edit_is_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = Path(tmp, "ads.list")
            report = Path(tmp, "stats.json")
            with patch.object(converter, "STATS_FILE", report):
                def generate(host):
                    with patch.object(converter, "stats", converter.Stats()) as stats:
                        converter.write_rules(rules.as_posix(), ["DOMAIN," + host], "Test")
                        stats.save()
                generate("old.example")
                old_list = rules.read_bytes()
                old_stats = json.loads(report.read_text())
                old_stats["timestamp"] = "2000-01-01T00:00:00+00:00"
                report.write_text(json.dumps(old_stats))
                for path in (rules, report):
                    os.utime(path, (1000, 1000))
                generate("old.example")
                self.assertEqual([p.stat().st_mtime for p in (rules, report)], [1000, 1000])
                self.assertEqual(rules.read_bytes(), old_list)
                generate("new.example")
                self.assertIn("DOMAIN,new.example", rules.read_text())
                self.assertNotEqual(json.loads(report.read_text())["timestamp"], old_stats["timestamp"])

    def test_whitelist_protects_hosts_before_deduplication(self):
        whitelist = {"szlong.weixin.qq.com", "apikey.map.qq.com"}
        ads = {
            "HOST-SUFFIX,weixin.qq.com",
            "DOMAIN,szlong.weixin.qq.com",
            "HOST-KEYWORD,szlong.weixin",
            "DOMAIN-SUFFIX,apikey.map.qq.com",
            "HOST,child.apikey.map.qq.com",
            "DOMAIN,weixin.qq.com",
            "DOMAIN-SUFFIX,ad.weixin.qq.com",
            "DOMAIN,notapikey.map.qq.com",
        }
        filtered = converter.filter_by_whitelist(ads, whitelist)
        self.assertEqual(filtered, {
            "DOMAIN,weixin.qq.com",
            "DOMAIN-SUFFIX,ad.weixin.qq.com",
            "DOMAIN,notapikey.map.qq.com",
        })
        for formatter in (converter.format_for_loon, converter.format_for_quantumultx):
            self.assertEqual(len(formatter(filtered)), 3)

    def test_failed_update_preserves_all_lists_then_recovers(self):
        script = Path(converter.__file__).resolve()
        outputs = [converter.LOON_AD_OUTPUT, converter.LOON_DIRECT_OUTPUT,
                   converter.QUANTUMULTX_AD_OUTPUT, converter.QUANTUMULTX_DIRECT_OUTPUT,
                   converter.STATS_FILE]
        failed_url = converter.COMMON_AD_RULES_URLS[0]
        def fetch(url, timeout):
            if url == failed_url and isinstance(body, Exception):
                raise body
            response = requests.Response()
            response.status_code = 200
            response._content = (body if url == failed_url else "ads.example.org").encode()
            return response

        with tempfile.TemporaryDirectory() as tmp:
            previous = Path.cwd()
            os.chdir(tmp)
            try:
                for output in outputs:
                    Path(output).parent.mkdir(exist_ok=True)
                    Path(output).write_text("previous version")
                with patch.object(requests, "get", side_effect=fetch), patch("time.sleep"), \
                        patch.dict(os.environ, {"GITHUB_OUTPUT": ""}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    for body in (requests.ConnectionError("offline"), "# empty list",
                                 "<html>\nerror.example.org\n</html>"):
                        with self.assertRaises(SystemExit):
                            runpy.run_path(str(script), run_name="__main__")
                        self.assertEqual(Path("failed_sources.txt").read_text().splitlines(), [failed_url])
                        for output in outputs:
                            self.assertEqual(Path(output).read_text(), "previous version")
                    body = "recovered.example.org"
                    runpy.run_path(str(script), run_name="__main__")
                    self.assertEqual(Path("failed_sources.txt").read_text(), "")
                    for output in (converter.LOON_AD_OUTPUT, converter.QUANTUMULTX_AD_OUTPUT):
                        self.assertIn("SUFFIX,recovered.example.org\n", Path(output).read_text())
            finally:
                os.chdir(previous)
