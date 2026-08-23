#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import source_pinned_favicon_assets as pins


class PinnedFaviconAssetsTest(unittest.TestCase):
    def setUp(self):
        self.meta = (pins._load().get("pins") or {})["mic-dgcc"]
        self.path = pins._asset_path(self.meta)

    def test_mic_dgcc_pin_is_exact_green_run_asset(self):
        raw, actual_sha = pins.validate_asset("mic-dgcc", self.path, self.meta)
        self.assertEqual(len(raw), 19912)
        self.assertEqual(actual_sha, "fb5906ca71b08563282e4f48a9ada17a1f481031ada4071e85671499f84775fc")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.meta["sha256"])
        self.assertEqual(self.meta["entity"], "Ministero della Cultura / DGCC")
        self.assertEqual(self.meta["acquisitionMethod"], "official-page-html-or-manifest")
        self.assertEqual(self.meta["acquiredFromRun"], 32622185338)
        self.assertEqual(self.meta["artifactId"], 9488890210)
        self.assertTrue(pins._valid_png(raw))

        payload = {"opportunities": [{"id": "x", "source_id": "mic-dgcc", "presentation": {}}], "archive": []}
        with tempfile.TemporaryDirectory() as tmp:
            materialized, provenance = pins.materialize(payload, Path(tmp))
            target = Path(tmp) / "assets" / "source-favicons" / "mic-dgcc.png"
            self.assertEqual(target.read_bytes(), raw)
            self.assertEqual(provenance["mic-dgcc"]["repositoryAsset"], "assets/institutional-favicons/mic-dgcc.png")
            self.assertEqual(provenance["mic-dgcc"]["method"], "pinned-official-asset-from-green-run")
            self.assertIn("source-favicons/mic-dgcc.png", materialized["opportunities"][0]["presentation"]["source_favicon"])

    def test_validation_rejects_missing_empty_invalid_and_hash_mismatch(self):
        raw = self.path.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing.png"
            with self.assertRaises(SystemExit):
                pins.validate_asset("mic-dgcc", missing, self.meta)

            empty = root / "empty.png"
            empty.write_bytes(b"")
            with self.assertRaises(SystemExit):
                pins.validate_asset("mic-dgcc", empty, self.meta)

            invalid = root / "invalid.png"
            invalid.write_bytes(b"<!doctype html><title>not an image</title>")
            invalid_meta = copy.deepcopy(self.meta)
            invalid_meta["bytes"] = invalid.stat().st_size
            invalid_meta["sha256"] = hashlib.sha256(invalid.read_bytes()).hexdigest()
            with self.assertRaises(SystemExit):
                pins.validate_asset("mic-dgcc", invalid, invalid_meta)

            mismatch = root / "mismatch.png"
            mismatch.write_bytes(raw)
            mismatch_meta = copy.deepcopy(self.meta)
            mismatch_meta["sha256"] = "0" * 64
            with self.assertRaises(SystemExit):
                pins.validate_asset("mic-dgcc", mismatch, mismatch_meta)


if __name__ == "__main__":
    unittest.main()
