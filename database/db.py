import os
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, db

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Database:
    def __init__(self):
        self.inventory = {}
        self.products = []
        self.initialize_firebase()

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            database_url = os.getenv("FIREBASE_DATABASE_URL")
            if not database_url:
                raise ValueError("FIREBASE_DATABASE_URL is not set or could not be loaded")
            
            print("Loaded Firebase Database URL:", database_url)

            cred = credentials.Certificate({
                "type": os.getenv("FIREBASE_TYPE"),
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            })

            initialize_app(cred, {
                "databaseURL": database_url,
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
