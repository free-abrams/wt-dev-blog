import pathlib
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = pathlib.Path.joinpath(pathlib.Path(__file__).parent)

class DevelopmentModel:
    """Development 表的基础模型封装"""

    def __init__(self, db_path: str = DB_PATH.joinpath("wt.sqlite3")):
        """初始化模型，连接到数据库"""
        self.db_path = db_path
        self._initialize_table()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _initialize_table(self):
        """初始化数据表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
    CREATE TABLE IF NOT EXISTS development(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT NOT NULL,
            title TEXT NOT NULL,
            poster TEXT NOT NULL,
            published_at TIMESTAMP,
            lang TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL,
            is_deleted INTEGER DEFAULT 0,
            UNIQUE(title,lang)  -- 确保记录唯一
        );""")

            # 创建更新触发器
            cursor.execute("""
                           CREATE TRIGGER IF NOT EXISTS update_development_timestamp
            AFTER
                           UPDATE ON development
                               FOR EACH ROW
                           BEGIN
                           UPDATE development
                           SET updated_at = CURRENT_TIMESTAMP
                           WHERE id = OLD.id;
                           END;
                           """)
            conn.commit()

    def create(self, link: str, title: str, poster: str,lang: str,
               published_at: Optional[datetime] = None) -> Optional[int]:
        """
        创建新记录
        :param lang: 语言
        :param link: 文章链接
        :param title: 文章标题
        :param poster: 发布者
        :param published_at: 发布时间
        :return: 新记录的ID或None(失败时)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                               INSERT INTO development (link, title, poster, lang, published_at)
                               VALUES (?, ?, ?, ?, ?)
                               """, (link, title, poster,lang,published_at))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"创建记录失败: {e} (可能是链接已存在)")
            return None

    def get_by_id(self, record_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """
        根据ID获取记录
        :param record_id: 记录ID
        :param include_deleted: 是否包含已删除的记录
        :return: 记录字典或None
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row  # 允许以字典方式访问
            cursor = conn.cursor()

            query = "SELECT * FROM development WHERE id = ?"
            params = [record_id]

            if not include_deleted:
                query += " AND is_deleted = 0"

            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有记录
        :param include_deleted: 是否包含已删除的记录
        :return: 记录列表
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM development"
            if not include_deleted:
                query += " WHERE is_deleted = 0"
            query += " ORDER BY created_at DESC"

            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def update(self, record_id: int, **kwargs) -> bool:
        """
        更新记录
        :param record_id: 要更新的记录ID
        :param kwargs: 要更新的字段和值
        :return: 是否成功
        """
        if not kwargs:
            return False

        allowed_fields = {'link', 'title', 'poster', 'published_at'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        # 处理datetime字段
        if 'published_at' in updates and isinstance(updates['published_at'], datetime):
            updates['published_at'] = updates['published_at'].isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(record_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                UPDATE development 
                SET {set_clause}
                WHERE id = ? AND is_deleted = 0
                """, values)
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"更新失败: {e} (可能是链接冲突)")
            return False

    def delete(self, record_id: int, hard_delete: bool = False) -> bool:
        """
        删除记录
        :param record_id: 要删除的记录ID
        :param hard_delete: 是否硬删除(True则永久删除，False为软删除)
        :return: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if hard_delete:
                    cursor.execute("DELETE FROM development WHERE id = ?", (record_id,))
                else:
                    cursor.execute("""
                                   UPDATE development
                                   SET is_deleted = 1,
                                       deleted_at = CURRENT_TIMESTAMP
                                   WHERE id = ?
                                     AND is_deleted = 0
                                   """, (record_id,))

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除失败: {e}")
            return False

    def search(self, keyword: str, field: str = 'title',
               include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        搜索记录
        :param keyword: 搜索关键词
        :param field: 搜索字段(title/poster)
        :param include_deleted: 是否包含已删除的记录
        :return: 匹配的记录列表
        """
        if field not in ['title', 'poster']:
            field = 'title'

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = f"SELECT * FROM development WHERE {field} LIKE ?"
            params = [f"%{keyword}%"]

            if not include_deleted:
                query += " AND is_deleted = 0"

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    def firstOrCreate(self, params:{}, value:{}):
        query = f"SELECT * FROM development WHERE title = ? AND lang = ? AND is_deleted = 0"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (params["title"],params["lang"]))
        exist = [dict(row) for row in cursor.fetchall()]

        if exist:
            return exist[0]
        else:
            return  self.create(**value)


# 使用示例
if __name__ == "__main__":
    model = DevelopmentModel()

    # 创建记录
    new_id = model.create(
        link="https://example.com/post1",
        title="Python SQLite教程",
        poster="张三",
        published_at=datetime.now()
    )
    print(f"新记录ID: {new_id}")

    # 查询记录
    record = model.get_by_id(new_id)
    print("获取的记录:", record)

    # 更新记录
    success = model.update(new_id, title="更新的Python教程", poster="李四")
    print(f"更新{'成功' if success else '失败'}")

    # 搜索记录
    results = model.search("Python")
    print("搜索结果:", results)

    # 软删除记录
    success = model.delete(new_id)
    print(f"删除{'成功' if success else '失败'}")

    # 获取所有活跃记录
    all_records = model.get_all()
    print("所有活跃记录:", all_records)