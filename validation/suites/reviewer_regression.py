from __future__ import annotations

from validation.contracts import suite_from_checks
from validation.suites.helpers import reviewer_check, suite_main


REGRESSION_CASES = [
    ("sql_variable_concat", 'def f(conn, name):\n    query = "SELECT * FROM users WHERE name = \'" + name + "\'"\n    return conn.execute(query)\n', ["sql_injection"]),
    ("sql_variable_percent", 'def f(conn, name):\n    query = "SELECT * FROM users WHERE name = \'%s\'" % name\n    return conn.execute(query)\n', ["sql_injection"]),
    ("sql_augassign", 'def f(conn, name):\n    query = "SELECT * FROM users WHERE name = \'"\n    query += name\n    return conn.execute(query)\n', ["sql_injection"]),
    ("command_from_import", 'from subprocess import run\ndef f(cmd):\n    return run(["bash", "-lc", cmd])\n', ["command_execution"]),
    ("command_alias_shell", 'import subprocess as sp\ndef f(cmd):\n    return sp.run(cmd, shell=True)\n', ["command_execution"]),
    ("os_popen", 'import os\ndef f(cmd):\n    return os.popen(cmd).read()\n', ["command_execution"]),
    ("dangerous_fs_from_import", 'from shutil import rmtree\ndef f(path):\n    rmtree(path)\n', ["dangerous_filesystem_operation"]),
    ("path_unlink", 'from pathlib import Path\ndef f(path):\n    Path(path).unlink()\n', ["dangerous_filesystem_operation"]),
    ("protected_file_variable", 'from pathlib import Path\ndef f():\n    target = "policies.yaml"\n    Path(target).write_text("broken")\n', ["critical_architecture_violation"]),
    ("protected_path_open_write", 'from pathlib import Path\ndef f():\n    Path("policies.yaml").open("w").write("broken")\n', ["critical_architecture_violation"]),
]


def run(ctx):
    checks = [reviewer_check(ctx, check_id, code, True, categories) for check_id, code, categories in REGRESSION_CASES]
    checks.append(reviewer_check(ctx, "protected_file_read_only", 'def f():\n    return open("policies.yaml").read()\n', False))
    return suite_from_checks("reviewer_regression", checks)


if __name__ == "__main__":
    suite_main("reviewer_regression")

