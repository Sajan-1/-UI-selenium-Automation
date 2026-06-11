from pathlib import Path
import re

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

backup = Path("testes_BACKUP_BEFORE_PROBLEMS_CLEANUP.py")
backup.write_text(s, encoding="utf-8")

# 1) Remove bad NUL / invalid unicode control chars
s = s.replace("\x00", "")

# 2) Remove literal broken \u0 tokens if they were inserted as text
s = s.replace("\\u0", "")

# 3) Ensure _re exists if old patches use it
if "import re as _re" not in s:
    # Add near imports/top safely
    s = "import re as _re\n" + s

p.write_text(s, encoding="utf-8")

print("DONE: cleaned invalid chars and added import re as _re")
print("Backup:", backup)
