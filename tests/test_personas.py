"""Persona seed invariants (SPEC.md §V.1–§V.6)."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USERS = ROOT / "acu-config/master/91-users.yaml"
ROLES = ROOT / "acu-config/master/90-roles.yaml"
ROLE_USERS = ROOT / "acu-config/master/92-role-users.yaml"
README = ROOT / "README.md"

PERSON_USERNAMES = ("etremblay", "mvance", "dsingh", "sarchambault")

JOB_USERS = {
    "qa-director": {
        "FirstName": "Elodie",
        "LastName": "Tremblay",
        "roles": ["IN Manager", "PO Viewer"],
    },
    "vp-supply-chain": {
        "FirstName": "Marcus",
        "LastName": "Vance",
        "roles": ["PO Admin", "SO Admin"],
    },
    "receiving-supervisor": {
        "FirstName": "Devon",
        "LastName": "Singh",
        "roles": ["IN Receiver", "PO Clerk"],
    },
    "erp-architect": {
        "FirstName": "Sophie",
        "LastName": "Archambault",
        "roles": ["Administrator"],
    },
}

KEBAB = re.compile(r"^[a-z]+(-[a-z0-9]+)*$")


def load_records(path: Path) -> list[dict]:
    out = subprocess.check_output(["yq", "-o=json", ".records", str(path)])
    return json.loads(out)


def users_by_username() -> dict[str, dict]:
    return {u["Username"]: u for u in load_records(USERS)}


class TestV1LoginIsJobFunction(unittest.TestCase):
    def test_usernames_are_kebab_case_job_functions(self):
        names = [u["Username"] for u in load_records(USERS)]
        for name in names:
            with self.subTest(username=name):
                self.assertRegex(name, KEBAB)
                self.assertNotIn(name, PERSON_USERNAMES)
        for expected in JOB_USERS:
            self.assertIn(expected, names)

    def test_person_initial_usernames_absent_from_users_yaml(self):
        names = {u["Username"] for u in load_records(USERS)}
        for old in PERSON_USERNAMES:
            self.assertNotIn(old, names)


class TestV2DisplayNameIsPerson(unittest.TestCase):
    def test_human_given_names_stay(self):
        by_name = users_by_username()
        for username, expected in JOB_USERS.items():
            user = by_name[username]
            self.assertEqual(user["FirstName"], expected["FirstName"])
            self.assertEqual(user["LastName"], expected["LastName"])


class TestV3ErpRolesStayBundled(unittest.TestCase):
    def test_each_login_keeps_erp_role_set(self):
        by_name = users_by_username()
        for username, expected in JOB_USERS.items():
            got = [r["Rolename"] for r in by_name[username]["Roles"]]
            self.assertEqual(got, expected["roles"])

    def test_user_roles_omit_selected(self):
        for user in load_records(USERS):
            for row in user["Roles"]:
                self.assertNotIn("Selected", row)

    def test_role_users_yaml_matches_user_roles(self):
        by_role: dict[str, list[str]] = {}
        for user in load_records(USERS):
            for row in user["Roles"]:
                by_role.setdefault(row["Rolename"], []).append(user["Username"])
        live = {r["Rolename"]: [u["Username"] for u in r["Users"]] for r in load_records(ROLE_USERS)}
        self.assertEqual(live, by_role)


class TestV5EmailFollowsUsername(unittest.TestCase):
    def test_email_is_username_at_cannordic(self):
        for user in load_records(USERS):
            self.assertEqual(user["Email"], f"{user['Username']}@cannordic.ca")


def readme_persona_usernames() -> list[str]:
    names: list[str] = []
    in_table = False
    for line in README.read_text().splitlines():
        if line.startswith("| User |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if re.match(r"^\|[\s|-]+\|$", line):
            continue
        match = re.match(r"^\| `([^`]+)` \|", line)
        if match:
            names.append(match.group(1))
    return names


class TestV6PersonasSync(unittest.TestCase):
    def test_readme_usernames_match_users_yaml(self):
        yaml_names = [u["Username"] for u in load_records(USERS)]
        self.assertEqual(readme_persona_usernames(), yaml_names)


SKIP_DIRS = {".git", "__pycache__", ".spec", "tests"}
SKIP_FILES = {"SPEC.md", ".env", ".env.gpg"}


class TestV1LeftoverSweep(unittest.TestCase):
    def test_person_usernames_absent_from_seed_surfaces(self):
        pattern = re.compile("|".join(re.escape(n) for n in PERSON_USERNAMES))
        hits: list[str] = []
        for path in ROOT.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name in SKIP_FILES or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if pattern.search(text):
                hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [])


class TestV4LlmAgentQmUser(unittest.TestCase):
    def test_llm_agent_user_is_not_a_human_persona(self):
        user = users_by_username()["llm-agent"]
        self.assertEqual(user["FirstName"], "LLM")
        self.assertEqual(user["LastName"], "Agent")
        self.assertEqual(user["Email"], "llm-agent@cannordic.ca")
        roles = [r["Rolename"] for r in user["Roles"]]
        self.assertEqual(roles, ["LLM Agent"])
        self.assertNotEqual(user["Username"], "LLM Agent")


class TestV4LlmAgentQmRole(unittest.TestCase):
    def test_llm_agent_role_exists_with_qm_descr(self):
        roles = {r["Rolename"]: r for r in load_records(ROLES)}
        self.assertIn("LLM Agent", roles)
        descr = roles["LLM Agent"]["Descr"]
        self.assertIn("QM documents", descr)
        self.assertIn("inspection orders", descr)
        self.assertIn("CoA files", descr)
        self.assertIn("NCR", descr)

    def test_stock_roles_still_present(self):
        names = {r["Rolename"] for r in load_records(ROLES)}
        for stock in (
            "Administrator",
            "IN Manager",
            "PO Viewer",
            "PO Admin",
            "SO Admin",
            "IN Receiver",
            "PO Clerk",
            "LLM Prompt Engineer",
            "LLM Security Expert",
        ):
            self.assertIn(stock, names)


if __name__ == "__main__":
    unittest.main()
