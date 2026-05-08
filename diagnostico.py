"""Script de diagnostico para verificar a situacao dos dados no banco."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'financas.db')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 50)
print("DIAGNOSTICO DO BANCO DE DADOS")
print("=" * 50)

print("\nUSUARIOS CADASTRADOS:")
c.execute('SELECT id, nome, email FROM usuarios')
for r in c.fetchall():
    print(f"  ID={r['id']}, Nome={r['nome']}, Email={r['email']}")

print("\nTRANSACOES POR USUARIO_ID:")
c.execute('SELECT usuario_id, COUNT(*) as total FROM transacoes GROUP BY usuario_id')
for r in c.fetchall():
    print(f"  usuario_id={r['usuario_id']} -> {r['total']} transacoes")

print("\nDESPESAS FIXAS POR USUARIO_ID:")
c.execute('SELECT usuario_id, COUNT(*) as total FROM despesas_fixas GROUP BY usuario_id')
rows = c.fetchall()
if rows:
    for r in rows:
        print(f"  usuario_id={r['usuario_id']} -> {r['total']} despesas fixas")
else:
    print("  (nenhuma)")

conn.close()
