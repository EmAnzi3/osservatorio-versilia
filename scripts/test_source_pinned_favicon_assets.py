#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import source_pinned_favicon_assets as pins


class PinnedFaviconAssetsTest(unittest.TestCase):
    def test_mic_dgcc_pin_is_exact_green_run_asset(self):
        payload = {
            "opportunities": [
                {"id": "x", "source_id": "mic-dgcc", "presentation": {}}
            ],
            "archive": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            materialized, provenance = pins.materialize(payload, Path(tmp))
            meta = provenance["mic-dgcc"]
            path = Path(tmp) / "assets" / "source-favicons" / "mic-dgcc.png"
            raw = path.read_bytes()
            self.assertEqual(len(raw), 19912)
            self.assertEqual(
                hashlib.sha256(raw).hexdigest(),
                "fb5906ca71b08563282e4f48a9ada17a1f481031ada4071e85671499f84775fc",
            )
            self.assertEqual(meta["method"], "pinned-official-asset-from-green-run")
            self.assertEqual(meta["acquiredFromRun"], 32622185338)
            self.assertIn("source-favicons/mic-dgcc.png", materialized["opportunities"][0]["presentation"]["source_favicon"])


if __name__ == "__main__":
    unittest.main()
