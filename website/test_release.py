"""Admission doubles and real subprocess regressions; no real signature claims."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import release


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tag = "core-v0.47.0"
        self.digest = "d" * 64
        self.source = {"commit": "a" * 40, "tree": "b" * 40}
        self.manifest = {"source": self.source, "candidate_id": "c" * 64,
                         "qualification_sha256": "e" * 64, "recipe_sha256": "f" * 64}
        self.run = {"id": 123, "run_attempt": 1, "repository": {"id": release.REPOSITORY_ID,
                    "full_name": release.REPOSITORY}, "head_repository": {"id": release.REPOSITORY_ID},
                    "head_sha": self.source["commit"], "head_branch": self.tag,
                    "path": release.WORKFLOW, "event": "workflow_dispatch", "status": "in_progress",
                    "conclusion": None}
        self.result = {"verificationResult": {
            "statement": {"subject": [{"digest": {"sha256": self.digest}}],
                          "predicateType": release.PREDICATE,
                          "predicate": {"format": "gripsack.local-qualification.v1", "policy": release.POLICY,
                                        **self.manifest, "builder": "local", "hosted_build": False}},
            "signature": {"certificate": {
                "runInvocationURI": f"https://github.com/{release.REPOSITORY}/actions/runs/123/attempts/1",
                "sourceRepositoryIdentifier": str(release.REPOSITORY_ID),
                "buildTrigger": "workflow_dispatch"}}}}

    def test_selectors_require_all_explicit_identities(self):
        self.assertEqual(release.selectors(self.tag, self.digest, "123"), (self.tag, self.digest, 123))
        for tag, digest, run_id in [("latest", self.digest, 123), (self.tag, "", 123),
                                    (self.tag, self.digest, True), (self.tag, self.digest, "0123"),
                                    (self.tag, self.digest, "１２３"), (self.tag, self.digest, "123;echo bad")]:
            with self.subTest(tag=tag, digest=digest, run_id=run_id), self.assertRaises(ValueError):
                release.selectors(tag, digest, run_id)

    def test_signing_run_id_signed_64_bit_boundary(self):
        maximum = (1 << 63) - 1
        for value in (maximum, str(maximum)):
            self.assertEqual(release.selectors(self.tag, self.digest, value)[2], maximum)
        for value in (0, -1, 1 << 63, str(1 << 63), "9" * 100, "+1", "1.0", 1.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                release.selectors(self.tag, self.digest, value)

    def test_partial_input_never_falls_back(self):
        args = argparse.Namespace(release_tag=self.tag, manifest_sha256=None, run_id=None)
        with patch.object(release, "download") as fetch, self.assertRaises(ValueError):
            release.selected_inputs(args)
        fetch.assert_not_called()

    def test_no_inputs_read_only_deployed_selection(self):
        binding = {"format": "gripsack.site-release.v1", "repository": release.REPOSITORY,
                   "source": self.source, "candidate_id": "c" * 64, "manifest_sha256": self.digest,
                   "tag": self.tag, "run_id": 123, "release_id": 456, "version": "0.47.0"}
        args = argparse.Namespace(release_tag=None, manifest_sha256=None, run_id=None)
        with patch.object(release, "download", return_value=json.dumps(binding).encode()) as fetch:
            self.assertEqual(release.selected_inputs(args), (self.tag, self.digest, 123))
        fetch.assert_called_once_with("https://gripsack.dev/release.json")
        with patch.object(release, "download", return_value=b"{}"), self.assertRaises(ValueError):
            release.selected_inputs(args)

    def test_signed_run_and_subject_must_match_same_verified_result(self):
        release.verify_results([self.result], self.manifest, self.digest, self.run, self.tag)
        for key, value in [("runInvocationURI", f"https://github.com/{release.REPOSITORY}/actions/runs/124/attempts/1"),
                           ("runInvocationURI", f"https://github.com/{release.REPOSITORY}/actions/runs/123/attempts/2"),
                           ("sourceRepositoryIdentifier", "1"), ("buildTrigger", "push")]:
            result = copy.deepcopy(self.result)
            result["verificationResult"]["signature"]["certificate"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                release.verify_results([result], self.manifest, self.digest, self.run, self.tag)
        result = copy.deepcopy(self.result)
        result["verificationResult"]["statement"]["subject"][0]["digest"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            release.verify_results([result], self.manifest, self.digest, self.run, self.tag)
        result = copy.deepcopy(self.result)
        result["verificationResult"]["statement"]["predicate"]["hosted_build"] = True
        with self.assertRaises(ValueError):
            release.verify_results([result], self.manifest, self.digest, self.run, self.tag)

    def test_both_bundle_and_repository_attestations_are_required(self):
        outputs = [b"gh version 2.102.0 (2026-10-22)", json.dumps([self.result]).encode(), b"[]"]
        with patch.object(release, "command", side_effect=outputs) as commands, self.assertRaises(ValueError):
            release.verify(Path("manifest"), Path("bundle"), self.manifest, self.digest, self.run, self.tag)
        bundle_args = commands.call_args_list[1].args[0]
        association_args = commands.call_args_list[2].args[0]
        self.assertEqual(bundle_args[-2:], ["--bundle", "bundle"])
        self.assertNotIn("--bundle", association_args)
        for flag in ("--cert-identity", "--cert-oidc-issuer", "--source-ref", "--source-digest",
                     "--signer-digest", "--deny-self-hosted-runners", "--predicate-type"):
            self.assertIn(flag, association_args)

    def test_old_verifier_is_rejected(self):
        with patch.object(release, "command", return_value=b"gh version 2.101.0"), self.assertRaises(ValueError):
            release.verify(Path("manifest"), Path("bundle"), self.manifest, self.digest, self.run, self.tag)

    def test_in_progress_run_is_allowed_without_completion_cycle(self):
        with patch.object(release, "api", return_value=self.run):
            self.assertEqual(release.signing_run(123, self.tag, self.source), self.run)
        for field, value in [("head_sha", "0" * 40), ("event", "push"), ("head_branch", "main"),
                             ("path", ".github/workflows/other.yml"), ("conclusion", "failure")]:
            run = dict(self.run, **{field: value})
            with self.subTest(field=field), patch.object(release, "api", return_value=run), self.assertRaises(ValueError):
                release.signing_run(123, self.tag, self.source)
        successful = dict(self.run, status="completed", conclusion="success")
        with patch.object(release, "api", return_value=successful):
            release.signing_run(123, self.tag, self.source)

    def test_nominated_digest_is_checked_before_verifier(self):
        with patch.object(release, "published_release", return_value={"id": 456}), \
                patch.object(release, "download", return_value=b"{}"), \
                patch.object(release, "verify") as verify, self.assertRaises(ValueError):
            release.admit(self.tag, self.digest, 123)
        verify.assert_not_called()

    def test_exact_binding_and_source_files_from_admitted_manifest(self):
        manifest = dict(self.manifest, format="gripsack.release.v1", repository=release.REPOSITORY,
                        policy=release.POLICY, platform="linux-x86_64", provenance={"builder": "local", "hosted_build": False},
                        compatible={"core": "0.47.0"}, signer={"workflow": release.WORKFLOW, "ref": f"refs/tags/{self.tag}"},
                        artifacts=[{"path": "artifacts/grip.tar.gz"}])
        data = json.dumps(manifest).encode()
        digest = hashlib.sha256(data).hexdigest()
        names = ["grip.tar.gz", "gripsack-release-0.47.0.json", "gripsack-release-0.47.0.json.sigstore.json"]
        files = {"install.sh": b"source installer", "CHANGELOG.md": b"# source changelog"}
        with patch.object(release, "published_release", return_value={"id": 456}), \
                patch.object(release, "download", side_effect=[data, b"behavioral signature double"]), \
                patch.object(release, "tag_source", return_value=self.source), \
                patch.object(release, "signing_run", return_value=self.run), \
                patch.object(release, "api", return_value=[{"name": name} for name in names]), \
                patch.object(release, "verify") as verify, \
                patch.object(release, "source_files", return_value=files):
            binding, actual_files = release.admit(self.tag, digest, 123)
        self.assertEqual(set(binding), release.BINDING_FIELDS)
        self.assertEqual(binding, {"format": "gripsack.site-release.v1", "repository": release.REPOSITORY,
                                  "source": self.source, "candidate_id": manifest["candidate_id"],
                                  "manifest_sha256": digest, "tag": self.tag, "run_id": 123,
                                  "release_id": 456, "version": "0.47.0"})
        self.assertEqual(actual_files, files)
        verify.assert_called_once()

    def test_source_blob_bytes_are_checked(self):
        data = b"source file"
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        tree = {"sha": self.source["tree"], "truncated": False,
                "tree": [{"path": name, "type": "blob", "mode": "100644", "sha": blob}
                         for name in ("install.sh", "CHANGELOG.md")]}
        with patch.object(release, "api", return_value=tree), patch.object(release, "download", return_value=data):
            self.assertEqual(release.source_files(self.source)["install.sh"], data)
        with patch.object(release, "api", return_value=tree), patch.object(release, "download", return_value=b"foreign"), \
                self.assertRaises(ValueError):
            release.source_files(self.source)

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            release.decode(b'{"tag":"one","tag":"two"}')


class CommandTests(unittest.TestCase):
    """Execute actual local Python children, never a mock command runner."""

    def assert_reaped(self, pid):
        with self.assertRaises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)

    def failing_child(self, body, exception, *, timeout=5, maximum=1024):
        with tempfile.TemporaryDirectory() as directory:
            identity = Path(directory) / "pid"
            code = ("import os, sys, time\nfrom pathlib import Path\n"
                    "Path(sys.argv[1]).write_text(str(os.getpid()))\n" + body)
            with self.assertRaises(exception):
                release.command([sys.executable, "-c", code, str(identity)],
                                timeout=timeout, maximum=maximum)
            self.assert_reaped(int(identity.read_text()))

    def test_stdout_and_stderr_floods_are_stopped_and_reaped(self):
        for descriptor in (1, 2):
            with self.subTest(descriptor=descriptor):
                self.failing_child(
                    f"while True:\n    os.write({descriptor}, b'x' * 4096)\n", ValueError)

    def test_output_bound_is_combined_across_streams(self):
        self.failing_child(
            "os.write(1, b'x' * 600)\nos.write(2, b'y' * 600)\ntime.sleep(60)\n",
            ValueError)

    def test_exact_output_bound_and_both_pipes_are_drained(self):
        # More than pipe capacity on stderr first catches sequential draining.
        size = 128 * 1024
        code = f"import os\nos.write(2, b'e' * {size})\nos.write(1, b'o' * {size})\n"
        result = release.command([sys.executable, "-c", code], timeout=5, maximum=2 * size)
        self.assertEqual(result, b"o" * size)

    def test_silent_child_deadline_kills_and_reaps(self):
        self.failing_child("time.sleep(60)\n", TimeoutError, timeout=1)

    def test_closed_pipes_do_not_bypass_execution_deadline(self):
        self.failing_child("os.close(1)\nos.close(2)\ntime.sleep(60)\n",
                           subprocess.TimeoutExpired, timeout=1)

    def test_exited_leader_with_live_descendant_keeps_group_owned(self):
        with tempfile.TemporaryDirectory() as directory:
            identity = Path(directory) / "pids"
            # The descendant holds both pipes after the leader exits. The
            # command must not reap the leader before killing the owned group.
            code = ("import os, sys, time\nfrom pathlib import Path\n"
                    "leader = os.getpid()\nchild = os.fork()\n"
                    "if child == 0:\n    time.sleep(60)\n    os._exit(0)\n"
                    "Path(sys.argv[1]).write_text(f'{leader} {child}')\nos._exit(0)\n")
            with self.assertRaises(TimeoutError):
                release.command([sys.executable, "-c", code, str(identity)], timeout=1)
            leader, child = map(int, identity.read_text().split())
            self.assert_reaped(leader)
            try:
                descriptor = os.pidfd_open(child)
            except ProcessLookupError:
                return
            try:
                # pidfd readiness also handles a terminated orphan awaiting
                # init's reaping; no kill/probe against a potentially reused PID.
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                self.assertTrue(poller.poll(5000), "descendant survived owned-group termination")
            finally:
                os.close(descriptor)

    def test_no_group_signal_after_reaped_success_or_failure(self):
        for status in (0, 7):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                identity = Path(directory) / "pid"
                code = ("import os, sys\nfrom pathlib import Path\n"
                        "Path(sys.argv[1]).write_text(str(os.getpid()))\n"
                        f"os.write(2, b'expected diagnostic')\nsys.exit({status})\n")
                # Only the forbidden signal boundary is guarded. The process,
                # output, exit and wait/reap are all real.
                with patch.object(release.os, "killpg",
                                  side_effect=AssertionError("signalled a reaped process group")):
                    if status:
                        with self.assertRaisesRegex(ValueError, "expected diagnostic"):
                            release.command([sys.executable, "-c", code, str(identity)])
                    else:
                        self.assertEqual(release.command([sys.executable, "-c", code, str(identity)]), b"")
                self.assert_reaped(int(identity.read_text()))


if __name__ == "__main__":
    unittest.main()
