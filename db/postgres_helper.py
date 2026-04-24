import os
import psycopg2

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "geoclip")
POSTGRES_USER = os.getenv("POSTGRES_USER", "geoclip_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "geoclip_pass")


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_results (
            id SERIAL PRIMARY KEY,
            task_type TEXT NOT NULL,
            input_value TEXT,
            status TEXT NOT NULL,
            result_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    connection.commit()
    cursor.close()
    connection.close()


def save_job_result(task_type, input_value, status, result_text):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO job_results (task_type, input_value, status, result_text)
        VALUES (%s, %s, %s, %s);
        """,
        (task_type, input_value, status, result_text)
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_job_results():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, task_type, input_value, status, result_text, created_at
        FROM job_results
        ORDER BY created_at DESC;
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "id": row[0],
            "task_type": row[1],
            "input_value": row[2],
            "status": row[3],
            "result_text": row[4],
            "created_at": str(row[5])
        }
        for row in rows
    ]