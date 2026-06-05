from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

if "[WEBEX PRE-SEND ATTACHMENT] Applying Overview master report fix before attachment upload" in s:
    print("Already patched.")
    raise SystemExit(0)

target = "      _report_path = _classlens_webex_find_report_file()\n      url = \"https://webexapis.com/v1/messages\""
if target not in s:
    target = "    _report_path = _classlens_webex_find_report_file()\n    url = \"https://webexapis.com/v1/messages\""

if target not in s:
    raise SystemExit("Target attachment sender block not found. Run: Select-String -Path .\\testes.py -Pattern \"files=files\" -Context 25,25")

indent = target.split("_report_path")[0]

insert = (
    indent + "try:\n"
    + indent + "    print(\"[WEBEX PRE-SEND ATTACHMENT] Applying Overview master report fix before attachment upload...\")\n"
    + indent + "    __cl_force_full_detailed_overview_in_master_now__()\n"
    + indent + "    print(\"[WEBEX PRE-SEND ATTACHMENT] Overview master report fix complete.\")\n"
    + indent + "except Exception as exc:\n"
    + indent + "    print(\"[WEBEX PRE-SEND ATTACHMENT] Overview fix failed:\", exc)\n\n"
)

backup = Path("testes_BACKUP_BEFORE_ATTACHMENT_PRESEND_FIX.py")
backup.write_text(s, encoding="utf-8")

s = s.replace(target, insert + target, 1)
p.write_text(s, encoding="utf-8")

print("DONE: Attachment Webex sender patched before _report_path lookup.")
print("Backup:", backup)
