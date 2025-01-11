# Import necessary modules
import tkinter as tk
from utils.update_logic import *
from controllers.product_controller import *
from tkinter import ttk, messagebox, simpledialog
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class EMAGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EMAG - Zarzadzanie Magazynem")
        self.root.state("zoomed")
        self.controller = ProductController()  # Assuming it's imported

        # Set up styles
        self.style = ttkb.Style("cosmo")
        self.root.configure(bg="#F5F5F5")

        # Create UI components
        self.create_header()
        self.create_layout()
        self.create_status_bar()

        # Initial data load
        self.update_parts_list()
        self.update_products_list()

    def create_header(self):
        """Create the application header."""
        header = ttkb.Frame(self.root, padding=10, bootstyle="primary")
        header.pack(side=TOP, fill=X)

        ttkb.Label(
            header,
            text="EMAG - Zarzadzanie Magazynem",
            font=("Arial", 20, "bold"),
            bootstyle="inverse-primary",
        ).pack(side=LEFT, padx=20)

        ttkb.Button(
            header,
            text="Ciemny motyw",
            bootstyle="secondary-outline",
            command=self.toggle_dark_mode
        ).pack(side=RIGHT, padx=10)

        ttkb.Button(
            header,
            text="Zgloś problem",
            bootstyle="info-outline",
            command=self.show_feedback_form
        ).pack(side=RIGHT, padx=10)

        ttkb.Button(
            header,
            text="Sprawdź aktualizacje",
            bootstyle="success-outline",
            command=self.check_for_updates
        ).pack(side=RIGHT, padx=10)

    def create_layout(self):
        """Create the main application layout."""
        main_frame = ttkb.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)

        # Sidebar
        self.sidebar = ttkb.Frame(main_frame, width=200, bootstyle="secondary")
        self.sidebar.pack(side=LEFT, fill=Y)

        buttons = [
            ("Dodaj Części", self.show_add_part_menu),
            ("Edytuj Części", self.show_edit_part_menu),
            ("Dodaj Produkt", self.show_add_product_menu),
            ("Edytuj Produkt", self.show_edit_product_menu),
            ("Wizualizacja", self.show_visualization),
            ("Dostawy", self.show_bulk_delivery_menu),
        ]

        for text, command in buttons:
            ttkb.Button(
                self.sidebar,
                text=text,
                bootstyle="flat",  # Neutral style
                command=command,
            ).pack(fill=X, pady=5, padx=10)

        # Main content
        self.main_content = ttkb.Notebook(main_frame)
        self.main_content.pack(side=LEFT, fill=BOTH, expand=True)

        # Right frame for dynamic content
        self.right_frame = ttkb.Frame(main_frame)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Parts tab
        self.parts_tab = ttkb.Frame(self.main_content)
        self.main_content.add(self.parts_tab, text="Części")
        
        self.parts_list = self.create_treeview(
            self.parts_tab, ["name", "quantity"]
        )
        self.parts_list.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Products tab
        self.products_tab = ttkb.Frame(self.main_content)
        self.main_content.add(self.products_tab, text="Produkty")
        
        self.products_list = self.create_treeview(
            self.products_tab, ["name", "quantity", "parts"]
        )
        self.products_list.pack(fill=BOTH, expand=True, padx=10, pady=10)


    def create_treeview(self, parent, columns):
        """Create a styled Treeview for data display."""
        tree = ttkb.Treeview(parent, columns=columns, show="headings", bootstyle="info")
        for col in columns:
            tree.heading(col, text=col.capitalize())
            tree.column(col, width=150, anchor=CENTER)
        return tree

    def create_status_bar(self):
        """Create a status bar at the bottom."""
        self.status_bar = ttkb.Label(
            self.root, text="Gotowy", anchor=W, bootstyle="secondary", padding=5
        )
        self.status_bar.pack(side=BOTTOM, fill=X)

    def toggle_dark_mode(self):
        """Toggle dark/light mode."""
        theme = "darkly" if self.style.theme_use() == "cosmo" else "cosmo"
        self.style.theme_use(theme)

    def update_parts_list(self):
        """Update the parts list in the Treeview with Firebase data."""
        try:
            # Load inventory from Firebase
            self.controller.db.load_inventory_from_firebase()

            # Debug: Print inventory data
            print("Inventory items:", list(self.controller.db.inventory.items()))

            # Clear the treeview
            self.parts_list.delete(*self.parts_list.get_children())

            # Populate the treeview
            for i, (part, quantity) in enumerate(self.controller.db.inventory.items()):
                tag = "oddrow" if i % 2 == 0 else "evenrow"

                # Debug: Print each item being inserted
                print(f"Inserting part: {part}, quantity: {quantity}")

                self.parts_list.insert("", "end", values=(part, quantity), tags=(tag,))
            
            # Force UI update
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error loading inventory: {e}")
            messagebox.showerror("Error", "Could not load inventory.")

    def update_products_list(self):
        """Update the products list in the TreeView."""
        try:
            # Load products from Firebase
            self.controller.db.load_products_from_firebase()

            # Debug: Print raw products data
            print("Raw products:", self.controller.db.products)

            # Combine products with the same name and identical parts
            combined_products = {}
            for product in self.controller.db.products:
                key = (product["name"], frozenset(product["parts"].items()))
                if key in combined_products:
                    combined_products[key]["quantity"] += product["quantity"]
                else:
                    combined_products[key] = {
                        "name": product["name"],
                        "quantity": product["quantity"],
                        "parts": product["parts"],
                    }

            # Debug: Print combined products
            print("Combined products:", combined_products)

            # Clear the TreeView
            self.products_list.delete(*self.products_list.get_children())

            # Populate the TreeView
            for i, product in enumerate(combined_products.values()):
                parts_str = ", ".join(
                    [f"{part} ({qty})" for part, qty in product["parts"].items()]
                )

                # Debug: Print each product being inserted
                print(f"Inserting product: {product['name']}, quantity: {product['quantity']}, parts: {parts_str}")

                self.products_list.insert(
                    "",
                    "end",
                    values=(product["name"], product["quantity"], parts_str),
                )
            
            # Force UI update
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating products list: {e}")
            messagebox.showerror("Error", "Could not update products list.")

    def show_add_part_menu(self):
        # Repack right_frame if hidden
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Clear previous widgets
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        ttkb.Label(
            self.right_frame,
            text="Dodaj Część",
            font=("Arial", 18, "bold"),
            bootstyle="flat",
        ).pack(pady=10)

        form_frame = ttkb.Labelframe(
            self.right_frame,
            text="Formularz",
            bootstyle="secondary",
            padding=20,
        )
        form_frame.pack(fill=BOTH, padx=20, pady=20, expand=True)

        part_name_var = tk.StringVar()
        available_parts = self.controller.get_available_parts()
        if not available_parts:
            messagebox.showerror("Błąd", "Brak dostępnych części.")
            return

        ttkb.Label(form_frame, text="Wybierz część:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=10)
        part_name_var.set(next(iter(available_parts), ""))
        ttkb.OptionMenu(form_frame, part_name_var, *available_parts.keys()).grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        size_var = tk.StringVar()
        size_menu = ttkb.OptionMenu(form_frame, size_var, "")
        size_menu.grid(row=1, column=1, pady=10, padx=10, sticky="ew")

        def update_size_menu(*args):
            selected_part = part_name_var.get()
            sizes = available_parts.get(selected_part, [])
            if sizes:
                size_var.set(sizes[0])
                menu = size_menu["menu"]
                menu.delete(0, "end")
                for size in sizes:
                    menu.add_command(label=size, command=lambda value=size: size_var.set(value))
            else:
                size_var.set("")
                menu = size_menu["menu"]
                menu.delete(0, "end")

        part_name_var.trace_add("write", update_size_menu)
        update_size_menu()

        ttkb.Label(form_frame, text="Podaj ilość:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=10)
        quantity_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=quantity_var).grid(row=2, column=1, sticky="ew", pady=10, padx=10)

        def add_part():
            part_name = part_name_var.get()
            size = size_var.get()
            quantity = quantity_var.get()
            if not quantity.isdigit() or int(quantity) <= 0:
                messagebox.showerror("Błąd", "Podaj poprawną ilość.")
                return
            full_part_name = f"{part_name} ({size})"
            self.controller.db.add_part(full_part_name, int(quantity))
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Część '{full_part_name}' została dodana.")

        ttkb.Button(
            self.right_frame,
            text="Dodaj",
            bootstyle="success",
            command=add_part,
        ).pack(pady=20, padx=20, fill="x")

    def show_edit_part_menu(self):
        # Repack right_frame if hidden
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Clear previous widgets
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        ttkb.Label(
            self.right_frame,
            text="Edytuj Część",
            font=("Arial", 18, "bold"),
            bootstyle="flat",
        ).pack(pady=10)

        form_frame = ttkb.Labelframe(
            self.right_frame,
            text="Formularz",
            bootstyle="secondary",
            padding=20,
        )
        form_frame.pack(fill=BOTH, padx=20, pady=20, expand=True)

        # Use consistent geometry manager (grid) inside form_frame
        ttkb.Label(form_frame, text="Wybierz część:", font=("Arial", 12)).grid(
            row=0, column=0, sticky="w", pady=10
        )
        part_name_var = tk.StringVar()
        available_parts = self.controller.db.inventory.keys()
        part_name_var.set(next(iter(available_parts), ""))  # Set default part if available
        ttkb.OptionMenu(form_frame, part_name_var, *available_parts).grid(
            row=0, column=1, pady=10, padx=10, sticky="ew"
        )

        ttkb.Label(form_frame, text="Zmień ilość (+/-):", font=("Arial", 12)).grid(
            row=1, column=0, sticky="w", pady=10
        )
        delta_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=delta_var).grid(
            row=1, column=1, pady=10, padx=10, sticky="ew"
        )

        def edit_part():
            part_name = part_name_var.get()
            try:
                delta = int(delta_var.get())
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną liczbę.")
                return
            current_quantity = self.controller.db.get_part(part_name)
            new_quantity = current_quantity + delta
            if new_quantity < 0:
                messagebox.showerror("Błąd", "Nowa ilość nie może być ujemna.")
                return
            self.controller.db.add_part(part_name, new_quantity)
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Ilość dla '{part_name}' została zaktualizowana.")

        ttkb.Button(
            form_frame,
            text="Zapisz zmiany",
            bootstyle="success",
            command=edit_part,
        ).grid(row=2, column=0, columnspan=2, pady=10, padx=20, sticky="ew")


    def show_add_product_menu(self):
        # Repack right_frame if hidden
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Clear previous widgets
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        ttkb.Label(
            self.right_frame,
            text="Dodaj Produkt",
            font=("Arial", 18, "bold"),
            bootstyle="flat",
        ).pack(pady=10)

        form_frame = ttkb.Labelframe(
            self.right_frame,
            text="Formularz",
            bootstyle="secondary",
            padding=20,
        )
        form_frame.pack(fill=BOTH, padx=20, pady=20, expand=True)

        ttkb.Label(form_frame, text="Nazwa Produktu:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=10)
        product_name_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=product_name_var).grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        ttkb.Label(form_frame, text="Ilość Produktów:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=10)
        product_quantity_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=product_quantity_var).grid(row=1, column=1, pady=10, padx=10, sticky="ew")

        ttkb.Label(form_frame, text="Części:", font=("Arial", 12)).grid(row=2, column=0, sticky="nw", pady=10)
        parts_tree = ttkb.Treeview(
            form_frame, columns=("Część", "Dostępne", "Użyte"), show="headings", height=8
        )
        parts_tree.heading("Część", text="Część")
        parts_tree.heading("Dostępne", text="Dostępne")
        parts_tree.heading("Użyte", text="Użyte")
        parts_tree.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        # Configure grid weights for dynamic resizing
        form_frame.grid_rowconfigure(2, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)

        # Populate the parts list
        for part, quantity in self.controller.db.inventory.items():
            parts_tree.insert("", "end", values=(part, quantity, 0))

        def add_product():
            product_name = product_name_var.get()
            if not product_name:
                messagebox.showerror("Błąd", "Podaj nazwę produktu.")
                return
            try:
                quantity = int(product_quantity_var.get())
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną ilość.")
                return
            selected_parts = {}
            for item in parts_tree.get_children():
                part, available, used = parts_tree.item(item, "values")
                if int(used) > 0:
                    selected_parts[part] = int(used)
            self.controller.db.add_product(product_name, quantity, selected_parts)
            self.update_products_list()
            messagebox.showinfo("Sukces", f"Produkt '{product_name}' został dodany.")

        ttkb.Button(
            form_frame,
            text="Dodaj Produkt",
            bootstyle="success",
            command=add_product,
        ).grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

    def show_edit_product_menu(self):
        # Repack right_frame if hidden
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Clear previous widgets
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        # Title
        ttkb.Label(
            self.right_frame,
            text="Edytuj Produkt",
            font=("Arial", 18, "bold"),
            bootstyle="flat",
        ).pack(pady=10)

        # Form Frame
        form_frame = ttkb.Labelframe(
            self.right_frame,
            text="Formularz",
            bootstyle="secondary",
            padding=20,
        )
        form_frame.pack(fill=BOTH, padx=20, pady=20, expand=True)

        # Product Selection
        ttkb.Label(form_frame, text="Wybierz produkt:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=10)
        product_name_var = tk.StringVar()
        product_names = [product["name"] for product in self.controller.db.products]
        product_name_var.set(product_names[0] if product_names else "")
        ttkb.OptionMenu(form_frame, product_name_var, *product_names).grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        # Current Quantity Display
        ttkb.Label(form_frame, text="Ilość aktualna:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=10)
        current_quantity_label = ttkb.Label(form_frame, text="0", font=("Arial", 12))
        current_quantity_label.grid(row=1, column=1, pady=10, padx=10, sticky="w")

        # Update the current quantity dynamically based on product selection
        def update_current_quantity(*args):
            product_name = product_name_var.get()
            product = next((p for p in self.controller.db.products if p["name"] == product_name), None)
            current_quantity_label.config(text=str(product["quantity"]) if product else "0")

        product_name_var.trace_add("write", update_current_quantity)
        update_current_quantity()  # Initialize for the first product

        # Quantity Adjustment Input
        ttkb.Label(form_frame, text="Zmień ilość (+/-):", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=10)
        delta_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=delta_var).grid(row=2, column=1, pady=10, padx=10, sticky="ew")

        # Edit Button
        def edit_product():
            """Edit the selected product quantity."""
            product_name = product_name_var.get()
            try:
                delta = int(delta_var.get())
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną liczbę.")
                return

            product = next((p for p in self.controller.db.products if p["name"] == product_name), None)
            if not product:
                messagebox.showerror("Błąd", f"Produkt '{product_name}' nie istnieje.")
                return

            new_quantity = product["quantity"] + delta
            if new_quantity < 0:
                messagebox.showerror("Błąd", "Nowa ilość nie może być ujemna.")
                return

            if delta > 0:
                # Check for sufficient parts in inventory
                for part_name, part_quantity in product["parts"].items():
                    required_quantity = delta * part_quantity
                    available_quantity = self.controller.db.inventory.get(part_name, 0)
                    if required_quantity > available_quantity:
                        messagebox.showerror(
                            "Błąd",
                            f"Niewystarczająca ilość części '{part_name}' (potrzeba: {required_quantity}, dostępne: {available_quantity}).",
                        )
                        return

                # Deduct parts from inventory
                for part_name, part_quantity in product["parts"].items():
                    self.controller.db.inventory[part_name] -= delta * part_quantity

            elif delta < 0:
                # Ask if parts should be returned to inventory
                should_return_parts = messagebox.askyesno(
                    "Zwrot części",
                    "Czy chcesz zwrócić części do magazynu?",
                )
                if should_return_parts:
                    for part_name, part_quantity in product["parts"].items():
                        self.controller.db.inventory[part_name] += abs(delta) * part_quantity

            # Update product quantity
            product["quantity"] = new_quantity
            self.update_products_list()
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Ilość produktu '{product_name}' została zaktualizowana.")

        ttkb.Button(
            form_frame,
            text="Zapisz zmiany",
            bootstyle="success",
            command=edit_product,
        ).grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky="ew")


    def show_feedback_form(self):
        """Display a feedback form."""
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Zgloś opinie")
        feedback_window.geometry("600x500")

        ttkb.Label(
            feedback_window,
            text="Twoja opinia:",
            font=("Arial", 12, "bold")
        ).pack(pady=10, padx=10)

        feedback_text = tk.Text(feedback_window, wrap="word", height=10)
        feedback_text.pack(fill=BOTH, expand=True, padx=10, pady=10)

        category_var = tk.StringVar(value="Bug Report")
        ttkb.Label(
            feedback_window,
            text="Kategoria:",
            font=("Arial", 12)
        ).pack(pady=5)

        category_menu = ttkb.OptionMenu(
            feedback_window, category_var, "Bug Report", "Funkcjonalność", "Inne"
        )
        category_menu.pack(fill=X, padx=10, pady=5)

        ttkb.Button(
            feedback_window,
            text="Wyślij",
            bootstyle="success",
            command=lambda: self.send_feedback(category_var, feedback_text.get("1.0", "end").strip(), feedback_window)
        ).pack(pady=10)

    def show_visualization(self):
        """Display a visualization of inventory or product data."""
        visualization_window = tk.Toplevel(self.root)
        visualization_window.title("Wizualizacja Danych")
        visualization_window.geometry("800x600")

        ttkb.Label(
            visualization_window,
            text="Wizualizacja Danych Magazynowych",
            font=("Arial", 16, "bold"),
            bootstyle="primary"
        ).pack(pady=10)

        # Prepare data for visualization
        try:
            parts_data = self.controller.db.inventory.items()
            part_names = [part for part, qty in parts_data]
            part_quantities = [qty for part, qty in parts_data]

            # Create a bar chart
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(part_names, part_quantities, color="skyblue")
            ax.set_title("Stany Magazynowe Części")
            ax.set_xlabel("Części")
            ax.set_ylabel("Ilość")
            ax.tick_params(axis="x", rotation=45)

            # Embed the matplotlib figure in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=visualization_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=BOTH, expand=True, padx=10, pady=10)
            canvas.draw()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się załadować danych: {e}")

        # Close button
        ttkb.Button(
            visualization_window,
            text="Zamknij",
            bootstyle="danger-outline",
            command=visualization_window.destroy
        ).pack(pady=10)

    def show_bulk_delivery_menu(self):
        # Repack right_frame if hidden
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Clear previous widgets
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        # Title
        ttkb.Label(
            self.right_frame,
            text="Menu dostaw",
            font=("Arial", 18, "bold"),
            bootstyle="flat",
        ).pack(pady=10)

        # Main form frame
        form_frame = ttkb.Frame(self.right_frame, padding=10)
        form_frame.pack(fill=BOTH, padx=10, pady=10, expand=True)

        scanned_items = []

        # Table for displaying scanned EANs and quantities
        scanned_table = ttkb.Treeview(
            form_frame, columns=("EAN", "Name", "Quantity"), show="headings", height=8
        )
        scanned_table.heading("EAN", text="EAN")
        scanned_table.heading("Name", text="Name")
        scanned_table.heading("Quantity", text="Quantity")
        scanned_table.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Input fields for EAN and Quantity
        ttkb.Label(form_frame, text="Scan EAN:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ean_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=ean_var).grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ttkb.Label(form_frame, text="Quantity:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        quantity_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=quantity_var).grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        # Add part button
        def add_scanned_item():
            """Add scanned item to the table."""
            ean = ean_var.get()
            quantity = quantity_var.get()
            if not ean or not quantity.isdigit():
                messagebox.showerror("Error", "Invalid EAN or quantity.")
                return
            scanned_items.append((ean, int(quantity)))
            scanned_table.insert("", "end", values=(ean, "Pending Verification", quantity))
            ean_var.set("")
            quantity_var.set("")

        ttkb.Button(
            form_frame,
            text="Dodaj część",
            bootstyle="success",
            command=add_scanned_item,
        ).grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

        # Close delivery button
        def close_delivery():
            """Verify all scanned items and update Firebase."""
            for ean, quantity in scanned_items:
                name = self.controller.db.verify_ean_in_firebase(ean)
                if not name:
                    # Prompt user for part name
                    name = simpledialog.askstring("New EAN", f"Enter name for EAN: {ean}")
                    if name:
                        self.controller.db.add_ean_to_firebase(ean, name)
                    else:
                        messagebox.showerror("Error", f"Skipping EAN {ean}.")
                        continue
                # Add part to inventory
                self.controller.db.add_part(name, quantity)
            self.update_parts_list()
            messagebox.showinfo("Success", "Delivery processed successfully.")
            self.clear_right_frame()

        ttkb.Button(
            form_frame,
            text="Zamknij Dostawę",
            bootstyle="danger",
            command=close_delivery,
        ).grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

        # Configure grid weights for dynamic resizing
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_rowconfigure(0, weight=1)



    def check_for_updates(self):
        """Check for application updates."""
        current_version = "2.0.0"  # Replace with dynamic versioning logic
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
                            "Aktualizacja została pomyślnie zainstalowana. Uruchom ponownie aplikację."
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

    def clear_right_frame(self):
        """Clear all widgets from the right frame."""
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        self.right_frame.pack_forget()  # Hide the frame


    def hide_right_frame(self):
        """Hide the right frame when 'Close Menu' is clicked."""
        if hasattr(self, 'right_frame'):
            self.right_frame.pack_forget()  # Hide the frame


if __name__ == "__main__":
    root = ttkb.Window("EMAG", themename="cosmo")
    app = EMAGApp(root)
    root.mainloop()
