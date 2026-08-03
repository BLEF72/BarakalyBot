import sqlite3
c = sqlite3.connect("foodsave.db")
print([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='index'")])
