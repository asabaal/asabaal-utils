# SQL INJECTION VULNERABILITY - BAD CODE
import sqlite3

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        
    def query(self, sql):
        """Execute raw SQL query"""
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor

db = Database("products.db")

def search_products(query, filters):
    """Search products - VULNERABLE TO SQL INJECTION"""
    products = db.query("SELECT * FROM products WHERE active = 1")
    
    if query:
        # SQL INJECTION VULNERABILITY
        sql = "SELECT * FROM products WHERE active = 1 AND name LIKE '%" + query + "%'"
        products = db.query(sql)
    
    if filters.get('category'):
        # Another SQL injection vulnerability
        sql += " AND category = '" + filters['category'] + "'"
        products = db.query(sql)
        
    return products.fetchall()

def get_product(product_id):
    """Get single product - also vulnerable"""
    sql = "SELECT * FROM products WHERE id = " + str(product_id)
    return db.query(sql).fetchone()