from models.product import Product, Part
from database.db import Database


class ProductController:
    def __init__(self):
        self.db = Database()
        self.available_parts = {
            "Wybierz": ["Rozmiar"],
            "Śrubki": ["M4", "M6", "M8"],
            "Nakrętki": ["M4", "M6", "M8"],
            "Podkładki": ["M4", "M6", "M8"],
            "Uszczelki gumowe": ["10mm", "20mm", "30mm"],
            "Flansze plastikowe": ["50mm", "100mm", "150mm"],
            "Flansze stalowe": ["50mm", "100mm", "150mm"],
            "Flansze ocynkowane": ["50mm", "100mm", "150mm"],
            "Haczyki": ["Małe", "Średnie", "Duże"],
        }

        self.available_products = {
        }
    
    def get_available_parts(self):
        """Zwraca listę dostępnych części."""
        return self.available_parts

    def get_available_products(self):
        """Zwraca listę dostępnych produktów."""
        return self.available_products

    def add_part_to_inventory(self, part_name, size, quantity):
        """Dodaje część do magazynu."""
        if part_name not in self.available_parts:
            print(f"Część '{part_name}' nie jest dostępna na liście.")
            return
        if size not in self.available_parts[part_name]:
            print(f"Rozmiar '{size}' nie jest dostępny dla części '{part_name}'.")
            return
        if quantity <= 0:
            print("Ilość musi być większa niż 0.")
            return

        part_key = f"{part_name} ({size})"
        self.db.add_part(part_key, quantity)
        print(f"Część '{part_key}' dodana do magazynu. Ilość: {quantity}.")

    def add_product(self, product_name, product_quantity, selected_parts):
        """Adds a product to the database with its associated parts."""
        # Check if product already exists
        for product in self.db.products:
            if product["name"] == product_name:
                print(f"Produkt '{product_name}' już istnieje.")
                return False

        # Deduct parts from inventory
        for part_name, part_quantity in product["parts"].items():
            required_quantity = delta * part_quantity
            available_quantity = self.controller.db.inventory.get(part_name, 0)

            if required_quantity > available_quantity:
                messagebox.showerror(
                    "Błąd",
                    f"Niewystarczająca ilość części '{part_name}' (potrzeba: {required_quantity}, dostępne: {available_quantity})."
                )
                return  # Stop product creation

            self.controller.db.inventory[part_name] -= required_quantity  # Deduct parts correctly


        # Add product to the database
        self.db.products.append({
            "name": product_name,
            "quantity": product_quantity,
            "parts": selected_parts,
        })
        print(f"Produkt '{product_name}' dodany pomyślnie.")
        return True


    def display_inventory(self):
        """Wyświetla aktualny stan magazynu z grupowaniem i ostrzeżeniami."""
        print("\nStan magazynowy:")
        if not self.db.inventory:
            print("Magazyn jest pusty.")
            return

        low_stock_parts = []
        for part, quantity in self.db.inventory.items():
            if quantity < 5:  # Przykład niskiego stanu
                low_stock_parts.append(part)
            print(f"{part}: {quantity}")

        if low_stock_parts:
            print("\nOstrzeżenie! Niski stan magazynowy dla:")
            for part in low_stock_parts:
                print(f"- {part}")

    def edit_part_quantity(self, part_name, size, delta):
        """Edytuje ilość części w magazynie."""
        part_key = f"{part_name} ({size})"
        if part_key in self.db.inventory:
            new_quantity = self.db.inventory[part_key] + delta
            if new_quantity < 0:
                print("Nie można zmniejszyć ilości poniżej zera.")
                return
            self.db.inventory[part_key] = new_quantity
            print(f"Ilość części '{part_key}' została zaktualizowana do {new_quantity}.")
        else:
            print(f"Część '{part_key}' nie istnieje w magazynie.")

    def remove_product(self, product_name, size):
        """Usuwa produkt z listy produktów."""
        product_key = f"{product_name} ({size})"
        for product in self.db.products:
            if product.name == product_key:
                self.db.products.remove(product)
                print(f"Produkt '{product_key}' został usunięty.")
                return
        print(f"Produkt '{product_key}' nie istnieje.")
