import os
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, db, _apps

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Database:
    def __init__(self):
        self.inventory = {}
        self.products = []
        self.initialize_firebase()

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK only if it hasn't been initialized."""
        try:
            database_url = os.getenv("FIREBASE_DATABASE_URL")
            if not database_url:
                raise ValueError("FIREBASE_DATABASE_URL is not set or could not be loaded")

            print("Loaded Firebase Database URL:", database_url)

            if not _apps:  # Check if Firebase is already initialized
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

                initialize_app(cred, {"databaseURL": database_url})
                print("Firebase initialized successfully.")
            else:
                print("Firebase already initialized. Skipping re-initialization.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")


    def verify_ean_in_firebase(self, ean):
        """Check if an EAN exists in Firebase."""
        try:
            ref = db.reference("ean_codes")
            ean_data = ref.child(ean).get()
            if ean_data:
                return ean_data.get("name")
            return None
        except Exception as e:
            print(f"Error verifying EAN in Firebase: {e}")
            raise

    def verify_product_ean_in_firebase(self, ean):
        """
        Checks if a product EAN exists in Firebase, at /product_ean_codes/<ean>.
        If found, returns the associated product name. Otherwise returns None.
        """
        try:
            ref = db.reference("product_ean_codes")
            ean_data = ref.child(ean).get()
            if ean_data:
                return ean_data.get("name")  # e.g. "Glowica2"
            return None
        except Exception as e:
            print(f"Error verifying product EAN in Firebase: {e}")
            raise

    def add_product_ean_to_firebase(self, ean, product_name):
        """
        Adds or updates an EAN => product_name mapping under /product_ean_codes/<ean>.
        Example path: /product_ean_codes/123 => {"name": "Glowica2"}
        """
        try:
            ref = db.reference(f"product_ean_codes/{ean}")
            ref.set({"name": product_name})
            print(f"Product EAN '{ean}' with name '{product_name}' added to Firebase.")
        except Exception as e:
            print(f"Error adding EAN '{ean}' to Firebase: {e}")
            raise


    def add_ean_to_firebase(self, ean, name):
        """Add a new EAN code to Firebase."""
        try:
            ref = db.reference(f"ean_codes/{ean}")
            ref.set({"name": name})
            print(f"EAN '{ean}' with name '{name}' added to Firebase.")
        except Exception as e:
            print(f"Error adding EAN '{ean}' to Firebase: {e}")
            raise

    # Inventory-related methods
    def add_part(self, name, quantity):
        """Adds a part to the inventory and syncs with Firebase."""
        if name in self.inventory:
            self.inventory[name] += quantity
        else:
            self.inventory[name] = quantity

        self.update_part_quantity(name, self.inventory[name])

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
                        "ean": value.get("ean"),
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

    def update_part_quantity(self, name, quantity_change):
        """Correctly adjust part quantity instead of overwriting."""
        try:
            ref = db.reference(f"inventory/{name}")
            current_quantity = ref.get() or 0  # Get current stock, default to 0
            new_quantity = current_quantity + quantity_change  # Apply adjustment

            if new_quantity < 0:
                new_quantity = 0  # Prevent negative values

            ref.set(new_quantity)  # Save updated quantity
            print(f"Part '{name}' updated to {new_quantity} in Firebase.")
        except Exception as e:
            print(f"Error updating part '{name}' in Firebase: {e}")

    
    # In db.py
    def update_product_in_firebase(self, product):
        try:
            product_name = product["name"]
            ref = db.reference("products")
            product_node = ref.child(product_name)
            if not product_node.get():
                print(f"[WARNING] No product named '{product_name}' in /products.")
                return

            # Update only the fields you want
            product_node.update({
                "quantity": product["quantity"],
                "parts": product.get("parts", {})
            })
            print(f"Updated product '{product_name}' => quantity={product['quantity']} in Firebase.")
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

    def load_inventory(self):
        """Load inventory from Firebase and print debug info."""
        ref = db.reference("inventory")
        inventory_data = ref.get()
        print("Loaded Inventory Data:", inventory_data)  # Debugging
        if isinstance(inventory_data, dict):
            return inventory_data
        return {}

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

    def sync_with_firebase(self):
        """Sync local data with Firebase."""
        try:
            self.load_parts()
            self.load_products()
            print("Data synchronized successfully with Firebase.")
        except Exception as e:
            print(f"Error during Firebase synchronization: {e}")
            raise

    def add_product_to_firebase(self, product):
        """
        Store the product at /products/<product_name>.
        Example path: /products/Glowica2
        """
        try:
            ref = db.reference("products")
            product_name = product["name"]  # e.g. "Glowica2"
            ref.child(product_name).set(product)
            print(f"Product '{product_name}' added to Firebase.")
        except Exception as e:
            print(f"Error adding product '{product_name}' to Firebase: {e}")
            raise


    def load_products(self):
        """
        Reads all products under /products and returns a list of dicts:
        [
        {
            "name": "<product_key>",
            "quantity": <int>,
            "parts": {...}
        },
        ...
        ]
        """
        ref = db.reference("products")
        products_data = ref.get()
        print("Loaded Products Data:", products_data)  # Debugging

        if isinstance(products_data, dict):
            # Each top-level key is the product's name
            return [
                {
                    "name": key,
                    "ean": value.get("ean"),
                    "quantity": value.get("quantity", 0),
                    "parts": value.get("parts", {})
                }
                for key, value in products_data.items()
            ]
        return []


    def update_product_in_firebase(self, product):
        """
        Locates /products/<product_name> and updates its 'quantity' and 'parts' fields.
        No more queries needed; we directly address the product name as the node key.
        """
        try:
            ref = db.reference("products")
            product_name = product["name"]
            product_node = ref.child(product_name)

            if not product_node.get():
                print(f"[WARNING] No product named '{product_name}' in /products.")
                return

            product_node.update({
                "quantity": product["quantity"],
                "parts": product.get("parts", {})
            })
            print(f"Updated product '{product_name}' => quantity={product['quantity']} in Firebase.")

        except Exception as e:
            print(f"Error updating product '{product['name']}' in Firebase: {e}")


    def delete_product(self, product_name):
        """
        Deletes the product at /products/<product_name> and returns any used parts to inventory.
        """
        ref = db.reference("products")
        product_node = ref.child(product_name)
        product_data = product_node.get()

        if not product_data:
            print(f"Product '{product_name}' not found in database.")
            return

        # Return used parts to inventory
        if "parts" in product_data and isinstance(product_data["parts"], dict):
            inventory_ref = db.reference("inventory")
            quantity = product_data.get("quantity", 0)

            for part_name, part_qty in product_data["parts"].items():
                if part_qty > 0:
                    current_stock = inventory_ref.child(part_name).get() or 0
                    new_stock = current_stock + (part_qty * quantity)
                    inventory_ref.child(part_name).set(new_stock)

        product_node.delete()
        print(f"Product '{product_name}' deleted from database, and parts returned to inventory.")

