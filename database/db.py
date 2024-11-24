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
        print(f"Firebase Key Path: {firebase_key_path}")
        if not os.path.exists(firebase_key_path):
            raise FileNotFoundError(f"The Firebase key file was not found at: {firebase_key_path}")

        if not firebase_key_path:
            raise FileNotFoundError("The Firebase key path is not set or the .env file is missing.")
        
        try:
            cred = credentials.Certificate(firebase_key_path)
            initialize_app(cred, {
                "databaseURL": "https://emag-14f01-default-rtdb.europe-west1.firebasedatabase.app/"
            })
            print("Firebase initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Firebase: {str(e)}")

    # Inventory-related methods
    def add_part(self, name, quantity):
        """Adds a part to the inventory and syncs with Firebase."""
        if name in self.inventory:
            self.inventory[name] += quantity
        else:
            self.inventory[name] = quantity

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
            else:
                print("No inventory data found in Firebase.")
            print("Inventory loaded successfully from Firebase.")
        except Exception as e:
            print(f"Error loading inventory from Firebase: {e}")
            raise

    def load_products_from_firebase(self):
        """Load products from Firebase, including parts."""
        try:
            ref = db.reference("products")
            products_data = ref.get()
            if products_data:
                self.products = [
                    {
                        "name": value.get("name"),
                        "quantity": value.get("quantity", 0),
                        "parts": value.get("parts", {}),
                    }
                    for value in products_data.values()
                ]
                print(f"Loaded {len(self.products)} products from Firebase.")
            else:
                print("No products data found in Firebase.")
        except Exception as e:
            print(f"Error loading products from Firebase: {e}")
            raise


    def update_part_in_firebase(self, name, quantity):
        """Update a specific part in Firebase."""
        try:
            ref = db.reference(f"inventory/{name}")
            ref.set(quantity)
            print(f"Part '{name}' updated in Firebase.")
        except Exception as e:
            print(f"Error updating part '{name}' in Firebase: {e}")
    
    def update_product_in_firebase(self, product):
        """Update an existing product in Firebase."""
        try:
            ref = db.reference("products")
            product_ref = ref.order_by_child("name").equal_to(product["name"]).get()
            for key in product_ref.keys():
                ref.child(key).update({"quantity": product["quantity"]})
            print(f"Product '{product['name']}' updated in Firebase.")
        except Exception as e:
            print(f"Error updating product '{product['name']}' in Firebase: {e}")

    # Product-related methods
    def add_product(self, product):
        """Adds a product to the products list and syncs with Firebase."""
        existing_product = next(
            (
                p
                for p in self.products
                if p["name"] == product["name"] and p["parts"] == product["parts"]
            ),
            None,
        )
        if existing_product:
            # If a product with the same name and same parts exists, update its quantity
            existing_product["quantity"] += product["quantity"]
            self.update_product_in_firebase(existing_product)
        else:
            # Add as a new product
            self.products.append(product)
            self.add_product_to_firebase(product)

    def load_products(self):
        """Load products from Firebase."""
        try:
            ref = db.reference("products")
            products_data = ref.get()
            if products_data:
                self.products = [product for product in products_data.values()]
            else:
                print("No products data found in Firebase.")
            print("Products loaded successfully from Firebase.")
        except Exception as e:
            print(f"Error loading products from Firebase: {e}")
            raise

    def load_parts(self):
        """Load parts (inventory) from Firebase."""
        try:
            ref = db.reference("inventory")
            inventory_data = ref.get()
            if inventory_data:
                self.inventory = inventory_data
            else:
                print("No parts data found in Firebase.")
            print("Parts loaded successfully from Firebase.")
        except Exception as e:
            print(f"Error loading parts from Firebase: {e}")
            raise

    def add_product_to_firebase(self, product):
        """Add a product to Firebase."""
        try:
            ref = db.reference("products")
            ref.push(product)
            print(f"Product '{product['name']}' added to Firebase.")
        except Exception as e:
            print(f"Error adding product '{product['name']}' to Firebase: {e}")
            raise

    def sync_with_firebase(self):
        """Sync local data with Firebase."""
        try:
            self.load_parts()
            self.load_products()
            print("Data synchronized successfully with Firebase.")
        except Exception as e:
            print(f"Error during Firebase synchronization: {e}")
            raise
