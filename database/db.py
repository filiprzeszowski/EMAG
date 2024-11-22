class Database:
    """Simple in-memory database for managing inventory and products."""
    def __init__(self):
        self.inventory = {}  # Inventory with parts
        self.products = []   # List of final products

    def add_part(self, name, quantity):
        """Adds a part to the inventory."""
        if name in self.inventory:
            self.inventory[name] += quantity
        else:
            self.inventory[name] = quantity

    def get_part(self, name):
        """Retrieves a part from inventory."""
        return self.inventory.get(name, 0)

    def add_product(self, product):
        """Adds a final product to the products list."""
        self.products.append(product)
