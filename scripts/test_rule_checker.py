import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import dns.message
import dns.name
import dns.rcode
import dns.resolver
import dns.rrset

from scripts import rule_checker


class RuleCheckerTests(unittest.TestCase):
    def test_only_nxdomain_for_the_original_host_is_removable(self):
        resolver = Mock()
        host = "missing.example"
        qname = dns.name.from_text(host)
        response = dns.message.make_response(dns.message.make_query(qname, "A"))
        response.set_rcode(dns.rcode.NXDOMAIN)
        response.authority.append(dns.rrset.from_text(
            "example.", 60, "IN", "SOA", "ns.example. admin.example. 1 2 3 4 5"))
        resolver.resolve.side_effect = dns.resolver.NXDOMAIN(
            qnames=[qname], responses={qname: response})
        self.assertTrue(rule_checker.is_nonexistent(host, resolver))
        response.answer.append(dns.rrset.from_text(host + ".", 60, "IN", "CNAME", "target.example."))
        self.assertFalse(rule_checker.is_nonexistent(host, resolver))
        for outcome in (dns.resolver.LifetimeTimeout(), dns.resolver.NoNameservers(), None):
            resolver.resolve.side_effect = outcome
            self.assertFalse(rule_checker.is_nonexistent(host, resolver))
        resolver.resolve.assert_called_with(qname, "A", search=False, raise_on_no_answer=False,
                                            lifetime=rule_checker.TIMEOUT)

    def test_clean_preserves_original_rules_and_layout(self):
        keep = b"# comment\r\nHOST-SUFFIX,alive.example\r\n\r\nIP-CIDR,1.2.3.0/24\r\n1.2.3.4"
        rows = b".missing.example\r\nHOST-SUFFIX,missing.example\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "blacklist")
            path.write_bytes(rows + keep)
            with patch.object(rule_checker.dns.resolver, "Resolver"), \
                    patch.object(rule_checker, "is_nonexistent",
                                 side_effect=lambda host, resolver: host == "missing.example") as probe:
                self.assertEqual(rule_checker.check_blacklist(path, False), 0)
                self.assertEqual(path.read_bytes(), rows + keep)
                probe.reset_mock()
                self.assertEqual(rule_checker.check_blacklist(path, True), 2)
                self.assertEqual(sorted(call.args[0] for call in probe.call_args_list),
                                 ["alive.example", "missing.example"])
            self.assertEqual(path.read_bytes(), keep)
