"""QMS seed invariants (SPEC.md §V.7–§V.11)."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "config/bootstrap/features.yaml"
NUMBERING = ROOT / "config/master/05-numbering-sequences.yaml"
LOTS = ROOT / "config/master/55-lot-serial-classes.yaml"
PARTS = ROOT / "config/master/80-stock-items-parts.yaml"
KITS = ROOT / "config/master/82-stock-items-kits.yaml"
PLANS = ROOT / "config/qms/10-inspection-plans.yaml"
ITEM_QMS = ROOT / "config/qms/20-stock-item-qms.yaml"
QM_ROLE_USERS = ROOT / "config/qms/30-qm-role-users.yaml"
BUY = ROOT / "scenario/20-buy.yaml"
BUILD = ROOT / "scenario/30-build.yaml"
README = ROOT / "README.md"

RAW_ITEMS = (
    "RAW-ECH-EXT4",
    "RAW-ELD-EXT10",
    "RAW-ASH-EXT5",
    "RAW-COQ10-99",
    "RAW-OMEGA3-70",
    "RAW-ASTA-10",
)

PLAN_BY_ITEM = {
    "RAW-ECH-EXT4": "PLAN-ECH-EXT4",
    "RAW-ELD-EXT10": "PLAN-ELD-EXT10",
    "RAW-ASH-EXT5": "PLAN-ASH-EXT5",
    "RAW-COQ10-99": "PLAN-COQ10-99",
    "RAW-OMEGA3-70": "PLAN-OMEGA3-70",
    "RAW-ASTA-10": "PLAN-ASTA-10",
}


def load_records(path: Path) -> list[dict]:
    out = subprocess.check_output(["yq", "-o=json", ".records", str(path)])
    return json.loads(out)


def load_mapping(path: Path) -> dict:
    out = subprocess.check_output(["yq", "-o=json", ".", str(path)])
    return json.loads(out)


class TestV7RawLotTracked(unittest.TestCase):
    def test_lot_serial_feature_enabled(self):
        names = FEATURES.read_text().splitlines()
        self.assertIn("- LotSerialTracking", names)

    def test_lot_raw_class(self):
        recs = load_records(LOTS)
        by_id = {r["ClassID"]: r for r in recs}
        self.assertEqual(set(by_id), {"LOTRAW", "NOTRACK"})
        row = by_id["LOTRAW"]
        self.assertEqual(row["TrackingMethod"], "Track Lot Numbers")
        self.assertEqual(row["AssignmentMethod"], "When Received")
        self.assertEqual(row["IssueMethod"], "User-Enterable")
        self.assertTrue(row["TrackExpirationDate"])
        segs = row["Segments"]
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0]["Type"], "Auto-Incremental Value")
        self.assertEqual(by_id["NOTRACK"]["TrackingMethod"], "Not Tracked")

    def test_kits_use_notrack(self):
        recs = load_records(KITS)
        self.assertGreaterEqual(len(recs), 1)
        for row in recs:
            with self.subTest(item=row["InventoryID"]):
                self.assertEqual(row["LotSerialClass"], "NOTRACK")

    def test_parts_use_lot_raw(self):
        by_id = {r["InventoryID"]: r for r in load_records(PARTS)}
        self.assertEqual(set(by_id), set(RAW_ITEMS))
        for item_id, row in by_id.items():
            with self.subTest(item=item_id):
                self.assertEqual(row["LotSerialClass"], "LOTRAW")
                self.assertNotIn("UsrQMSInspectionRequired", row)

    def test_buy_receipts_carry_lot_and_expiry(self):
        text = BUY.read_text()
        self.assertIn("LotSerialNbr:", text)
        self.assertIn("ExpirationDate:", text)
        for item_id in RAW_ITEMS:
            self.assertIn(item_id, text)

    def test_build_allocates_raw_lots(self):
        text = BUILD.read_text()
        self.assertIn("StockComponents:", text)
        self.assertIn("Allocations:", text)
        self.assertIn("expand: [StockComponents]", text)
        self.assertIn("LotSerialNbr: NB-ECH-25001", text)
        self.assertIn("LotSerialNbr: NM-OM3-25001", text)
        for item_id in RAW_ITEMS:
            self.assertIn(item_id, text)


class TestV8QmsNumbering(unittest.TestCase):
    def test_qord_qncr_present(self):
        by_id = {r["NumberingID"]: r for r in load_records(NUMBERING)}
        self.assertIn("QORD", by_id)
        self.assertIn("QNCR", by_id)
        self.assertEqual(by_id["QORD"]["Descr"], "QMS Inspection Order")
        self.assertEqual(by_id["QNCR"]["Descr"], "QMS NCR")


class TestV9QmsPlansAfterPublish(unittest.TestCase):
    def test_plans_use_qms_endpoint(self):
        doc = load_mapping(PLANS)
        self.assertEqual(doc["entity"], "InspectionPlan")
        self.assertEqual(doc["endpoint"], "QMS/22.200.001")
        self.assertEqual(doc["detail_keys"]["Tests"], "LineNbr")

    def test_one_active_plan_per_raw_item(self):
        recs = load_records(PLANS)
        by_item = {r["InventoryID"]: r for r in recs}
        self.assertEqual(set(by_item), set(RAW_ITEMS))
        for item_id, plan_id in PLAN_BY_ITEM.items():
            plan = by_item[item_id]
            self.assertEqual(plan["PlanID"], plan_id)
            self.assertEqual(plan["Status"], "A")
            tests = plan["Tests"]
            self.assertGreaterEqual(len(tests), 1)
            self.assertEqual(tests[0]["LineNbr"], 10)
            self.assertEqual(tests[0]["Criticality"], "C")


class TestV10QmsItemFlags(unittest.TestCase):
    def test_usr_flags_live_in_qms_tree(self):
        recs = load_records(ITEM_QMS)
        by_id = {r["InventoryID"]: r for r in recs}
        self.assertEqual(set(by_id), set(RAW_ITEMS))
        for item_id, plan_id in PLAN_BY_ITEM.items():
            row = by_id[item_id]
            self.assertTrue(row["UsrQMSInspectionRequired"])
            self.assertEqual(row["UsrQMSInspectionPlanID"], plan_id)
            self.assertGreater(row["UsrMinShelfLifeDays"], 0)


class TestV11QmRoleUsers(unittest.TestCase):
    def test_qa_director_and_llm_agent_get_quality_manager(self):
        recs = load_records(QM_ROLE_USERS)
        self.assertEqual(len(recs), 1)
        row = recs[0]
        self.assertEqual(row["Rolename"], "Quality Manager")
        names = [u["Username"] for u in row["Users"]]
        self.assertEqual(names, ["qa-director", "llm-agent"])


PIN = ROOT / "customization/Lab5.QMS.pin"
MAKEFILE = ROOT / "Makefile"


class TestReadmeQmsLayout(unittest.TestCase):
    def test_readme_documents_qms_apply_and_drops_matrix(self):
        text = README.read_text()
        self.assertNotIn("matrix.yaml", text)
        self.assertIn("config/qms/", text)
        self.assertIn("acu apply config/qms/", text)
        self.assertIn("LOTRAW", text)
        self.assertIn("QORD", text)
        self.assertIn("gmake publish", text)
        self.assertIn("customization/Lab5.QMS.pin", text)
        self.assertIn("acu tenant delete", text)
        self.assertIn("acu tenant create", text)

    def test_readme_does_not_run_acu_check(self):
        in_fence = False
        for line in README.read_text().splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                continue
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            self.assertFalse(
                stripped == "acu check" or stripped.startswith("acu check "),
                f"rebuild fence must not invoke acu check: {stripped}",
            )


class TestV12PinnedLab5Qms(unittest.TestCase):
    def test_pin_names_release_and_digest(self):
        text = PIN.read_text()
        required = ("repo=", "tag=", "asset=", "sha256=", "package=", "endpoint=")
        for key in required:
            self.assertIn(key, text)
        self.assertIn("kborovik/acu-custom-qms", text)
        self.assertIn("Lab5_QMS_Customization.zip", text)
        self.assertIn("QMS/22.200.001", text)
        sha = next(
            line.split("=", 1)[1].strip()
            for line in text.splitlines()
            if line.startswith("sha256=")
        )
        self.assertEqual(len(sha), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in sha))

    def test_makefile_rebuild_skips_acu_check(self):
        text = MAKEFILE.read_text()
        self.assertIn("lab5-qms deploy", text)
        self.assertIn("tenant delete", text)
        self.assertIn("tenant create", text)
        self.assertNotRegex(text, r"(?m)^\s*acu check\b")


if __name__ == "__main__":
    unittest.main()
