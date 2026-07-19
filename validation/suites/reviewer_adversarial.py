from __future__ import annotations

from validation.contracts import suite_from_checks
from validation.suites.helpers import reviewer_check, suite_main


def run(ctx):
    checks = [
        reviewer_check(ctx, "plaintext_password", 'PASSWORD = "plaintext"\n', True, ["plaintext_password"]),
        reviewer_check(ctx, "missing_auth", 'def login(user, password):\n    return True\n', True, ["missing_authentication"]),
        reviewer_check(ctx, "sql_inline_concat", 'def f(conn, name):\n    return conn.execute("SELECT * FROM users WHERE name = " + name)\n', True, ["sql_injection"]),
        reviewer_check(ctx, "sql_variable_concat", 'def f(conn, name):\n    query = "SELECT * FROM users WHERE name = \'" + name + "\'"\n    return conn.execute(query)\n', True, ["sql_injection"]),
        reviewer_check(ctx, "sql_percent", 'def f(conn, name):\n    query = "SELECT * FROM users WHERE name = \'%s\'" % name\n    return conn.execute(query)\n', True, ["sql_injection"]),
        reviewer_check(ctx, "sql_augassign", 'def f(conn, name):\n    query = "SELECT * FROM users WHERE name = \'"\n    query += name\n    return conn.execute(query)\n', True, ["sql_injection"]),
        reviewer_check(ctx, "command_direct", 'import os\ndef f(cmd):\n    return os.system(cmd)\n', True, ["command_execution"]),
        reviewer_check(ctx, "command_alias", 'import subprocess as sp\ndef f(cmd):\n    return sp.run(cmd, shell=True)\n', True, ["command_execution"]),
        reviewer_check(ctx, "os_popen", 'import os\ndef f(cmd):\n    return os.popen(cmd).read()\n', True, ["command_execution"]),
        reviewer_check(ctx, "dangerous_fs_direct", 'import shutil\ndef f(path):\n    shutil.rmtree(path)\n', True, ["dangerous_filesystem_operation"]),
        reviewer_check(ctx, "dangerous_fs_alias", 'from shutil import rmtree\ndef f(path):\n    rmtree(path)\n', True, ["dangerous_filesystem_operation"]),
        reviewer_check(ctx, "path_unlink", 'from pathlib import Path\ndef f(path):\n    Path(path).unlink()\n', True, ["dangerous_filesystem_operation"]),
        reviewer_check(ctx, "protected_file_write", 'from pathlib import Path\ndef f():\n    Path("policies.yaml").write_text("broken")\n', True, ["critical_architecture_violation"]),
        reviewer_check(ctx, "protected_file_open_write", 'from pathlib import Path\ndef f():\n    Path("policies.yaml").open("w").write("broken")\n', True, ["critical_architecture_violation"]),
        reviewer_check(ctx, "secure_parameterized", 'import hmac, hashlib\ndef h(password):\n    return hashlib.sha256(password.encode()).hexdigest()\ndef authenticate(user, password, stored):\n    if not user or not stored:\n        return False\n    return hmac.compare_digest(h(password), stored)\ndef lookup(conn, name):\n    return conn.execute("SELECT * FROM users WHERE name = ?", (name,))\n', False),
    ]
    return suite_from_checks("reviewer_adversarial", checks)


if __name__ == "__main__":
    suite_main("reviewer_adversarial")

