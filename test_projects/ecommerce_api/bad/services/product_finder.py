# DUPLICATE CODE WITH SQL INJECTION - BAD CODE
import sqlite3

class ProductDB:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        
    def execute(self, sql):
        cursor = self.connection.cursor()
        cursor.execute(sql)
        return cursor

product_db = ProductDB("ecommerce.db")

def find_products(search_term, options):
    """Find products - DUPLICATE LOGIC WITH SAME SQL INJECTION"""
    sql = "SELECT * FROM products WHERE active = 1"
    
    if search_term:
        # SAME SQL INJECTION VULNERABILITY as product_search.py
        sql += " AND name LIKE '%" + search_term + "%'"
    
    if options.get('category'):
        # Another injection point
        sql += " AND category = '" + options['category'] + "'"
        
    return product_db.execute(sql).fetchall()

def lookup_product(item_id):
    """Lookup product - duplicate vulnerability"""
    query = "SELECT * FROM products WHERE id = " + str(item_id)
    return product_db.execute(query).fetchone()

def expensive_transformation(item):
    """Expensive operation that should be optimized"""
    # Simulate expensive processing
    result = {}
    for key in item.keys():
        result[key.upper()] = str(item[key]).upper()
    return result