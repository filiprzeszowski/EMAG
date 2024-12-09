import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from controllers.product_controller import ProductController
import requests
from config.config import VERSION
import zipfile
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib, shutil
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *


class EMAGApp:
    def __init__(self, root):
        self.controller = ProductController()
        self.root = root
        self.root.title("EMAG - Zarządzanie magazynem")
        self.root.state("zoomed")
        self.dark_mode = True
        self.setup_styles()
        self.style.theme_use("darkly")
        self.create_header()
        self.create_layout()
        self.create_status_bar()
        self.check_for_updates()
        self.update_parts_list()
        self.update_products_list()

    def setup_styles(self):
        """Configure consistent theme styles"""
        self.style = ttkb.Style("cosmo")  # Modern theme
        self.root.configure(bg="#BEE9E8")  # Set primary app background

        # Global widget styles
        self.style.configure(
            "TLabel",
            background="#BEE9E8",  # Match main app background
            foreground="#1B4965",  # Text color
            font=("Arial", 12),
        )
        self.style.configure(
            "TButton",
            font=("Arial", 14, "bold"),
            background="#5FA8D3",
            foreground="white",
            borderwidth=1,
            padding=5,
        )
        self.style.configure(
            "Treeview",
            background="#CAE9FF",
            fieldbackground="#CAE9FF",
            foreground="#1B4965",
        )
        self.style.map(
            "TButton",
            background=[("active", "#CAE9FF")],  # Lighter blue on hover
            foreground=[("active", "#1B4965")],
        )
        self.style.configure(
            "TEntry",
            fieldbackground="#FFFFFF",  # Entry fields with a clean white background
            foreground="#1B4965",
        )

    def create_header(self):
        """Create a header with branding."""
        header = ttkb.Frame(self.root, bootstyle=PRIMARY, padding=10)
        header.pack(side=TOP, fill=X)

        ttkb.Label(
            header,
            text="EMAG - Zarządzanie magazynem",
            font=("Arial", 18, "bold"),
            anchor=CENTER,
            foreground="white",
        ).pack()

    def create_layout(self):
        """Create a clean and responsive layout with proportional adjustments."""
        # Main Frame
        self.main_frame = ttkb.Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Sidebar Menu
        self.menu_frame = ttkb.Frame(self.main_frame, width=200)
        self.menu_frame.pack(side=LEFT, fill=Y, padx=5)

        # Set menu background color using a valid approach
        menu_bg_color = "#1B4965"  # Unified background color
        self.menu_frame.configure(style="TFrame")
        self.style.configure(
            "TFrame",
            background=menu_bg_color,
        )

        # Menu Header
        ttkb.Label(
            self.menu_frame,
            text="Menu",
            font=("Arial", 16, "bold"),
            background=menu_bg_color,
            foreground="white",
            anchor="center",
        ).pack(pady=(10, 20))

        # Menu Buttons
        menu_buttons = [
            ("Dodaj Część", self.show_add_part_menu),
            ("Edytuj Część", self.show_edit_part_menu),
            ("Dodaj Produkt", self.show_add_product_menu),
            ("Edytuj Produkt", self.show_edit_product_menu),
        ]
        for text, command in menu_buttons:
            ttkb.Button(
                self.menu_frame,
                text=text,
                bootstyle="success-outline",
                command=command,
            ).pack(fill=X, pady=5)

        # Middle Section (Notebook)
        self.notebook_frame = ttkb.Frame(self.main_frame, padding=10, width=700)  # Increased width
        self.notebook_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

        self.notebook = ttkb.Notebook(self.notebook_frame)
        self.notebook.pack(fill=BOTH, expand=True)

        # Parts Tab
        self.parts_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.parts_tab, text="Części")
        self.parts_list = self.create_treeview(self.parts_tab, columns=("name", "quantity"))
        self.parts_list.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Products Tab
        self.products_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.products_tab, text="Produkty")
        self.products_list = self.create_treeview(
            self.products_tab, columns=("name", "quantity", "parts")
        )
        self.products_list.heading("parts", text="Części")
        self.products_list.column("parts", width=300)
        self.products_list.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Right Panel
        self.right_frame = ttkb.Frame(
            self.main_frame, padding=10, width=400  # Adjusted width
        )
        self.right_frame.pack(side=RIGHT, fill=BOTH, padx=10, pady=10)
        self.right_frame.pack_propagate(False)

    def create_treeview(self, parent, columns):
        """Create a styled treeview."""
        tree = ttkb.Treeview(parent, columns=columns, show="headings", style="Treeview")
        for col in columns:
            tree.heading(col, text=col.capitalize())
            tree.column(col, anchor=CENTER, width=150)
        return tree

    def create_status_bar(self):
        """Create a status bar."""
        self.status_bar = ttkb.Label(
            self.root,
            text="Gotowy",
            anchor=W,
            bootstyle=SECONDARY,
            padding=5,
        )
        self.status_bar.pack(side=BOTTOM, fill=X)

    def toggle_dark_mode(self):
        """Toggle dark/light mode."""
        self.dark_mode = not self.dark_mode
        theme = "darkly" if self.dark_mode else "litera"
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



    def create_header(self):
        """Create a modern and visually appealing header."""
        # Header Frame
        self.header = ttkb.Frame(self.root, padding=10, bootstyle="primary")
        self.header.pack(side="top", fill="x")

        # Application Title
        ttkb.Label(
            self.header,
            text="EMAG - Zarządzanie Magazynem",
            font=("Arial", 20, "bold"),
            bootstyle="inverse-primary",
            anchor="w",
        ).pack(side="left", padx=20)

        # Centered Placeholder or Logo
        self.logo_label = ttkb.Label(
            self.header,
            text="🔧",  # Replace with a logo icon or image if available
            font=("Arial", 20),
            bootstyle="inverse-primary",
        )
        self.logo_label.pack(side="left", padx=10)

        # Buttons Section (on the right)
        ttkb.Button(
            self.header,
            text="Zgłoś błąd",
            bootstyle="danger-outline",
            command=self.show_feedback_form,
        ).pack(side="right", padx=10)

        ttkb.Button(
            self.header,
            text="Sprawdź aktualizacje",
            bootstyle="success-outline",
            command=self.check_for_updates,
        ).pack(side="right", padx=10)

        self.dark_mode_button = ttkb.Button(
            self.header,
            text="Ciemny motyw",
            bootstyle="secondary-outline",
            command=self.toggle_dark_mode,
        )
        self.dark_mode_button.pack(side="right", padx=10)



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
        """Display the Add Part menu with improved styling and functionality."""
        self.clear_right_frame()

        # Title
        ttkb.Label(
            self.right_frame,
            text="Dodaj Część",
            font=("Arial", 18, "bold"),
            bootstyle="inverse-secondary",
            anchor="center",
        ).pack(pady=10)

        # Form Frame
        form_frame = ttkb.Labelframe(
            self.right_frame,
            text="Formularz",
            bootstyle="secondary",
            padding=20,
        )
        form_frame.pack(fill=BOTH, padx=20, pady=20, expand=True)

        # Part Selection
        ttkb.Label(form_frame, text="Wybierz część:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        part_name_var = tk.StringVar()
        available_parts = list(self.controller.get_available_parts().keys())
        part_name_var.set(available_parts[0])  # Default to the first part
        ttkb.OptionMenu(form_frame, part_name_var, *available_parts).grid(row=0, column=1, sticky="ew", pady=10, padx=10)

        # Size Selection
        ttkb.Label(form_frame, text="Wybierz rozmiar:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        size_var = tk.StringVar()
        size_menu = ttkb.OptionMenu(form_frame, size_var, "")  # Initially empty
        size_menu.grid(row=1, column=1, sticky="ew", pady=10, padx=10)

        # Populate sizes dynamically based on part selection
        def update_size_menu(*args):
            selected_part = part_name_var.get()
            sizes = self.controller.get_available_parts()[selected_part]
            size_var.set(sizes[0])  # Default to the first size
            menu = size_menu["menu"]
            menu.delete(0, "end")  # Clear existing menu items
            for size in sizes:
                menu.add_command(label=size, command=lambda value=size: size_var.set(value))

        part_name_var.trace_add("write", update_size_menu)  # Trigger when part changes

        # Trigger the size menu update for the initial selection
        update_size_menu()

        # Quantity Input
        ttkb.Label(form_frame, text="Podaj ilość:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        quantity_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=quantity_var, font=("Arial", 12)).grid(row=2, column=1, sticky="ew", pady=10, padx=10)

        # Add Button
        def add_part():
            """Add the part to inventory."""
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
        """Display the Edit Part menu."""
        self.clear_right_frame()

        # Set frame title
        ttkb.Label(
            self.right_frame,
            text="Edytuj Część",
            font=("Arial", 18, "bold"),
            bootstyle="inverse-secondary",
            anchor="center",
        ).pack(pady=20)

        # Create form frame
        form_frame = ttkb.Frame(self.right_frame, padding=10, bootstyle="secondary")
        form_frame.pack(fill="x", padx=20, pady=10)

        # Part Selection
        ttkb.Label(form_frame, text="Wybierz część:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=10, padx=5)
        part_name_var = tk.StringVar()
        available_parts = list(self.controller.db.inventory.keys())
        part_name_var.set(available_parts[0])
        ttkb.OptionMenu(form_frame, part_name_var, *available_parts).grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        # Quantity Change Input
        ttkb.Label(form_frame, text="Zmień ilość (+/-):", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=10, padx=5)
        delta_var = tk.StringVar()
        ttkb.Entry(form_frame, textvariable=delta_var, font=("Arial", 12)).grid(row=1, column=1, pady=10, padx=10, sticky="ew")

        # Edit Button
        def edit_part():
            """Edit the selected part quantity."""
            part_name = part_name_var.get()
            try:
                delta = int(delta_var.get())
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną liczbę dla zmiany ilości.")
                return
            new_quantity = self.controller.db.get_part(part_name) + delta
            self.controller.db.add_part(part_name, new_quantity)
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Część '{part_name}' została zaktualizowana.")

        ttkb.Button(
            self.right_frame,
            text="Zapisz Zmiany",
            bootstyle="success",
            command=edit_part,
        ).pack(pady=20, padx=20, fill="x")

    def show_add_product_menu(self):
        """Display the Add Product menu"""
        self.clear_right_frame()
        ttkb.Label(
            self.right_frame,
            text="Dodaj Produkt",
            font=("Arial", 14, "bold"),
            bootstyle="inverse",
        ).pack(pady=10)

        # Product Name Input
        tk.Label(self.right_frame, text="Nazwa Produktu:", font=("Arial", 12), bg="#f0f0f0").pack(anchor="w", padx=10)
        product_name_var = tk.StringVar(self.right_frame)
        product_name_entry = tk.Entry(self.right_frame, textvariable=product_name_var, font=("Arial", 12))
        product_name_entry.pack(fill="x", padx=10, pady=5)

        # Suggestions for Recently Added Products
        suggestions_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        suggestions_frame.pack(fill="x", padx=10)

        def update_suggestions(*args):
            """Updates suggestions for recently used product names."""
            for widget in suggestions_frame.winfo_children():
                widget.destroy()
            query = product_name_var.get().lower()
            suggestions = [
                name for name in self.controller.get_available_products()
                if query in name.lower()
            ]
            for suggestion in suggestions[:5]:  # Show top 5 matches
                btn = tk.Button(
                    suggestions_frame,
                    text=suggestion,
                    font=("Arial", 10),
                    bg="#e8e8e8",
                    command=lambda s=suggestion: product_name_var.set(s),
                )
                btn.pack(fill="x", pady=2)

        product_name_var.trace("w", update_suggestions)

        # Parts Selection
        tk.Label(self.right_frame, text="Wybierz Części:", font=("Arial", 12), bg="#f0f0f0").pack(anchor="w", padx=10, pady=5)
        parts_tree = ttk.Treeview(self.right_frame, columns=("name", "available", "quantity"), show="headings")
        parts_tree.heading("name", text="Część")
        parts_tree.heading("available", text="Dostępne")
        parts_tree.heading("quantity", text="Ilość")
        parts_tree.column("name", width=150)
        parts_tree.column("available", width=100, anchor="center")
        parts_tree.column("quantity", width=100, anchor="center")
        parts_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Populate Treeview with parts data
        for part_name, quantity in self.controller.db.inventory.items():
            parts_tree.insert("", "end", values=(part_name, quantity, 0))

        # Edit Quantity Functionality
        def edit_quantity(event):
            selected_item = parts_tree.selection()
            if not selected_item:
                return
            item = selected_item[0]
            values = parts_tree.item(item, "values")
            part_name = values[0]
            available = int(values[1])

            def apply_change():
                try:
                    quantity = int(quantity_var.get())
                    if quantity < 0 or quantity > available:
                        raise ValueError
                    parts_tree.item(item, values=(part_name, available, quantity))
                    edit_window.destroy()
                except ValueError:
                    messagebox.showerror("Błąd", "Podaj poprawną ilość (0 - dostępne).")

            # Quantity Edit Window
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edytuj Ilość")
            edit_window.geometry("300x150")
            tk.Label(edit_window, text=f"Część: {part_name}", font=("Arial", 12)).pack(pady=10)
            quantity_var = tk.StringVar(value=values[2])
            tk.Entry(edit_window, textvariable=quantity_var, font=("Arial", 12)).pack(pady=10)
            tk.Button(edit_window, text="Zapisz", command=apply_change).pack(pady=10)

        parts_tree.bind("<Double-1>", edit_quantity)

        # Product Quantity Input
        tk.Label(self.right_frame, text="Ilość Produktów:", font=("Arial", 12), bg="#f0f0f0").pack(anchor="w", padx=10, pady=5)
        product_quantity_var = tk.StringVar(self.right_frame)
        product_quantity_entry = tk.Entry(self.right_frame, textvariable=product_quantity_var, font=("Arial", 12))
        product_quantity_entry.pack(fill="x", padx=10, pady=5)

        # Add Product Functionality
        def add_product():
            """Add a product to the inventory."""
            product_name = product_name_var.get()
            if not product_name:
                messagebox.showerror("Błąd", "Podaj nazwę produktu.")
                return

            try:
                product_quantity = int(product_quantity_var.get())
                if product_quantity <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Błąd", "Podaj poprawną ilość produktów.")
                return

            # Gather selected parts
            selected_parts = {}
            for item in parts_tree.get_children():
                part_name, available, quantity = parts_tree.item(item, "values")
                quantity = int(quantity)
                if quantity > 0:
                    if quantity > int(available):
                        messagebox.showerror(
                            "Błąd",
                            f"Ilość części '{part_name}' przekracza dostępne {available}.",
                        )
                        return
                    selected_parts[part_name] = quantity

            if not selected_parts:
                messagebox.showerror("Błąd", "Wybierz przynajmniej jedną część.")
                return

            # Prevent duplicate product creation
            existing_product = next(
                (
                    p
                    for p in self.controller.db.products
                    if p["name"] == product_name and p["parts"] == selected_parts
                ),
                None,
            )
            if existing_product:
                messagebox.showerror(
                    "Błąd",
                    f"Produkt '{product_name}' z identycznymi częściami już istnieje."
                )
                return

            # Deduct the required parts from inventory
            for part_name, quantity_per_product in selected_parts.items():
                total_quantity_needed = quantity_per_product * product_quantity
                if self.controller.db.inventory.get(part_name, 0) < total_quantity_needed:
                    messagebox.showerror(
                        "Błąd",
                        f"Niewystarczająca ilość części '{part_name}' do utworzenia produktu.",
                    )
                    return

            for part_name, quantity_per_product in selected_parts.items():
                total_quantity_needed = quantity_per_product * product_quantity
                new_quantity = self.controller.db.inventory[part_name] - total_quantity_needed
                self.controller.db.inventory[part_name] = new_quantity
                self.controller.db.add_part(part_name, new_quantity)

            # Add product to Firebase
            product = {
                "name": product_name,
                "quantity": product_quantity,
                "parts": selected_parts,
            }
            self.controller.db.add_product(product)

            # Refresh the UI
            self.update_products_list()
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Produkt '{product_name}' został dodany.")


        ttkb.Button(
            self.right_frame,
            text="Dodaj",
            bootstyle="success",
            command=add_product,
        ).pack(pady=10, fill="x")

    def show_edit_product_menu(self):
        """Displays the Edit Product menu in the right panel."""
        self.clear_right_frame()
        
        ttkb.Label(
            self.right_frame,
            text="Edytuj Produkt",
            font=("Arial", 14, "bold"),
            bootstyle="inverse-secondary",
        ).pack(pady=10)

        # Product Selection
        ttkb.Label(
            self.right_frame,
            text="Wybierz produkt:",
            font=("Arial", 12),
        ).pack(anchor="w", padx=10)

        product_name_var = tk.StringVar(self.right_frame)

        if self.controller.db.products:
            product_name_var.set(self.controller.db.products[0]["name"])
            product_names = [product["name"] for product in self.controller.db.products]
        else:
            product_names = []

        product_menu = ttkb.OptionMenu(
            self.right_frame,
            product_name_var,
            product_names[0] if product_names else None,
            *product_names,
        )
        product_menu.pack(fill="x", padx=10, pady=5)

        # Quantity Adjustment
        ttkb.Label(
            self.right_frame,
            text="Zmień ilość (+/-):",
            font=("Arial", 12),
        ).pack(anchor="w", padx=10, pady=5)

        delta_entry = ttkb.Entry(self.right_frame, font=("Arial", 12))
        delta_entry.pack(fill="x", padx=10, pady=5)

        def edit_product():
            product_name = product_name_var.get()
            delta = delta_entry.get()

            # Validate input
            if not delta.lstrip("-").isdigit():
                messagebox.showerror("Błąd", "Podaj poprawną liczbę.")
                return

            delta = int(delta)
            product = next(
                (product for product in self.controller.db.products if product["name"] == product_name), None
            )
            if not product:
                messagebox.showerror("Błąd", f"Produkt '{product_name}' nie istnieje.")
                return

            if delta > 0:
                # Increase product quantity
                required_parts = product["parts"]
                for part_name, part_quantity in required_parts.items():
                    if self.controller.db.inventory.get(part_name, 0) < part_quantity * delta:
                        messagebox.showerror(
                            "Błąd",
                            f"Niewystarczająca ilość części '{part_name}'."
                        )
                        return

                # Deduct parts from inventory
                for part_name, part_quantity in required_parts.items():
                    self.controller.db.inventory[part_name] -= part_quantity * delta

                product["quantity"] += delta
                messagebox.showinfo("Sukces", f"Ilość produktu '{product_name}' została zwiększona o {delta}.")
            elif delta < 0:
                # Decrease product quantity
                if product["quantity"] + delta < 0:
                    messagebox.showerror("Błąd", "Ilość produktu nie może być ujemna.")
                    return

                should_return_parts = messagebox.askyesno(
                    "Zwrot części",
                    "Czy chcesz zwrócić części do magazynu?"
                )
                if should_return_parts:
                    # Return parts to inventory
                    required_parts = product["parts"]
                    for part_name, part_quantity in required_parts.items():
                        self.controller.db.inventory[part_name] += part_quantity * abs(delta)

                product["quantity"] += delta
                messagebox.showinfo(
                    "Sukces",
                    f"Ilość produktu '{product_name}' została zmniejszona o {abs(delta)}."
                )

            # Refresh UI
            self.update_products_list()
            self.update_parts_list()

        ttkb.Button(
            self.right_frame,
            text="Zapisz zmiany",
            bootstyle="success",
            command=edit_product,
        ).pack(pady=20)


    def clear_right_frame(self):
        """Clear all widgets from the right frame"""
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def show_feedback_form(self):
        """Display the feedback form in a new window."""
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Zgłoś błąd")
        feedback_window.geometry("600x500")
        feedback_window.resizable(False, False)

        # Feedback form components
        ttkb.Label(feedback_window, text="Kategoria:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=5)
        category_var = tk.StringVar(value="UI Bug")
        categories = ["UI Bug", "Funkcjonalność", "Crash/Error", "Inne"]
        category_menu = ttkb.OptionMenu(feedback_window, category_var, *categories)
        category_menu.pack(fill="x", padx=10, pady=5)

        ttkb.Label(feedback_window, text="Opis błędu:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=5)
        message_text = tk.Text(feedback_window, wrap="word", height=10, font=("Arial", 12))
        message_text.pack(fill="both", expand=True, padx=10, pady=5)

        def send_feedback():
            """Send feedback via email."""
            category = category_var.get()
            message = message_text.get("1.0", "end").strip()
            if not message:
                messagebox.showerror("Błąd", "Wiadomość nie może być pusta.")
                return

            try:
                # Email configuration
                sender_email = "app.emag@gmail.com"  # Replace with your app's email
                sender_password = "pvzc vlfx tndc nssh"  # Replace with your email password
                recipient_email = "devrzeszowski@gmail.com"  # Replace with your personal email
                subject = f"Bug Report - {category}"

                # Construct the email
                email_message = MIMEMultipart()
                email_message["From"] = sender_email
                email_message["To"] = recipient_email
                email_message["Subject"] = subject
                email_message.attach(MIMEText(message, "plain"))

                # Send the email
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient_email, email_message.as_string())

                messagebox.showinfo("Wiadomość została wysłana.")
                feedback_window.destroy()

            except Exception as e:
                print(f"Błąd: {e}")
                messagebox.showerror("Błąd", "Spróbuj później")

        ttkb.Button(
            feedback_window,
            text="Wyślij",
            bootstyle="success",
            command=send_feedback,
        ).pack(pady=10, padx=10)


    def check_for_updates(self):
        """Check for updates."""
        try:
            response = requests.get("https://api.github.com/repos/filiprzeszowski/EMAG/releases/latest")
            response.raise_for_status()
            latest_version = response.json()["tag_name"]

            if VERSION < latest_version:
                should_update = messagebox.askyesno(
                    "Aktualizacja dostępna",
                    f"Nowa wersja ({latest_version}) jest dostępna. Czy chcesz zaktualizować?"
                )
                if should_update:
                    self.download_and_apply_update(response.json()["zipball_url"])
            else:
                messagebox.showinfo("Aktualizacja", "Masz najnowszą wersję.")
        except Exception as e:
            print(f"Błąd sprawdzania aktualizacji: {e}")
            messagebox.showerror("Błąd aktualizacji", "Nie udało się sprawdzić.")


    def download_and_apply_update(self, update_package_url):
        """Download and apply the update package."""
        update_zip_path = "update.zip"
        extract_dir = "update_extracted"
        try:
            response = requests.get(update_package_url, stream=True)
            response.raise_for_status()
            with open(update_zip_path, "wb") as update_file:
                for chunk in response.iter_content(chunk_size=8192):
                    update_file.write(chunk)
            with zipfile.ZipFile(update_zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_path, extract_dir)
                    destination_path = os.path.join(".", relative_path)
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    os.replace(source_path, destination_path)
            messagebox.showinfo("Aktualizacja", "Aplikacja została zaktualizowana. Teraz uruchomi się ponownie.")
            self.restart_app()
        except requests.exceptions.RequestException as e:
            print(f"Błąd pobierania aktualizacji: {e}")
            messagebox.showerror("Błąd aktualizacji", "Nie udało się pobrać aktualizacji.")
        except Exception as e:
            print(f"Błąd podczas aktualizacji: {e}")
            messagebox.showerror("Błąd aktualizacji", "Wystąpił błąd podczas aktualizacji.")
        finally:
            if os.path.exists(update_zip_path):
                os.remove(update_zip_path)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)



    def restart_app(self):
        """Restart the application."""
        python = sys.executable
        os.execl(python, python, *sys.argv)

def run_gui():
    root = ttkb.Window("EMAG", themename="cosmo")
    app = EMAGApp(root)
    root.mainloop()