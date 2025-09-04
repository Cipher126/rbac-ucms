import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

connection_uri = psycopg2.connect(
    host= os.getenv("DB_HOST"),
    database= os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

# connection = connection_uri
#
# with connection.cursor() as cursor:
#     cursor.execute("""
#         ALTER TABLE results
#         ALTER COLUMN session TYPE VARCHAR(20);
#     """)
# connection.commit()
