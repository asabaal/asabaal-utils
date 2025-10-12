from typing import List, Dict, Optional
from ..models.product import Product

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.products = []
        
    def query(self, model_class):
        return MockQuery(self.products, model_class)
        
    def add(self, obj):
        self.products.append(obj)
        
    def commit(self):
        pass
        
    def refresh(self, obj):
        pass

class MockQuery:
    def __init__(self, data, model_class):
        self.data = [item for item in data if isinstance(item, model_class)]
        self.filters = []
        
    def filter(self, condition):
        # Simple mock filter - in real implementation this would handle SQLAlchemy conditions
        if hasattr(condition, '__call__'):
            self.data = [item for item in self.data if condition(item)]
        return self
        
    def ilike(self, pattern):
        # Mock ilike functionality
        def contains_pattern(item):
            if hasattr(item, 'name'):
                search_term = pattern.replace('%', '')
                return search_term.lower() in item.name.lower()
            return False
        return contains_pattern
        
    def limit(self, count):
        self.data = self.data[:count]
        return self
        
    def first(self):
        return self.data[0] if self.data else None
        
    def all(self):
        return self.data

class ProductService:
    def __init__(self, db: MockDatabase):
        self.db = db
        
    def search_products(self, query: str, filters: Dict[str, any]) -> List[Product]:
        """Search products with filters"""
        base_query = self.db.query(Product)
        
        # Filter active products
        base_query = base_query.filter(lambda p: p.is_active)
        
        if query and query.strip():
            search_term = query.strip().lower()
            base_query = base_query.filter(lambda p: search_term in p.name.lower())
        
        if filters.get('category'):
            base_query = base_query.filter(lambda p: p.category == filters['category'])
            
        if filters.get('min_price'):
            base_query = base_query.filter(lambda p: p.price >= filters['min_price'])
            
        if filters.get('max_price'):
            base_query = base_query.filter(lambda p: p.price <= filters['max_price'])
            
        return base_query.limit(50).all()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get single product by ID"""
        products = self.db.query(Product).filter(lambda p: p.id == product_id).all()
        return products[0] if products else None
    
    def create_product(self, product_data: Dict[str, any]) -> Product:
        """Create new product with validation"""
        required_fields = ['name', 'price', 'category']
        for field in required_fields:
            if field not in product_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Generate a simple ID
        new_id = len(self.db.products) + 1
        
        product = Product(
            id=new_id,
            name=product_data['name'],
            description=product_data.get('description', ''),
            price=float(product_data['price']),
            category=product_data['category']
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product