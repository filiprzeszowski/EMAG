import os
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, db

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

class Database:
    def __init__(self):
        self.inventory = {}
        self.products = []
        self.initialize_firebase()

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        firebase_key_path = os.getenv("FIREBASE_KEY_PATH")
        if not firebase_key_path:
            raise ValueError("FIREBASE_KEY_PATH is not set in the environment variables.")
        
        try:
            cred = credentials.Certificate(firebase_key_path)
            initialize_app(cred, {
                "databaseURL": "https://emag-14f01-default-rtdb.europe-west1.firebasedatabase.app/"  # Replace with your Firebase URL
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