import psycopg2
from config.settings import load_config

config = load_config()
conn = psycopg2.connect(config.get_database_url())
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

# Get user info from email_statistics
cur.execute("SELECT DISTINCT user_id FROM email_statistics WHERE sender = %s OR recipient = %s", 
           ('jauwwad.nallamandu123@gmail.com', 'jauwwad.nallamandu123@gmail.com'))
user_results = cur.fetchall()
print('User IDs for jauwwad.nallamandu123@gmail.com:', user_results)

conn.close()