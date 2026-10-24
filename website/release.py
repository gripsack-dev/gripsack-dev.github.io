"""Admit one published release before rendering; selectors are never authority.

No core/candidate Python is downloaded or executed. Trust is the reviewed site
code plus independently provisioned gh >= 2.102.0. This is publication admission,
not the later cross-surface consumer-completion verdict.

Core dispatch contract: repository_dispatch event_type=\"rebuild\", client_payload
with release_tag (stable core-vX.Y.Z), manifest_sha256 (64 lowercase hex), run_id
(canonical positive signed-64-bit JSON integer identifying the core signer).
All three are required.
The release must already be finalized and expose its manifest and Sigstore
bundle. The signing run may still be in_progress when it dispatches this site;
its signed certificate must bind that exact run and current attempt.
Verifier subprocess stdout/stderr share an enforced streaming byte bound and
deadline. Aborted commands terminate and reap their still-owned process group;
already reaped leaders are never signalled.

Pushes/manual runs with no selectors re-admit the live /release.json selection.
No existing binding (including the historical0.46 site) means no new artifact
or deployment, not a made-up selection or downgrade. Manual partial inputs and
repository dispatches missing any selector fail closed.

Local operator commands (use actual published identifiers and qualified files):
  uv run --with markdown python website/build.py --release-tag \"$TAG\" \\
    --manifest-sha256 \"$MANIFEST_SHA256\" --run-id \"$SIGNING_RUN_ID\"
  python3 -m unittest discover -s website -p 'test_release.py'
  python3 \"$CORE/scripts/check_examples.py\" --site \"$PWD\" --core-repo \"$CORE\" \\
    --grip \"$QUALIFIED_GRIP\" --sdk \"$QUALIFIED_SDK_TGZ\" --deno \"$DENO\" --selfcheck
CORE must be the selected exact source, with its matching qualified binary and
packed SDK; do not rebuild products in Pages or replace source-bound local gates.
For browser review: python3 -m http.server 8000 --directory public
Open /, /release.json and /docs/changelog.html. Check the versioned install/copy
commands and source-bound SDK links in /docs/{architecture,environments,
workspace-migration}.html. These commands are instructions, not success evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors as io_selectors
import signal
import subprocess
import tempfile
import time

REPOSITORY = "gripsack-dev/gripsack"
REPOSITORY_ID = 1342976637
API = f"https://api.github.com/repos/{REPOSITORY}"
WORKFLOW = ".github/workflows/release-core.yml"
POLICY = "LOCAL-QUALIFICATION-AUTHORITY-2026-10-23"
PREDICATE = "https://gripsack.dev/attestations/local-qualification/v1"
MAX_BYTES = 8 * 1024 * 1024
BINDING_FIELDS = {"format", "repository", "source", "candidate_id", "manifest_sha256",
                  "tag", "run_id", "release_id", "version"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(data):
    require(len(data) <= MAX_BYTES, "JSON exceeds bound")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda _: require(False, "nonfinite JSON"))


def command(args, *, timeout=330, maximum=MAX_BYTES):
    process = subprocess.Popen(
        args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True, env=dict(os.environ, GH_PROMPT_DISABLED="1", GH_PAGER="cat"),
    )
    selector = io_selectors.DefaultSelector()
    output, errors = bytearray(), bytearray()
    deadline = time.monotonic() + timeout
    try:
        selector.register(process.stdout, io_selectors.EVENT_READ, output)
        selector.register(process.stderr, io_selectors.EVENT_READ, errors)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"{args[0]} exceeded its verification deadline")
            for key, _ in selector.select(remaining):
                data = os.read(key.fileobj.fileno(), 65536)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                require(len(output) + len(errors) + len(data) <= maximum,
                        f"{args[0]} output exceeds verification bound")
                key.data.extend(data)
        process.wait(timeout=max(0.001, deadline - time.monotonic()))
        require(process.returncode == 0,
                f"{args[0]} failed: {errors[-4096:].decode('utf-8', errors='replace')}")
        return bytes(output)
    finally:
        selector.close()
        # Until wait() reaps it, the leader reserves this process-group ID.
        # Never poll/reap it while draining pipes, or signal after a known
        # terminal result: the PID/process-group ID could already be reused.
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        process.stdout.close()
        process.stderr.close()


def download(url):
    require(url.startswith("https://"), "HTTPS required")
    with tempfile.TemporaryDirectory(prefix="site-fetch-") as directory:
        path = Path(directory) / "body"
        command(["curl", "--fail", "--silent", "--show-error", "--location", "--proto", "=https",
                 "--proto-redir", "=https", "--max-time", "300", "--max-filesize", str(MAX_BYTES),
                 "--output", str(path), url])
        require(path.stat().st_size <= MAX_BYTES, "download exceeds bound")
        return path.read_bytes()


def api(path):
    return decode(download(f"{API}/{path}"))


def selectors(tag, digest, run_id):
    require(isinstance(tag, str) and re.fullmatch(r"core-v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag),
            "an explicit stable core release tag is required")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "manifest SHA256 is required")
    require(type(run_id) in (str, int) and re.fullmatch(r"[1-9][0-9]{0,18}", str(run_id))
            and int(run_id) <= (1 << 63) - 1, "canonical positive signed-64-bit signing run ID required")
    return tag, digest, int(run_id)


def selected_inputs(args):
    values = (args.release_tag, args.manifest_sha256, args.run_id)
    if any(value is not None for value in values):
        require(all(value is not None for value in values), "supply all three release selectors")
        return selectors(*values)
    # A rebuild re-admits the already deployed selection, never discovers latest.
    # Before the first signed release there is no binding: fail without deployment.
    current = decode(download("https://gripsack.dev/release.json"))
    require(isinstance(current, dict) and set(current) == BINDING_FIELDS
            and current["format"] == "gripsack.site-release.v1"
            and current["repository"] == REPOSITORY, "no deployed signed release selection; preserve existing site")
    return selectors(current["tag"], current["manifest_sha256"], current["run_id"])


def tag_source(tag):
    obj = api(f"git/ref/tags/{tag}")["object"]
    for _ in range(4):
        require(re.fullmatch(r"[0-9a-f]{40}", obj.get("sha", "")), "invalid tag source")
        if obj["type"] == "commit":
            commit = api(f"git/commits/{obj['sha']}")
            require(commit["sha"] == obj["sha"], "commit identity differs")
            return {"commit": obj["sha"], "tree": commit["tree"]["sha"]}
        require(obj["type"] == "tag", "tag does not resolve to commit")
        obj = api(f"git/tags/{obj['sha']}")["object"]
    raise ValueError("tag indirection exceeds bound")


def published_release(tag):
    release = api(f"releases/tags/{tag}")
    require(release.get("tag_name") == tag and release.get("draft") is False
            and release.get("prerelease") is False and release.get("published_at")
            and type(release.get("id")) is int and release["id"] > 0, "release is not published stable")
    return release


def signing_run(run_id, tag, source):
    run = api(f"actions/runs/{run_id}")
    require(run.get("id") == run_id and run.get("repository", {}).get("id") == REPOSITORY_ID
            and run.get("repository", {}).get("full_name") == REPOSITORY
            and run.get("head_repository", {}).get("id") == REPOSITORY_ID
            and run.get("head_sha") == source["commit"] and run.get("head_branch") == tag
            and run.get("path") == WORKFLOW and run.get("event") == "workflow_dispatch"
            and type(run.get("run_attempt")) is int and run["run_attempt"] > 0,
            "signing run identity differs")
    # Dispatch happens inside this run. Requiring completion here would race
    # publication; consumer completion is observed independently after deployment.
    require((run.get("status") == "in_progress" and run.get("conclusion") is None)
            or (run.get("status") == "completed" and run.get("conclusion") == "success"),
            "signing run is neither publishing nor successful")
    return run


def verify_results(results, manifest, digest, run, tag):
    require(isinstance(results, list) and results, "no verified attestation")
    predicate = {"format": "gripsack.local-qualification.v1", "policy": POLICY,
                 "source": manifest["source"], "candidate_id": manifest["candidate_id"],
                 "qualification_sha256": manifest["qualification_sha256"],
                 "recipe_sha256": manifest["recipe_sha256"], "builder": "local", "hosted_build": False}
    # gh v2.102.0 verify.go documents verificationResult.signature.certificate.
    # sigstore-go v1.3.0 pkg/fulcio/certificate/{summarize,extensions}.go flattens
    # runInvocationURI/sourceRepositoryIdentifier into that certificate object.
    invocation = f"https://github.com/{REPOSITORY}/actions/runs/{run['id']}/attempts/{run['run_attempt']}"
    for result in results:
        verified = result.get("verificationResult", {})
        statement = verified.get("statement", {})
        certificate = verified.get("signature", {}).get("certificate", {})
        if (statement.get("predicateType") == PREDICATE and statement.get("predicate") == predicate
                and any(subject.get("digest") == {"sha256": digest}
                        for subject in statement.get("subject", []))
                and certificate.get("runInvocationURI") == invocation
                and certificate.get("sourceRepositoryIdentifier") == str(REPOSITORY_ID)
                and certificate.get("buildTrigger") == "workflow_dispatch"):
            return
    raise ValueError("verified attestation does not bind manifest policy and signing run/attempt")


def verify(path, bundle, manifest, digest, run, tag):
    version = command(["gh", "--version"]).decode()
    match = re.search(r"gh version (\d+)\.(\d+)\.(\d+)", version)
    require(match and tuple(map(int, match.groups())) >= (2, 102, 0), "gh >= 2.102.0 required; no unsigned fallback")
    ref = f"refs/tags/{tag}"
    source = manifest["source"]["commit"]
    args = ["gh", "attestation", "verify", str(path), "--repo", REPOSITORY, "--hostname", "github.com",
            "--cert-identity", f"https://github.com/{REPOSITORY}/{WORKFLOW}@{ref}",
            "--cert-oidc-issuer", "https://token.actions.githubusercontent.com",
            "--source-ref", ref, "--source-digest", source, "--signer-digest", source,
            "--predicate-type", PREDICATE, "--deny-self-hosted-runners", "--format", "json"]
    # Both the published bundle and GitHub repository association must admit the
    # very same policy and run. Never parse an unverified bundle as authority.
    for suffix in (["--bundle", str(bundle)], []):
        verify_results(decode(command(args + suffix)), manifest, digest, run, tag)


def source_files(source):
    tree = api(f"git/trees/{source['tree']}")
    require(tree.get("sha") == source["tree"] and tree.get("truncated") is False, "source tree differs")
    files = {}
    for name in ("install.sh", "CHANGELOG.md"):
        entries = [entry for entry in tree["tree"] if entry["path"] == name]
        require(len(entries) == 1 and entries[0]["type"] == "blob"
                and entries[0]["mode"] in ("100644", "100755"), "source file is missing or not regular")
        data = download(f"https://raw.githubusercontent.com/{REPOSITORY}/{source['commit']}/{name}")
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        require(blob == entries[0]["sha"], "source file bytes differ from bound tree")
        files[name] = data
    return files


def admit(tag, digest, run_id):
    tag, digest, run_id = selectors(tag, digest, run_id)
    release = published_release(tag)
    version = tag.removeprefix("core-v")
    name = f"gripsack-release-{version}.json"
    base = f"https://github.com/{REPOSITORY}/releases/download/{tag}"
    data = download(f"{base}/{name}")
    require(hashlib.sha256(data).hexdigest() == digest, "nominated manifest digest differs")
    manifest = decode(data)
    require(manifest.get("format") == "gripsack.release.v1" and manifest.get("repository") == REPOSITORY
            and manifest.get("policy") == POLICY and manifest.get("platform") == "linux-x86_64"
            and manifest.get("provenance") == {"builder": "local", "hosted_build": False}
            and manifest.get("compatible", {}).get("core") == version
            and manifest.get("signer") == {"workflow": WORKFLOW, "ref": f"refs/tags/{tag}"},
            "unsupported manifest authority/version")
    for field in ("candidate_id", "qualification_sha256", "recipe_sha256"):
        require(isinstance(manifest.get(field), str) and re.fullmatch(r"[0-9a-f]{64}", manifest[field]),
                f"invalid manifest {field}")
    source = tag_source(tag)
    require(manifest.get("source") == source and re.fullmatch(r"[0-9a-f]{40}", source["tree"]), "manifest source differs")
    run = signing_run(run_id, tag, source)
    assets = []
    for page in range(1, 11):
        batch = api(f"releases/{release['id']}/assets?per_page=100&page={page}")
        require(isinstance(batch, list), "invalid public assets")
        assets.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError("public asset inventory exceeds bound")
    expected = {Path(item["path"]).name for item in manifest["artifacts"]} | {name, name + ".sigstore.json"}
    require(len(assets) == len(expected) and {a["name"] for a in assets} == expected, "public asset inventory differs")
    with tempfile.TemporaryDirectory(prefix="site-attestation-") as directory:
        path = Path(directory) / name
        path.write_bytes(data)
        bundle = Path(directory) / (name + ".sigstore.json")
        bundle.write_bytes(download(f"{base}/{bundle.name}"))
        verify(path, bundle, manifest, digest, run, tag)
    files = source_files(source)
    require(published_release(tag)["id"] == release["id"] and tag_source(tag) == source,
            "release changed during admission")
    fresh_run = signing_run(run_id, tag, source)
    require(fresh_run["run_attempt"] == run["run_attempt"], "signing attempt changed during admission")
    binding = {"format": "gripsack.site-release.v1", "repository": REPOSITORY, "source": source,
               "candidate_id": manifest["candidate_id"], "manifest_sha256": digest, "tag": tag,
               "run_id": run_id, "release_id": release["id"], "version": version}
    return binding, files


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-tag")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--run-id")
    return parser.parse_args()
