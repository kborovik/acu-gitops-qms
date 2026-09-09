"""QMS seed invariants (SPEC.md §V.7–§V.15)."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "config/bootstrap/features.yaml"
NUMBERING = ROOT / "config/master/05-numbering-sequences.yaml"
IN_PREFS = ROOT / "config/master/20-in-preferences.yaml"
LOTS = ROOT / "config/master/55-lot-serial-classes.yaml"
PARTS = ROOT / "config/master/80-stock-items-parts.yaml"
KITS = ROOT / "config/master/82-stock-items-kits.yaml"
KIT_SPECS = ROOT / "config/master/85-kit-specifications.yaml"
PLANS = ROOT / "config/qms/10-inspection-plans.yaml"
ITEM_QMS = ROOT / "config/qms/20-stock-item-qms.yaml"
QM_ROLE_USERS = ROOT / "config/qms/30-qm-role-users.yaml"
BUY = ROOT / "scenario/20-buy.yaml"
WH_LOCS = ROOT / "config/master/51-warehouse-locations.yaml"
WH_DEF = ROOT / "config/master/52-warehouse-defaults.yaml"
SCENARIO = ROOT / "scenario"
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
        self.assertIn("Location: QCHOLD", text)
        self.assertNotIn("Location: MAIN", text)
        for item_id in RAW_ITEMS:
            self.assertIn(item_id, text)


class TestV13QcReadyLocations(unittest.TestCase):
    def test_warehouse_has_qc_hold_and_ready(self):
        recs = load_records(WH_LOCS)
        self.assertEqual(len(recs), 1)
        wh = recs[0]
        self.assertEqual(wh["WarehouseID"], "WH-MISS-01")
        self.assertEqual(wh["ReceivingLocationID"], "QCHOLD")
        self.assertEqual(wh["ShippingLocationID"], "READY")
        self.assertEqual(wh["RMALocationID"], "QCHOLD")
        by_id = {row["LocationID"]: row for row in wh["Locations"]}
        self.assertEqual(set(by_id), {"MAIN", "QCHOLD", "READY", "QUARANTINE"})
        hold = by_id["QCHOLD"]
        self.assertTrue(hold["ReceiptsAllowed"])
        self.assertTrue(hold["TransfersAllowed"])
        self.assertFalse(hold["SalesAllowed"])
        self.assertFalse(hold["AssemblyAllowed"])
        ready = by_id["READY"]
        self.assertFalse(ready["ReceiptsAllowed"])
        self.assertTrue(ready["SalesAllowed"])
        self.assertTrue(ready["TransfersAllowed"])
        self.assertTrue(ready["AssemblyAllowed"])
        quar = by_id["QUARANTINE"]
        self.assertEqual(quar["Description"], "Quarantine")
        self.assertFalse(quar["ReceiptsAllowed"])
        self.assertFalse(quar["SalesAllowed"])
        self.assertTrue(quar["TransfersAllowed"])
        self.assertFalse(quar["AssemblyAllowed"])

    def test_warehouse_defaults_match_locations(self):
        recs = load_records(WH_DEF)
        self.assertEqual(len(recs), 1)
        row = recs[0]
        self.assertEqual(row["ReceivingLocationID"], "QCHOLD")
        self.assertEqual(row["ShippingLocationID"], "READY")
        self.assertEqual(row["RMALocationID"], "QCHOLD")


class TestV14RunIsCapitalBuy(unittest.TestCase):
    def test_run_scenarios_are_capital_and_buy(self):
        names = sorted(p.name for p in SCENARIO.glob("*.yaml"))
        self.assertEqual(names, ["10-seed-capital.yaml", "20-buy.yaml"])
        self.assertFalse((SCENARIO / "30-build.yaml").exists())
        self.assertFalse((SCENARIO / "40-sell.yaml").exists())

    def test_kit_specs_and_inkitassy_absent(self):
        self.assertFalse(KIT_SPECS.exists())
        by_id = {r["NumberingID"]: r for r in load_records(NUMBERING)}
        self.assertNotIn("INKITASSY", by_id)
        recs = load_records(IN_PREFS)
        self.assertEqual(len(recs), 1)
        self.assertNotIn("KitAssemblyNumberingID", recs[0])

    def test_readme_drops_kit_specs(self):
        text = README.read_text()
        self.assertNotIn("85-kit-specifications.yaml", text)
        self.assertNotIn("INKITASSY", text)
        self.assertNotIn("KitAssemblyNumberingID", text)
        self.assertNotIn("Kit specs stay", text)
        self.assertNotIn("Kit specs follow", text)


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
    def test_item_qms_uses_qms_endpoint(self):
        doc = load_mapping(ITEM_QMS)
        self.assertEqual(doc["entity"], "StockItem")
        self.assertEqual(doc["endpoint"], "QMS/22.200.001")

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

    def test_readme_does_not_call_item_qms_apply_a_noop(self):
        text = README.read_text()
        self.assertNotIn("is a no-op", text)
        self.assertIn("config/qms/20-stock-item-qms.yaml", text)
        self.assertIn("endpoint: QMS/22.200.001", text)

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
        self.assertIn("tag=v0.4.0", text)
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


SEED_DIRS = (
    ROOT / "config/bootstrap",
    ROOT / "config/baseline",
    ROOT / "config/setup",
    ROOT / "config/master",
)
QMS_ONLY = re.compile(
    r"QMS/22\.200\.001|UsrQMS|entity: InspectionPlan|Rolename: Quality Manager"
)
REBUILD_STEPS = (
    "delete",
    "create",
    "apply",
    "run",
    "publish",
    "qms",
    "diff",
    "state",
)


def makefile_prereqs(name: str) -> list[str]:
    prefix = f"{name}:"
    for line in MAKEFILE.read_text().splitlines():
        if line.startswith(prefix):
            head = line.split("##", 1)[0]
            return [p for p in head.split(":", 1)[1].split() if p != ".WAIT"]
    raise AssertionError(f"Makefile target {name} missing")


def makefile_recipe(name: str) -> list[str]:
    prefix = f"{name}:"
    collecting = False
    recipe: list[str] = []
    for line in MAKEFILE.read_text().splitlines():
        if line.startswith(prefix):
            collecting = True
            continue
        if not collecting:
            continue
        if line.startswith("\t"):
            recipe.append(line[1:])
            continue
        if recipe:
            break
    return recipe


class TestV15StockPathWithoutQms(unittest.TestCase):
    def test_makefile_rebuild_runs_apply_then_run_before_publish(self):
        steps = makefile_prereqs("rebuild")
        self.assertEqual(steps, list(REBUILD_STEPS))
        self.assertLess(steps.index("apply"), steps.index("run"))
        self.assertLess(steps.index("run"), steps.index("publish"))
        self.assertLess(steps.index("publish"), steps.index("qms"))

    def test_makefile_apply_does_not_apply_config_qms(self):
        recipe = makefile_recipe("apply")
        self.assertIn("acu apply", recipe)
        self.assertFalse(any("config/qms" in line for line in recipe))
        qms = makefile_recipe("qms")
        self.assertTrue(any("config/qms" in line for line in qms))

    def test_seed_dirs_and_scenario_omit_qms_only_tokens(self):
        hits: list[str] = []
        roots = [*SEED_DIRS, ROOT / "scenario"]
        for root in roots:
            for path in root.rglob("*.yaml"):
                text = path.read_text()
                if QMS_ONLY.search(text):
                    hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [])

    def test_qms_tree_holds_qms_only_tokens(self):
        texts = [p.read_text() for p in (ROOT / "config/qms").glob("*.yaml")]
        joined = "\n".join(texts)
        self.assertIn("QMS/22.200.001", joined)
        self.assertIn("UsrQMS", joined)
        self.assertIn("entity: InspectionPlan", joined)
        self.assertIn("Rolename: Quality Manager", joined)

    def test_readme_rebuild_order_apply_run_before_publish(self):
        text = README.read_text()
        apply_at = text.index("\nacu apply\n")
        run_at = text.index("\nacu run\n")
        publish_at = text.index("\ngmake publish\n")
        qms_at = text.index("\nacu apply config/qms/\n")
        self.assertLess(apply_at, run_at)
        self.assertLess(run_at, publish_at)
        self.assertLess(publish_at, qms_at)
        self.assertIn(
            "`gmake apply` and `gmake run` succeed on a virgin tenant before Lab5.QMS is published.",
            text,
        )


if __name__ == "__main__":
    unittest.main()
