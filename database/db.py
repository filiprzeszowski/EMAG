import firebase_admin
from firebase_admin import credentials, db
import os

class Database:
    """Database class for managing inventory and products with Firebase support."""

    def __init__(self):
        self.inventory = {}  # Inventory with parts
        self.products = []   # List of final products

        # Initialize Firebase connection
        self.initialize_firebase()


    def initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        firebase_key_path = os.path.join(os.path.dirname(__file__), 'firebase_key.json')
        try:
            cred = credentials.Certificate(firebase_key_path)  # Replace with your Firebase key path
            firebase_admin.initialize_app(cred, {
                "databaseURL": "https://emag-14f01-default-rtdb.europe-west1.firebasedatabase.app/"  # Replace with your Firebase database URL
            })
        except Exception as e:
            print(f"Error initializing Firebase: {e}")

    # Inventory-related methods
    def add_part(self, name, quantity):
        """Adds a part to the inventory and syncs with Firebase."""
        if name in self.inventory:
            self.inventory[name] += quantity
        else:
            self.inventory[name] = quantity

        # Update Firebase
        self.update_part_in_firebase(name, self.inventory[name])

    def get_part(self, name):
        """Retrieves a part from inventory."""
        return self.inventory.get(name, 0)

    def load_inventory_from_firebase(self):
        """Load inventory from Firebase."""
        try:
            ref = db.reference("inventory")
            inventory_data = ref.get()
            if inventory_data:
                self.inventory = inventory_data
            print("Inventory loaded from Firebase.")
        except Exception as e:
            print(f"Error loading inventory from Firebase: {e}")

    def update_part_in_firebase(self, name, quantity):
        """Update a specific part in Firebase."""
        try:
            ref = db.reference(f"inventory/{name}")
            ref.set(quantity)
            print(f"Part '{name}' updated in Firebase.")
        except Exception as e:
            print(f"Error updating part '{name}' in Firebase: {e}")

    # Product-related methods
    def add_product(self, product):
        """Adds a product to the products list and syncs with Firebase."""
        self.products.append(product)

        # Update Firebase
        self.add_product_to_firebase(product)

    def load_products_from_firebase(self):
        """Load products from Firebase."""
        try:
            ref = db.reference("products")
            products_data = ref.get()
            if products_data:
                self.products = [product for product in products_data.values()]
            print("Products loaded from Firebase.")
        except Exception as e:
            print(f"Error loading products from Firebase: {e}")

    def add_product_to_firebase(self, product):
        """Add a product to Firebase."""
        try:
            ref = db.reference("products")
            ref.push(product)
            print(f"Product '{product['name']}' added to Firebase.")
        except Exception as e:
            print(f"Error adding product '{product['name']}' to Firebase: {e}")

    def sync_with_firebase(self):
        """Sync local data with Firebase."""
        self.load_inventory_from_firebase()
        self.load_products_from_firebase()
