"""PostgreSQL 连接管理"""
import psycopg2
from contextlib import contextmanager

def get_connection(db_name="global_military_monitor", user="postgres", host="localhost", port=5432, password=""):
    """获取数据库连接"""
    return psycopg2.connect(
        dbname=db_name,
        user=user,
        host=host,
        port=port,
        password=password
    )

@contextmanager
def get_cursor(db_name="global_military_monitor", user="postgres", host="localhost", port=5432, password=""):
    """上下文管理器：自动管理游标和提交"""
    conn = get_connection(db_name, user, host, port, password)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def test_connection():
    """测试数据库连接"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT version();")
            result = cur.fetchone()
            print(f"数据库连接成功: {result[0]}")
            return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()
