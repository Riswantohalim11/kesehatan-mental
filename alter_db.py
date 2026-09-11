import os
import pymysql

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "12345678")
DB_NAME = os.getenv("DB_NAME", "kesehatan_mental")

conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=DB_NAME,
)

try:
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE bookings ADD COLUMN booking_time VARCHAR(20) DEFAULT '09:00 WIB'")
    cursor.execute("ALTER TABLE test_results ADD COLUMN risk_level VARCHAR(50) DEFAULT 'Rendah'")
    cursor.execute("ALTER TABLE test_results ADD COLUMN risk_response VARCHAR(150) NULL")
    conn.commit()
finally:
    cursor.close()
    conn.close()

print("Database migration completed.")
