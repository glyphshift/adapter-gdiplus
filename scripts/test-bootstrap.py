"""Contract checks for SDK integrity and refusing a modified generated cache."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bootstrap", ROOT / "scripts/bootstrap-sdk.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BootstrapContracts(unittest.TestCase):
    def setUp(self):
        evidence = ROOT / "local-test/evidence/sdk-contracts"
        evidence.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=evidence)
        self.root = Path(self.temp.name)
        lock = json.loads((ROOT / "sdk.lock.json").read_text())
        destination = self.root / lock["archive"]
        destination.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / lock["archive"], destination)
        shutil.copyfile(ROOT / "sdk.lock.json", self.root / "sdk.lock.json")

    def tearDown(self):
        self.temp.cleanup()

    def test_modified_archive_rejected_before_extraction(self):
        archive = next((self.root / "vendor").glob("*.zip"))
        archive.write_bytes(archive.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            module.bootstrap(self.root)
        self.assertFalse((self.root / ".sdk").exists())

    def test_repeated_bootstrap_preserves_verified_cache_and_rejects_edits(self):
        module.bootstrap(self.root)
        module.bootstrap(self.root)
        source = self.root / ".sdk/crates/adapters/platform/sdk/src/lib.rs"
        source.write_bytes(source.read_bytes() + b"\n// changed\n")
        with self.assertRaisesRegex(ValueError, "cache changed"):
            module.bootstrap(self.root)
        self.assertTrue(source.read_bytes().endswith(b"// changed\n"))

    def test_lock_provenance_mismatch_rejected(self):
        path = self.root / "sdk.lock.json"
        lock = json.loads(path.read_text())
        lock["source_commit"] = "0" * 40
        path.write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            module.bootstrap(self.root)


if __name__ == "__main__":
    unittest.main()
