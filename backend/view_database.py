"""
SQLite 数据库查看器
用于查看和分析 Vue3 RAG 项目的数据库
"""
import sqlite3
import sys
import io
from datetime import datetime

# Windows 控制台 UTF-8 支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def print_separator(char='=', length=80):
    print(char * length)

def show_tables(db_path):
    """显示所有表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print_separator()
    print("📊 数据库表列表")
    print_separator()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()

    for idx, table in enumerate(tables, 1):
        print(f"{idx}. {table[0]}")

    conn.close()
    return [t[0] for t in tables]

def show_table_schema(db_path, table_name):
    """显示表结构"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print_separator()
    print(f"📋 表结构: {table_name}")
    print_separator()

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    print(f"{'列ID':<6} {'列名':<20} {'类型':<15} {'非空':<6} {'默认值':<15} {'主键':<6}")
    print_separator('-')

    for col in columns:
        col_id, name, col_type, not_null, default_val, pk = col
        print(f"{col_id:<6} {name:<20} {col_type:<15} {'是' if not_null else '否':<6} {str(default_val or 'NULL'):<15} {'是' if pk else '否':<6}")

    conn.close()

def show_table_data(db_path, table_name, limit=10):
    """显示表数据"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取行数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_rows = cursor.fetchone()[0]

    print_separator()
    print(f"📄 表数据: {table_name} (总计 {total_rows} 行，显示前 {min(limit, total_rows)} 行)")
    print_separator()

    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
    rows = cursor.fetchall()

    if rows:
        # 获取列名
        columns = rows[0].keys()

        # 打印表头
        header = " | ".join([f"{col[:15]:<15}" for col in columns])
        print(header)
        print_separator('-')

        # 打印数据
        for row in rows:
            values = []
            for col in columns:
                val = row[col]
                if val is None:
                    val_str = "NULL"
                elif isinstance(val, (int, float)):
                    val_str = str(val)
                else:
                    val_str = str(val)[:15]
                values.append(f"{val_str:<15}")
            print(" | ".join(values))
    else:
        print("(空表)")

    conn.close()
    return total_rows

def show_indexes(db_path):
    """显示所有索引"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print_separator()
    print("🔍 数据库索引")
    print_separator()

    cursor.execute("""
        SELECT name, tbl_name, sql
        FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY tbl_name, name;
    """)
    indexes = cursor.fetchall()

    current_table = None
    for idx_name, tbl_name, sql in indexes:
        if current_table != tbl_name:
            current_table = tbl_name
            print(f"\n表: {tbl_name}")
            print("-" * 60)
        print(f"  索引: {idx_name}")
        if sql:
            print(f"  SQL: {sql}")

    conn.close()

def show_foreign_keys(db_path, table_name):
    """显示外键关系"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print_separator()
    print(f"🔗 外键关系: {table_name}")
    print_separator()

    cursor.execute(f"PRAGMA foreign_key_list({table_name});")
    fks = cursor.fetchall()

    if fks:
        print(f"{'ID':<4} {'列名':<20} {'引用表':<15} {'引用列':<15} {'ON UPDATE':<15} {'ON DELETE':<15}")
        print_separator('-')
        for fk in fks:
            fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
            print(f"{fk_id:<4} {from_col:<20} {ref_table:<15} {to_col:<15} {on_update:<15} {on_delete:<15}")
    else:
        print("(无外键)")

    conn.close()

def export_table_to_sql(db_path, table_name, output_file):
    """导出表的 INSERT 语句"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"-- 表: {table_name}\n")
        f.write(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 总行数: {len(rows)}\n\n")

        for row in rows:
            columns = list(row.keys())
            values = []
            for col in columns:
                val = row[col]
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                else:
                    values.append(str(val))

            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
            f.write(sql)

    conn.close()
    print(f"\n✅ 已导出 {len(rows)} 行数据到: {output_file}")

def main():
    db_path = r"C:\Users\tomyb\Desktop\vue3-rag-frontend2\backend\app\core\users.db"

    print("\n" + "="*80)
    print("🗄️  Vue3 RAG 项目数据库查看器")
    print("="*80)
    print(f"数据库文件: {db_path}\n")

    # 显示所有表
    tables = show_tables(db_path)

    print("\n")

    # 显示每个表的详细信息
    for table in tables:
        show_table_schema(db_path, table)
        print()
        total_rows = show_table_data(db_path, table, limit=5)
        print()
        show_foreign_keys(db_path, table)
        print("\n")

    # 显示索引
    show_indexes(db_path)

    print("\n" + "="*80)
    print("📊 数据库统计")
    print("="*80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"表 {table:<20}: {count:>6} 行")

    conn.close()

    print("\n" + "="*80)
    print("✨ 查看完成！")
    print("="*80)

    # 可选：导出 SQL
    print("\n是否要导出表的 SQL 语句？")
    print("1. 导出所有表")
    print("2. 导出指定表")
    print("3. 跳过")

    try:
        choice = input("\n请选择 (1-3): ").strip()

        if choice == '1':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            for table in tables:
                output_file = f"{table}_{timestamp}.sql"
                export_table_to_sql(db_path, table, output_file)
        elif choice == '2':
            print(f"\n可用的表: {', '.join(tables)}")
            table_name = input("请输入表名: ").strip()
            if table_name in tables:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"{table_name}_{timestamp}.sql"
                export_table_to_sql(db_path, table_name, output_file)
            else:
                print("❌ 表不存在")
    except KeyboardInterrupt:
        print("\n\n程序已取消")

if __name__ == "__main__":
    main()
