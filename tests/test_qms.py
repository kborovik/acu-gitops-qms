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
PLANS = ROOT / "config/qms/10-inspection-plans.yaml"
ITEM_QMS = ROOT / "config/qms/20-stock-item-qms.yaml"
QM_ROLE_USERS = ROOT / "config/qms/30-qm-role-users.yaml"
BUY = ROOT / "scenario/20-buy.yaml"
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
        self.assertEqual(len(recs), 1)
        row = recs[0]
        self.assertEqual(row["ClassID"], "LOTRAW")
        self.assertEqual(row["TrackingMethod"], "Track Lot Numbers")
        self.assertEqual(row["AssignmentMethod"], "When Received")
        self.assertEqual(row["IssueMethod"], "User-Enterable")
        self.assertTrue(row["TrackExpirationDate"])
        segs = row["Segments"]
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0]["Type"], "Auto-Incremental Value")

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


class TestReadmeQmsLayout(unittest.TestCase):
    def test_readme_documents_qms_apply_and_drops_matrix(self):
        text = README.read_text()
        self.assertNotIn("matrix.yaml", text)
        self.assertIn("config/qms/", text)
        self.assertIn("acu apply config/qms/", text)
        self.assertIn("LOTRAW", text)
        self.assertIn("QORD", text)


if __name__ == "__main__":
    unittest.main()
