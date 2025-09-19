# from fastapi import APIRouter
#
# router = APIRouter()
#
# @router.get("/test")
# def test_endpoint():
#    return {"message": "Hello, Test!"}

"""Inspect database schema and print all tables with their columns.

   Args:
       engine: SQLAlchemy engine fixture (connected to test DB).

   Purpose:
       - Verifies that tables are created successfully.
       - Outputs table and column details (name, type, nullable, default).
       - Useful for debugging migrations and ORM model definitions.
   """
def test_show_tables(engine):
    from sqlalchemy import inspect
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    for table in tables:
        print(f"\n Tabela: {table}")
        columns = inspector.get_columns(table)
        for col in columns:
            col_name = col["name"]
            col_type = col["type"]
            nullable = col["nullable"]
            default = col.get("default")
            print(f"  - {col_name} ({col_type}), nullable={nullable}, default={default}")
