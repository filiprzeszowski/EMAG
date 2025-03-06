import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from firebase_admin import db
from controllers.product_controller import ProductController
from database.db import Database

#
# Optional placeholders for update logic
#
def check_for_updates(current_version):
    """Placeholder for checking updates; return (is_available, latest_version, url)."""
    # Dummy example: no updates available
    return (False, "2.0.1", "http://example.com/update.zip")

def download_update(update_url):
    """Placeholder for download logic."""
    return None

def install_update(zip_path):
    """Placeholder for install logic."""
    return False

class EMAGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EMAG - Zarządzanie Magazynem")
        self.root.geometry("1200x700")

        # Controller and DB
        self.controller = ProductController()
        self.db = Database()  # This class interacts with Firebase

        # CustomTkinter settings
        ctk.set_appearance_mode("System")        # or "Dark", "Light"
        ctk.set_default_color_theme("dark-blue") # or any other theme

        # Create UI layout
        self.create_sidebar()
        self.create_main_content()
        self.create_status_bar()

        # Initial data load from Firebase
        # - update_parts_list() calls self.db.load_inventory()
        # - update_products_list() calls self.db.load_products()
        self.update_parts_list()
        self.update_products_list()

    # -------------------------------------------------------------------------
    #                           LAYOUT METHODS
    # -------------------------------------------------------------------------
    def create_sidebar(self):
        """Create a collapsible sidebar navigation menu."""
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=10)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, expand=False)

        ctk.CTkLabel(
            self.sidebar, text="EMAG Menu", font=("Arial", 18, "bold")
        ).pack(pady=10)

        menu_buttons = [
            ("Dashboard", self.show_dashboard),
            ("Dostawy części", self.show_delivery_menu),
            ("Edytuj Część", self.show_edit_part_form),
            ("Dodaj Produkt", self.show_add_product_form),
            ("Edytuj Produkt", self.show_edit_product_form),
            ("Wysyłka", self.show_orders_form),
            ("Raporty (Wizualizacja)", self.show_visualization),
            ("Zgłoś Problem", self.show_feedback_form),
            ("Sprawdź Aktualizacje", self.check_for_updates_button),
            ("Ustawienia", self.show_settings),
        ]

        for text, command in menu_buttons:
            ctk.CTkButton(
                self.sidebar, text=text, command=command
            ).pack(fill=tk.X, pady=5, padx=10)

    def create_main_content(self):
        """Create the main display area with a toggle for Parts & Products."""
        self.main_content = ctk.CTkFrame(self.root)
        self.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Toggle Switch for Parts/Products
        self.toggle_var = tk.StringVar(value="parts")
        toggle_frame = ctk.CTkFrame(self.main_content)
        toggle_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(toggle_frame, text="Widok:", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        ctk.CTkRadioButton(
            toggle_frame, text="Części", variable=self.toggle_var,
            value="parts", command=self.toggle_view
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkRadioButton(
            toggle_frame, text="Produkty", variable=self.toggle_var,
            value="products", command=self.toggle_view
        ).pack(side=tk.LEFT, padx=5)

        # Table Area
        self.tree_frame = ctk.CTkFrame(self.main_content)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Two frames for parts & products
        self.parts_tree = self.create_table(["Nazwa", "Ilość"])
        self.products_tree = self.create_table(["EAN", "Nazwa", "Ilość", "Części"])

        # Show default (parts view)
        self.toggle_view()

    def create_table(self, columns):
        """Create a table-like frame with column headers and a list frame."""
        container = ctk.CTkFrame(self.tree_frame)

        # Header
        header_frame = ctk.CTkFrame(container)
        header_frame.pack(fill=tk.X)

        for col in columns:
            ctk.CTkLabel(header_frame, text=col, font=("Arial", 12, "bold"), width=20).pack(side=tk.LEFT, padx=5)

        # This frame will hold rows
        list_frame = ctk.CTkFrame(container)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # We'll store the list_frame reference so we can populate it dynamically
        container.list_frame = list_frame
        return container

    def create_status_bar(self):
        """Create a status bar at the bottom of the UI."""
        self.status_bar = ctk.CTkLabel(self.root, text="Status: Gotowy", anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # -------------------------------------------------------------------------
    #                          PARTS/PRODUCTS TOGGLE
    # -------------------------------------------------------------------------
    def toggle_view(self):
        """Switch between Parts and Products view in the main content."""
        self.parts_tree.pack_forget()
        self.products_tree.pack_forget()

        if self.toggle_var.get() == "parts":
            self.parts_tree.pack(fill=tk.BOTH, expand=True)
            self.update_parts_list()
        else:
            self.products_tree.pack(fill=tk.BOTH, expand=True)
            self.update_products_list()

    # -------------------------------------------------------------------------
    #                         LOADING FROM DATABASE
    # -------------------------------------------------------------------------
    def update_parts_list(self):
        """Update the parts table by reloading from Firebase."""
        # Clear existing rows
        for widget in self.parts_tree.list_frame.winfo_children():
            widget.destroy()

        # Load from DB
        inventory = self.db.load_inventory()  # returns a dict from Firebase
        for part, quantity in inventory.items():
            row = ctk.CTkFrame(self.parts_tree.list_frame)
            row.pack(fill=tk.X)
            ctk.CTkLabel(row, text=part, width=20).pack(side=tk.LEFT, padx=5)
            ctk.CTkLabel(row, text=str(quantity), width=20).pack(side=tk.LEFT, padx=5)

    def update_products_list(self):
        """Update the products table by reloading from Firebase."""
        # Clear existing rows
        for widget in self.products_tree.list_frame.winfo_children():
            widget.destroy()

        products = self.db.load_products()  # returns list of product dicts from Firebase
        for product in products:
            # product typically: {"name": <>, "quantity": <>, "parts": {...}}
            parts_data = product.get("parts", {})
            parts_str = ", ".join([f"{p}({qty})" for p, qty in parts_data.items()])

            row = ctk.CTkFrame(self.products_tree.list_frame)
            row.pack(fill=tk.X)
            ctk.CTkLabel(row, text=product.get('ean', ''), width=20).pack(side=tk.LEFT, padx=5)
            ctk.CTkLabel(row, text=product.get('name', ''), width=50).pack(side=tk.LEFT, padx=5)
            ctk.CTkLabel(row, text=str(product.get('quantity', 0)), width=20).pack(side=tk.LEFT, padx=5)
            ctk.CTkLabel(row, text=parts_str, width=40).pack(side=tk.LEFT, padx=5)

    # -------------------------------------------------------------------------
    #                            SIDEBAR VIEWS
    # -------------------------------------------------------------------------
    def clear_main_content(self):
        """Remove everything from main_content except the toggle widget."""
        for widget in self.main_content.winfo_children():
            widget.pack_forget()

    def show_dashboard(self):
        """Show the same view as on initial startup (Parts/Products toggle)."""
        self.update_status("Dashboard: Przegląd magazynu")
        self.clear_main_content()

        # Re-create the toggle at the top
        toggle_frame = ctk.CTkFrame(self.main_content)
        toggle_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(toggle_frame, text="Widok:", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        ctk.CTkRadioButton(
            toggle_frame, text="Części",
            variable=self.toggle_var, value="parts",
            command=self.toggle_view
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkRadioButton(
            toggle_frame, text="Produkty",
            variable=self.toggle_var, value="products",
            command=self.toggle_view
        ).pack(side=tk.LEFT, padx=5)

        # Re-create the table area
        self.tree_frame = ctk.CTkFrame(self.main_content)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Two tables – one for parts, one for products
        self.parts_tree = self.create_table(["Nazwa", "Ilość"])
        self.products_tree = self.create_table(["EAN", "Nazwa", "Ilość", "Części"])

        # Force it to default to showing 'parts'
        self.toggle_var.set("parts")
        self.toggle_view()

    def show_inventory_view(self):
        """Switch back to normal 'Inventory' (parts/products) view."""
        self.update_status("Widok: Zarządzanie magazynem")
        self.clear_main_content()

        # Re-pack the toggle + table frames
        children = self.main_content.winfo_children()
        if not children:
            return

        toggle_frame, tree_frame = None, None
        for child in self.main_content.winfo_children():
            if isinstance(child, ctk.CTkFrame) and (toggle_frame is None):
                toggle_frame = child
            else:
                tree_frame = child

        if toggle_frame:
            toggle_frame.pack(fill=tk.X, pady=10)
        if tree_frame:
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Refresh the appropriate table
        self.toggle_view()

    # -------------------------------------------------------------------------
    #                           ADD / EDIT PARTS
    # -------------------------------------------------------------------------
    def show_add_part_form(self):
        self.update_status("Dodawanie nowej części")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Dodaj Część", font=("Arial", 18, "bold")).pack(pady=10)

        part_name_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Nazwa części:").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=part_name_var, width=300).pack(pady=5)

        quantity_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Ilość:").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=quantity_var, width=100).pack(pady=5)

        def add_part(self, name, quantity):
            """
            Adds 'quantity' units of 'name' to local inventory, 
            then sets the final total in Firebase (no second increment).
            """
            current_qty = self.inventory.get(name, 0)
            new_qty = current_qty + quantity
            self.inventory[name] = new_qty

            # Write that final absolute value to Firebase
            ref = db.reference("inventory")
            ref.child(name).set(new_qty)
            print(f"Part '{name}' updated to {new_qty} in Firebase.")


        ctk.CTkButton(frame, text="Dodaj", command=add_part).pack(pady=10)

    def show_edit_part_form(self):
        self.update_status("Edycja istniejącej części")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Edytuj Część", font=("Arial", 18, "bold")).pack(pady=10)

        # Reload inventory from Firebase
        inventory = self.db.load_inventory()
        part_options = list(inventory.keys())

        part_name_var = tk.StringVar()
        if part_options:
            part_name_var.set(part_options[0])

        ctk.CTkLabel(frame, text="Wybierz część:").pack(anchor="w", padx=5)
        if part_options:
            dropdown = ctk.CTkOptionMenu(frame, values=part_options, variable=part_name_var)
            dropdown.pack(pady=5)
        else:
            ctk.CTkLabel(frame, text="Brak części w bazie.").pack(pady=5)

        delta_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Zmień ilość (+/-):").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=delta_var, width=100).pack(pady=5)

        def edit_part():
            part_name = part_name_var.get()
            delta_str = delta_var.get().strip()
            try:
                delta = int(delta_str)
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną liczbę całkowitą.")
                return

            if part_name not in inventory:
                messagebox.showerror("Błąd", f"Część '{part_name}' nie istnieje.")
                return

            current_qty = inventory[part_name]
            new_qty = current_qty + delta
            if new_qty < 0:
                messagebox.showerror("Błąd", "Nowa ilość nie może być ujemna.")
                return

            self.db.update_part_quantity(part_name, delta)
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Ilość dla '{part_name}' zaktualizowana o {delta}.")

        ctk.CTkButton(frame, text="Zapisz zmiany", command=edit_part).pack(pady=10)

    # -------------------------------------------------------------------------
    #                          ADD / EDIT PRODUCTS
    # -------------------------------------------------------------------------
    def show_add_product_form(self):
        """
        Dodawanie nowego produktu przez EAN + określenie części (per item).
        If EAN is known, we just update quantity. If unknown, we create a new product 
        with the user’s chosen parts usage.
        """
        self.update_status("Dodawanie nowego produktu przez EAN")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Dodaj Produkt (EAN + Części)", font=("Arial", 18, "bold")).pack(pady=10)

        # ----- EAN Entry -----
        ean_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Kod EAN produktu:").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=ean_var, width=300).pack(pady=5)

        # ----- Quantity Entry -----
        quantity_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Ilość produktu:").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=quantity_var, width=100).pack(pady=5)

        # ----- Parts Usage Section -----
        ctk.CTkLabel(frame, text="Części składowe (użycie na 1 szt.):").pack(anchor="w", padx=5, pady=10)

        inventory = self.db.load_inventory()  # dict: {partName: quantityInStock, ...}
        parts_scroll_frame = ctk.CTkScrollableFrame(frame, width=400, height=200)
        parts_scroll_frame.pack(pady=5, fill=tk.X)

        # For each known part, let the user specify how many are needed PER product item
        parts_entries = {}
        for part_name, stock_qty in inventory.items():
            row = ctk.CTkFrame(parts_scroll_frame)
            row.pack(fill=tk.X)

            ctk.CTkLabel(row, text=f"{part_name} (Dost.: {stock_qty})").pack(side=tk.LEFT, padx=5)
            used_var = tk.StringVar(value="0")
            parts_entries[part_name] = used_var
            ctk.CTkEntry(row, textvariable=used_var, width=60).pack(side=tk.LEFT, padx=5)

        def add_or_update_product_via_ean():
            ean = ean_var.get().strip()
            q_str = quantity_var.get().strip()

            # Basic checks
            if not ean:
                messagebox.showerror("Błąd", "Podaj kod EAN.")
                return
            if not q_str.isdigit():
                messagebox.showerror("Błąd", "Podaj poprawną (całkowitą) ilość produktu.")
                return
            q_int = int(q_str)
            if q_int <= 0:
                messagebox.showerror("Błąd", "Ilość produktu musi być > 0.")
                return

            # Check if EAN is already in Firebase
            existing_name = self.db.verify_product_ean_in_firebase(ean)
            if existing_name:
                # This EAN is already associated with some product
                products = self.db.load_products()
                product_data = next((p for p in products if p["name"] == existing_name), None)
                if product_data:
                    # Just increase its quantity
                    old_qty = product_data["quantity"]
                    new_qty = old_qty + q_int
                    product_data["quantity"] = new_qty
                    self.db.update_product_in_firebase(product_data)

                    messagebox.showinfo(
                        "Sukces",
                        f"Ilość produktu '{existing_name}' zaktualizowana o {q_int}. "
                        f"Łącznie jest teraz {new_qty} szt."
                    )
                else:
                    # Edge case: the EAN is in ean_codes, but we have no product node. 
                    # We'll create it with quantity, ignoring parts usage (or ask user).
                    messagebox.showwarning("Info", f"EAN '{ean}' wskazuje na '{existing_name}', "
                                                "ale nie znaleziono produktu. Tworzenie nowego.")
                    new_product = {
                        "name": existing_name,
                        "quantity": q_int,
                        "parts": {},  # or gather from parts_entries if you want
                    }
                    self.db.add_product_to_firebase(new_product)
                    messagebox.showinfo("Sukces", f"Produkt '{existing_name}' utworzony z ilością {q_int}.")
            else:
                # EAN unknown -> ask for new product name
                new_name = simpledialog.askstring("Nowy produkt", f"Podaj nazwę produktu dla EAN: {ean}")
                if not new_name:
                    messagebox.showerror("Błąd", "Nie podano nazwy produktu. Anulowano.")
                    return

                # Build the 'parts usage' dict from user entries
                parts_usage = {}
                for part_name, var in parts_entries.items():
                    val_str = var.get().strip()
                    if val_str.isdigit():
                        per_item = int(val_str)
                        if per_item > 0:
                            parts_usage[part_name] = per_item

                # 1) Store the EAN => new_name in /product_ean_codes
                self.db.add_product_ean_to_firebase(ean, new_name)

                # 2) Create a brand-new product
                new_product = {
                    "name": new_name,
                    "quantity": q_int,
                    "parts": parts_usage,
                }
                self.db.add_product_to_firebase(new_product)
                messagebox.showinfo("Sukces", f"Utworzono nowy produkt '{new_name}' (EAN: {ean}), ilość: {q_int}.")

            # Finally, refresh product list & clear fields
            self.update_products_list()
            ean_var.set("")
            quantity_var.set("")
            # Optionally reset the parts usage fields to "0"
            for var in parts_entries.values():
                var.set("0")

        ctk.CTkButton(frame, text="Dodaj / Zaktualizuj przez EAN", command=add_or_update_product_via_ean).pack(pady=10)

    def show_edit_product_form(self):
        self.update_status("Edycja istniejącego produktu")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Edytuj Produkt", font=("Arial", 18, "bold")).pack(pady=10)

        # Reload from Firebase
        products = self.db.load_products()
        product_names = [p["name"] for p in products]

        product_var = tk.StringVar()
        if product_names:
            product_var.set(product_names[0])

        ctk.CTkLabel(frame, text="Wybierz produkt:").pack(anchor="w", padx=5)
        if product_names:
            dropdown = ctk.CTkOptionMenu(frame, values=product_names, variable=product_var)
            dropdown.pack(pady=5)
        else:
            ctk.CTkLabel(frame, text="Brak produktów w bazie.").pack(pady=5)

        current_qty_label = ctk.CTkLabel(frame, text="Ilość: 0")
        current_qty_label.pack(anchor="w", padx=5, pady=5)

        def update_current_quantity(*args):
            name = product_var.get()
            product = next((p for p in products if p["name"] == name), None)
            if product:
                current_qty_label.configure(text=f"Ilość: {product['quantity']}")
            else:
                current_qty_label.configure(text="Ilość: 0")

        product_var.trace_add("write", update_current_quantity)
        update_current_quantity()

        delta_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Zmień ilość (+/-):").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=delta_var, width=100).pack(pady=5)

        def save_changes():
            name = product_var.get()
            delta_str = delta_var.get().strip()

            try:
                delta = int(delta_str)
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną liczbę całkowitą.")
                return

            product = next((p for p in products if p["name"] == name), None)
            if not product:
                messagebox.showerror("Błąd", f"Nie znaleziono produktu '{name}'.")
                return

            new_quantity = product["quantity"] + delta
            if new_quantity < 0:
                messagebox.showerror("Błąd", "Nowa ilość nie może być ujemna.")
                return

            # If increasing quantity, check if we have enough parts
            if delta > 0:
                inventory = self.db.load_inventory()
                for part_name, part_qty in product["parts"].items():
                    required = delta * part_qty
                    available = inventory.get(part_name, 0)
                    if required > available:
                        messagebox.showerror(
                            "Błąd",
                            f"Niewystarczająca ilość części '{part_name}' "
                            f"(potrzeba {required}, dostępne {available})."
                        )
                        return
                # Deduct parts from inventory
                for part_name, part_qty in product["parts"].items():
                    self.db.update_part_quantity(part_name, -delta * part_qty)

            # If decreasing, optionally return parts
            # If decreasing quantity
            elif delta < 0:
                should_return = messagebox.askyesno("Zwrot części", "Zwrot części do magazynu?")
                if should_return:
                    for part_name, part_qty in product["parts"].items():
                        # part_qty is assumed to be how many of that part per 1 product item
                        # returned is how many total to return for the 'delta' items
                        returned = abs(delta) * part_qty
                        self.db.update_part_quantity(part_name, returned)


            # Update product quantity in Firebase
            product["quantity"] = new_quantity
            self.db.update_product_in_firebase(product)

            self.update_products_list()
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Ilość produktu '{name}' zaktualizowana.")


        ctk.CTkButton(frame, text="Zapisz zmiany", command=save_changes).pack(pady=10)

        def delete_product():
            name = product_var.get()
            if not name:
                return
            confirm = messagebox.askyesno("Potwierdzenie", f"Czy na pewno chcesz usunąć produkt '{name}'?")
            if confirm:
                self.db.delete_product(name)
                self.update_products_list()
                self.update_parts_list()
                messagebox.showinfo("Sukces", f"Produkt '{name}' został usunięty.")

        ctk.CTkButton(frame, text="Usuń Produkt", fg_color="red", command=delete_product).pack(pady=10)

    # -------------------------------------------------------------------------
    #                            DELIVERIES
    # -------------------------------------------------------------------------
    def show_delivery_menu(self):
        self.update_status("Menu dostaw")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Przetwarzanie dostaw (skanowanie EAN)", font=("Arial", 18, "bold")).pack(pady=10)

        # Table
        table_frame = ctk.CTkFrame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Headers
        header = ctk.CTkFrame(table_frame)
        header.pack(fill=tk.X)
        for col in ["EAN", "Name", "Quantity"]:
            ctk.CTkLabel(header, text=col, font=("Arial", 12, "bold"), width=20).pack(side=tk.LEFT, padx=5)

        # Body
        self.delivery_table_body = ctk.CTkFrame(table_frame)
        self.delivery_table_body.pack(fill=tk.BOTH, expand=True)

        self.scanned_items = []  # list of (ean, quantity)

        # Input fields
        input_frame = ctk.CTkFrame(frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ctk.CTkLabel(input_frame, text="Scan EAN:").pack(side=tk.LEFT, padx=5)
        self.ean_var = tk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.ean_var, width=150).pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(input_frame, text="Quantity:").pack(side=tk.LEFT, padx=5)
        self.qty_var = tk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.qty_var, width=60).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(input_frame, text="Dodaj", command=self.add_scanned_item).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(frame, text="Zamknij Dostawę", fg_color="red", command=self.close_delivery).pack(pady=10)

    def add_scanned_item(self):
        """Add scanned item to the internal table."""
        ean = self.ean_var.get().strip()
        qty_str = self.qty_var.get().strip()
        if not ean or not qty_str.isdigit():
            messagebox.showerror("Błąd", "Niepoprawny EAN lub ilość.")
            return
        qty = int(qty_str)
        if qty <= 0:
            messagebox.showerror("Błąd", "Ilość musi być większa od 0.")
            return

        self.scanned_items.append((ean, qty))

        row = ctk.CTkFrame(self.delivery_table_body)
        row.pack(fill=tk.X)
        ctk.CTkLabel(row, text=ean, width=20).pack(side=tk.LEFT, padx=5)
        ctk.CTkLabel(row, text="Pending Verification", width=20).pack(side=tk.LEFT, padx=5)
        ctk.CTkLabel(row, text=str(qty), width=20).pack(side=tk.LEFT, padx=5)

        self.ean_var.set("")
        self.qty_var.set("")

    def close_delivery(self):
        """Verify all scanned items and update inventory in Firebase."""
        for ean, quantity in self.scanned_items:
            name = self.db.verify_ean_in_firebase(ean)
            if not name:
                # Prompt user for a new EAN
                name = simpledialog.askstring("Nowy EAN", f"Podaj nazwę dla EAN: {ean}")
                if name:
                    self.db.add_ean_to_firebase(ean, name)
                else:
                    messagebox.showerror("Błąd", f"Pomijanie EAN {ean}.")
                    continue
            # Add part to inventory
            self.db.add_part(name, quantity)

        self.scanned_items.clear()
        self.update_parts_list()
        messagebox.showinfo("Sukces", "Dostawa przetworzona pomyślnie.")
        self.show_inventory_view()

    # -------------------------------------------------------------------------
    #           ORDERS (PACK & SHIP) - EXAMPLE OF REMOVING PRODUCTS
    # -------------------------------------------------------------------------
    def show_orders_form(self):
        """Demonstration: 'pack and ship' an order by reducing product qty, possibly removing it if 0."""
        self.update_status("Zamówienia (Pack & Ship)")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Zamówienie / Wysyłka", font=("Arial", 18, "bold")).pack(pady=10)

        # Load current products
        products = self.db.load_products()
        product_names = [p["name"] for p in products]

        product_var = tk.StringVar()
        if product_names:
            product_var.set(product_names[0])

        ctk.CTkLabel(frame, text="Wybierz produkt do wysyłki:").pack(anchor="w", padx=5)
        if product_names:
            dropdown = ctk.CTkOptionMenu(frame, values=product_names, variable=product_var)
            dropdown.pack(pady=5)
        else:
            ctk.CTkLabel(frame, text="Brak produktów w bazie.").pack(pady=5)

        order_qty_var = tk.StringVar()
        ctk.CTkLabel(frame, text="Ilość do wysłania:").pack(anchor="w", padx=5)
        ctk.CTkEntry(frame, textvariable=order_qty_var, width=100).pack(pady=5)

        def process_order():
            selected_name = product_var.get()
            qty_str = order_qty_var.get().strip()
            if not selected_name:
                messagebox.showerror("Błąd", "Wybierz produkt.")
                return
            if not qty_str.isdigit():
                messagebox.showerror("Błąd", "Podaj prawidłową ilość.")
                return

            order_qty = int(qty_str)
            if order_qty <= 0:
                messagebox.showerror("Błąd", "Ilość wysyłana musi być > 0.")
                return

            # Find product in our loaded list
            product_data = next((p for p in products if p["name"] == selected_name), None)
            if not product_data:
                messagebox.showerror("Błąd", f"Produkt '{selected_name}' nie istnieje w bazie.")
                return

            current_qty = product_data["quantity"]
            if order_qty > current_qty:
                messagebox.showerror("Błąd", f"Niewystarczający stan. Dostępne: {current_qty}.")
                return

            new_quantity = current_qty - order_qty
            product_data["quantity"] = new_quantity

            # If the product is fully used up
            if new_quantity == 0:
                confirm_delete = messagebox.askyesno(
                    "Potwierdzenie",
                    f"Produkt '{selected_name}' został całkowicie wyczerpany. Usunąć go z bazy?"
                )
                if confirm_delete:
                    self.db.delete_product(selected_name)
                    messagebox.showinfo("Sukces", f"Produkt '{selected_name}' usunięty z bazy.")
            else:
                # Update the product quantity
                self.db.update_product_in_firebase(product_data)
                messagebox.showinfo(
                    "Sukces",
                    f"Wysłano {order_qty} szt. produktu '{selected_name}'. Pozostało {new_quantity}."
                )

            self.update_products_list()
            self.show_orders_form()  # refresh the UI

        ctk.CTkButton(frame, text="Wystaw Zamówienie", command=process_order).pack(pady=10)

    # -------------------------------------------------------------------------
    #                           VISUALIZATION
    # -------------------------------------------------------------------------
    def show_visualization(self):
        """Show a bar chart of the current inventory."""
        self.update_status("Wizualizacja (Raporty)")
        self.clear_main_content()

        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Raport - Stan Magazynu", font=("Arial", 18, "bold")).pack(pady=10)

        try:
            inventory = self.db.load_inventory()
            parts = list(inventory.keys())
            quantities = list(inventory.values())

            fig, ax = plt.subplots(figsize=(6,4))
            ax.bar(parts, quantities, color="skyblue")
            ax.set_title("Stany Magazynowe")
            ax.set_ylabel("Ilość")
            ax.set_xlabel("Części")
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            canvas.draw()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wygenerować wykresu: {e}")

    # -------------------------------------------------------------------------
    #                          FEEDBACK FORM
    # -------------------------------------------------------------------------
    def show_feedback_form(self):
        self.update_status("Zgłoś opinię / problem")
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Zgłoś opinię")
        feedback_window.geometry("600x500")

        ctk.CTkLabel(feedback_window, text="Twoja opinia:", font=("Arial", 12, "bold")).pack(pady=10, padx=10)

        feedback_text = tk.Text(feedback_window, wrap="word", height=10)
        feedback_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        category_var = tk.StringVar(value="Bug Report")
        ctk.CTkLabel(feedback_window, text="Kategoria:", font=("Arial", 12)).pack(pady=5)

        ctk.CTkOptionMenu(feedback_window, values=["Bug Report", "Funkcjonalność", "Inne"], variable=category_var).pack(fill="x", padx=10, pady=5)

        def send_feedback():
            category = category_var.get()
            content = feedback_text.get("1.0", "end").strip()
            if not content:
                messagebox.showerror("Błąd", "Wpisz treść opinii.")
                return
            # Possibly send it to an API, email, or log it in Firebase
            messagebox.showinfo("Dziękujemy", f"Dziękujemy za zgłoszenie.\nKategoria: {category}\nTreść:\n{content}")
            feedback_window.destroy()

        ctk.CTkButton(feedback_window, text="Wyślij", command=send_feedback).pack(pady=10)

    # -------------------------------------------------------------------------
    #                        CHECK FOR UPDATES
    # -------------------------------------------------------------------------
    def check_for_updates_button(self):
        """Button handler for checking updates."""
        current_version = "2.0.0"
        is_update_available, latest_version, update_url = check_for_updates(current_version)
        if is_update_available:
            should_update = messagebox.askyesno(
                "Aktualizacje",
                f"Dostępna jest nowa wersja ({latest_version}). Czy chcesz zaktualizować?"
            )
            if should_update:
                update_zip = download_update(update_url)
                if update_zip:
                    if install_update(update_zip):
                        messagebox.showinfo(
                            "Sukces",
                            "Aktualizacja zainstalowana. Uruchom ponownie aplikację."
                        )
                    else:
                        messagebox.showerror(
                            "Błąd",
                            "Wystąpił problem podczas instalacji aktualizacji."
                        )
                else:
                    messagebox.showerror(
                        "Błąd",
                        "Nie udało się pobrać aktualizacji."
                    )
        else:
            messagebox.showinfo("Aktualizacje", "Masz najnowszą wersję aplikacji.")

    # -------------------------------------------------------------------------
    #                           SETTINGS
    # -------------------------------------------------------------------------
    def show_settings(self):
        self.update_status("Ustawienia aplikacji")
        self.clear_main_content()
        frame = ctk.CTkFrame(self.main_content)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Tutaj można dodać ustawienia (np. motyw).", font=("Arial", 14)).pack(pady=20)

    # -------------------------------------------------------------------------
    #                           STATUS UPDATER
    # -------------------------------------------------------------------------
    def update_status(self, message):
        self.status_bar.configure(text=f"Status: {message}")


def run_gui():
    root = ctk.CTk()
    root.title("EMAG")
    app = EMAGApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
