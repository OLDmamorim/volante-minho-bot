import sqlite3

conn = sqlite3.connect('database/hugo_bot.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE requests ADD COLUMN observations TEXT")
    conn.commit()
    print("✅ Coluna 'observations' adicionada com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ Coluna 'observations' já existe.")
    else:
        print(f"❌ Erro: {e}")

conn.close()
