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
import smtplib


class EMAGApp:
    def __init__(self, root):
        self.controller = ProductController()
        self.root = root
        self.root.title("EMAG - Zarządzanie magazynem")
        self.root.state("zoomed")  # Fullscreen
        self.dark_mode = False  # Default: Light Mode
        self.setup_styles()
        self.create_toolbar()
        self.create_layout()
        self.create_status_bar()
        self.check_for_updates()
        self.update_parts_list()
        self.update_products_list()


    def setup_styles(self):
        """Configure consistent theme styles"""
        self.style = ttkb.Style("cosmo")  # Modern theme
        self.root.configure(bg=self.style.colors.bg)

        # Global widget styles
        self.style.configure(
            "TLabel",
            background=self.style.colors.bg,  # Match app background
            foreground=self.style.colors.fg,
        )
        self.style.configure(
            "TButton",
            font=("Arial", 12),
            background=self.style.colors.primary,
            foreground=self.style.colors.light,
        )
        self.style.configure(
            "TEntry",
            fieldbackground=self.style.colors.bg,
            foreground=self.style.colors.fg,
        )
        self.style.configure(
            "Treeview",
            background=self.style.colors.bg,
            fieldbackground=self.style.colors.bg,
            foreground=self.style.colors.fg,
        )


    def create_toolbar(self):
        """Create a modern toolbar with consistent theme colors"""
        self.toolbar = ttkb.Frame(self.root, padding=10, bootstyle="primary")
        self.toolbar.pack(side="top", fill="x")

        ttkb.Label(
            self.toolbar,
            text="EMAG - Zarządzanie magazynem",
            font=("Arial", 16, "bold"),
            anchor="w",
            bootstyle="inverse-primary",
        ).pack(side="left", padx=10)

        ttkb.Button(
            self.toolbar,
            text="Ciemny motyw",
            bootstyle="secondary-outline",
            command=self.toggle_dark_mode,
        ).pack(side="right", padx=10)

        ttkb.Button(
            self.toolbar,
            text="Sprawdź aktualizacje",
            bootstyle="info-outline",
            command=self.check_for_updates,  # Call the update check function
        ).pack(side="right", padx=10)

        ttkb.Button(
            self.toolbar,
            text="Zgłoś błąd",
            bootstyle="danger-outline",
            command=self.show_feedback_form,
        ).pack(side="right", padx=10)



    def toggle_dark_mode(self):
        """Toggle dark mode for the application"""
        self.dark_mode = not self.dark_mode
        theme = "darkly" if self.dark_mode else "cosmo"
        self.style.theme_use(theme)

    def get_colors(self):
        """Retrieve colors for the current mode."""
        if self.dark_mode:
            return {
                "bg": "#ffffff",
                "menu_bg": "#f0f0f0",
                "notebook_bg": "#f8f9fa",
                "right_frame_bg": "#f8f9fa",
                "status_bg": "#e8e8e8",
                "status_fg": "black",
                "button_bg": "#555555",
                "button_fg": "white",
            }
        else:
            return {
                "bg": "#121212",
                "menu_bg": "#1f1f1f",
                "notebook_bg": "#2e2e2e",
                "right_frame_bg": "#1f1f1f",
                "status_bg": "#1c1c1c",
                "status_fg": "white",
                "button_bg": "#333333",
                "button_fg": "white",
            }

    def create_layout(self):
        """Create the main layout with responsive middle list."""
        # Create a container frame for left (menu), middle (notebook), and right sections
        self.main_frame = ttkb.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Side Menu
        self.menu_frame = ttkb.Frame(self.main_frame, padding=10, bootstyle="secondary")
        self.menu_frame.pack(side="left", fill="y", padx=10, pady=10)

        ttkb.Label(
            self.menu_frame,
            text="Menu",
            font=("Arial", 16, "bold"),
            anchor="center",
            bootstyle="primary",
        ).pack(pady=10)

        self.create_menu_buttons()

        # Middle Section (Notebook)
        self.notebook_frame = ttkb.Frame(self.main_frame, padding=10)
        self.notebook_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.notebook = ttkb.Notebook(self.notebook_frame, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True)

        # Parts Tab
        self.parts_tab = ttkb.Frame(self.notebook, padding=10)
        self.notebook.add(self.parts_tab, text="Części")

        self.parts_list = self.create_treeview(self.parts_tab)
        self.parts_list.pack(fill="both", expand=True, padx=10, pady=10)

        # Products Tab
        self.products_tab = ttkb.Frame(self.notebook, padding=10)
        self.notebook.add(self.products_tab, text="Produkty")

        self.products_list = self.create_treeview(self.products_tab)
        self.products_list.pack(fill="both", expand=True, padx=10, pady=10)

        # Right Frame
        self.right_frame = ttkb.Frame(self.main_frame, padding=10, bootstyle="secondary", width=300)
        self.right_frame.pack(side="right", fill="y", padx=10, pady=10)

        # Prevent the right frame from propagating its size to the parent
        self.right_frame.pack_propagate(False)



    def create_menu_buttons(self):
        """Add buttons to the side menu"""
        buttons = [
            ("Dodaj Część", self.show_add_part_menu),
            ("Edytuj Część", self.show_edit_part_menu),
            ("Dodaj Produkt", self.show_add_product_menu),
            ("Edytuj Produkt", self.show_edit_product_menu),
        ]
        for text, command in buttons:
            ttkb.Button(
                self.menu_frame,
                text=text,
                bootstyle="primary",
                command=command,
            ).pack(fill="x", pady=5)

    def create_treeview(self, parent):
        """Create a styled treeview"""
        tree = ttkb.Treeview(
            parent,
            columns=("name", "quantity"),
            show="headings",
            style="Treeview"
        )
        tree.heading("name", text="Nazwa")
        tree.heading("quantity", text="Ilość")
        tree.column("name", width=300)
        tree.column("quantity", width=100, anchor="center")

        # Ensure background matches theme
        tree.tag_configure("oddrow", background=self.style.colors.bg)
        tree.tag_configure("evenrow", background=self.style.colors.border)

        return tree


    def create_status_bar(self):
        """Add a modern status bar"""
        self.status_bar = ttkb.Label(
            self.root,
            text="Gotowy",
            anchor="w",
            bootstyle="inverse-dark",
            font=("Arial", 10),
        )
        self.status_bar.pack(side="bottom", fill="x")

    def create_animated_button(self, parent, text, command):
        """Create a button with hover animation."""
        button = tk.Button(parent, text=text, font=("Arial", 12), bg="#555555", fg="white", command=command)

        def on_enter(event):
            button.config(bg="#007BFF")

        def on_leave(event):
            button.config(bg="#555555")

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.pack(pady=10)

    def update_parts_list(self):
        """Update the parts list in the Treeview with Firebase data."""
        # Load inventory from Firebase
        self.controller.db.load_inventory_from_firebase()
        
        # Update the Treeview
        self.parts_list.delete(*self.parts_list.get_children())
        for part, quantity in self.controller.db.inventory.items():
            self.parts_list.insert("", "end", values=(part, quantity))


    def update_products_list(self):
        """Update the products list in the Treeview with Firebase data."""
        # Load products from Firebase
        self.controller.db.load_products_from_firebase()

        # Update the Treeview
        self.products_list.delete(*self.products_list.get_children())
        for product in self.controller.db.products:
            product_name = product["name"]
            product_quantity = product["quantity"]
            self.products_list.insert("", "end", values=(product_name, product_quantity))



    def show_add_part_menu(self):
        """Display the Add Part menu with responsive design."""
        self.clear_right_frame()

        # Set frame title with theme-consistent styling
        ttkb.Label(
            self.right_frame,
            text="Dodaj Część",
            font=("Arial", 14, "bold"),
            bootstyle="inverse-secondary",
        ).pack(pady=10)

        form_frame = ttkb.LabelFrame(
            self.right_frame, text="Dodaj Część",
            padding=10,
            bootstyle="secondary"
        )
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Part selection
        ttkb.Label(form_frame, text="Wybierz część:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
        part_name_var = tk.StringVar()
        available_parts = list(self.controller.get_available_parts().keys())
        part_name_var.set(available_parts[0])  # Default to the first part
        part_menu = ttkb.OptionMenu(form_frame, part_name_var, *available_parts)
        part_menu.grid(row=0, column=1, pady=5, sticky="ew")

        # Size selection
        ttkb.Label(form_frame, text="Wybierz rozmiar:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
        size_var = tk.StringVar()
        initial_sizes = self.controller.get_available_parts()[available_parts[0]]
        size_var.set(initial_sizes[0])  # Default size
        size_menu = ttkb.OptionMenu(form_frame, size_var, *initial_sizes)
        size_menu.grid(row=1, column=1, pady=5, sticky="ew")

        # Update size menu when part changes
        def update_size_menu(*args):
            selected_part = part_name_var.get()
            sizes = self.controller.get_available_parts()[selected_part]
            size_var.set(sizes[0])  # Default to the first size
            size_menu["menu"].delete(0, "end")
            for size in sizes:
                size_menu["menu"].add_command(label=size, command=lambda value=size: size_var.set(value))

        part_name_var.trace_add("write", update_size_menu)

        # Quantity input
        ttkb.Label(form_frame, text="Podaj ilość:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        quantity_entry = ttkb.Entry(form_frame, font=("Arial", 12))
        quantity_entry.grid(row=2, column=1, pady=5, sticky="ew")

        # Add button
        def add_part():
            """Add a part to the inventory and update Firebase."""
            part_name = part_name_var.get()
            size = size_var.get()
            quantity = quantity_entry.get()

            if not quantity.isdigit() or int(quantity) <= 0:
                messagebox.showerror("Błąd", "Podaj poprawną ilość.")
                return

            # Add part to Firebase database
            self.controller.db.add_part(f"{part_name} ({size})", int(quantity))
            
            # Update the parts list in the UI
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Część '{part_name} ({size})' została dodana.")


        ttkb.Button(
            self.right_frame,
            text="Dodaj",
            bootstyle="success",
            command=add_part,
        ).pack(pady=10, fill="x")


    def show_edit_part_menu(self):
        """Display the Edit Part menu"""
        self.clear_right_frame()
        ttkb.Label(
            self.right_frame,
            text="Edytuj Część",
            font=("Arial", 14, "bold"),
            bootstyle="inverse",
        ).pack(pady=10)

        part_name_var = tk.StringVar(self.right_frame)
        part_name_var.set(list(self.controller.get_available_parts().keys())[0])

        tk.Label(self.right_frame, text="Wybierz część:", font=("Arial", 12), bg="#f0f0f0").pack(
            pady=5
        )
        part_menu = tk.OptionMenu(
            self.right_frame,
            part_name_var,
            *self.controller.get_available_parts().keys(),
        )
        part_menu.pack(pady=10)

        size_var = tk.StringVar(self.right_frame)
        initial_sizes = self.controller.get_available_parts()[part_name_var.get()]
        size_var.set(initial_sizes[0])

        tk.Label(self.right_frame, text="Wybierz rozmiar:", font=("Arial", 12), bg="#f0f0f0").pack(
            pady=5
        )
        size_menu = tk.OptionMenu(self.right_frame, size_var, *initial_sizes)
        size_menu.pack(pady=10)

        # Aktualizacja rozmiarów po wyborze części
        def update_size_menu(*args):
            selected_part = part_name_var.get()
            sizes = self.controller.get_available_parts()[selected_part]
            size_var.set(sizes[0])  # Domyślny rozmiar
            size_menu["menu"].delete(0, "end")  # Wyczyszczenie starego menu
            for size in sizes:
                size_menu["menu"].add_command(
                    label=size, command=lambda value=size: size_var.set(value)
                )

        part_name_var.trace("w", update_size_menu)

        tk.Label(self.right_frame, text="Podaj zmianę ilości (+/-):", font=("Arial", 12), bg="#f0f0f0").pack(
            pady=5
        )
        delta_entry = tk.Entry(self.right_frame, font=("Arial", 12))
        delta_entry.pack(pady=10)

        def edit_part():
            part_name = part_name_var.get()
            size = size_var.get()
            delta = delta_entry.get()
            if not delta.lstrip('-').isdigit():
                messagebox.showerror("Błąd", "Podaj poprawną liczbę.")
                return
            self.controller.edit_part_quantity(part_name, size, int(delta))
            self.update_parts_list()
            messagebox.showinfo("Sukces", f"Część '{part_name} ({size})' została zmieniona.")

        tk.Button(
            self.right_frame,
            text="Zapisz",
            font=("Arial", 12),
            bg="#28a745",
            fg="white",
            command=edit_part,
        ).pack(pady=20)

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
            """Add a product and sync with Firebase."""
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
                        messagebox.showerror("Błąd", f"Ilość części '{part_name}' przekracza dostępne {available}.")
                        return
                    selected_parts[part_name] = quantity

            if not selected_parts:
                messagebox.showerror("Błąd", "Wybierz przynajmniej jedną część.")
                return

            # Check if there are enough parts for the desired quantity of products
            for part_name, quantity_per_product in selected_parts.items():
                total_quantity_needed = quantity_per_product * product_quantity
                if self.controller.db.inventory.get(part_name, 0) < total_quantity_needed:
                    messagebox.showerror(
                        "Błąd",
                        f"Niewystarczająca ilość części '{part_name}' do utworzenia {product_quantity} sztuk produktu.",
                    )
                    return

            # Deduct the required parts from Firebase
            for part_name, quantity_per_product in selected_parts.items():
                total_quantity_needed = quantity_per_product * product_quantity
                new_quantity = self.controller.db.inventory[part_name] - total_quantity_needed
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
        """Check for updates by comparing the local version with the remote version."""
        try:
            # URL of the version file and the update package in your GitHub repository
            remote_version_url = "https://raw.githubusercontent.com/filiprzeszowski/EMAG/refs/tags/EMAG/config/config.py"
            update_package_url = "https://github.com/filiprzeszowski/EMAG/releases/download/latest/update.zip"

            # Fetch the remote version file
            response = requests.get(remote_version_url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Get the latest version from the file
            remote_version = response.text.strip()

            # Compare versions
            if VERSION < remote_version:
                # Ask user for confirmation to update
                should_update = messagebox.askyesno(
                    "Aktualizacja dostępna",
                    f"Nowa wersja ({remote_version}) jest dostępna. Aktualna wersja: {VERSION}.\n\n"
                    "Czy pobrać aktualizację?"
                )
                if should_update:
                    self.download_and_apply_update(update_package_url)

        except requests.exceptions.RequestException as e:
            print(f"Błąd sprawdzania aktualizacji: {e}")
            messagebox.showerror("Błąd sprawdzania aktualizacji", "Zgłoszenie zostało wysłane.")

    def download_and_apply_update(self, update_package_url):
        """Download and apply the update package."""
        try:
            # Download the update package
            response = requests.get(update_package_url, stream=True)
            response.raise_for_status()

            # Save the zip file locally
            update_zip_path = "update.zip"
            with open(update_zip_path, "wb") as update_file:
                for chunk in response.iter_content(chunk_size=8192):
                    update_file.write(chunk)

            # Extract the update package
            with zipfile.ZipFile(update_zip_path, "r") as zip_ref:
                zip_ref.extractall(".")  # Extract into the current directory

            # Clean up the downloaded zip file
            os.remove(update_zip_path)

            # Notify user and restart the app
            messagebox.showinfo(
                "Update Applied",
                "The application has been updated successfully. The app will now restart."
            )
            self.restart_app()

        except requests.exceptions.RequestException as e:
            print(f"Error downloading the update: {e}")
            messagebox.showerror("Update Failed", "Failed to download the update. Please try again later.")
        except zipfile.BadZipFile as e:
            print(f"Error extracting the update package: {e}")
            messagebox.showerror("Update Failed", "The update package is corrupted.")

    def restart_app(self):
        """Restart the application."""
        python = sys.executable
        os.execl(python, python, *sys.argv)

def run_gui():
    root = ttkb.Window("EMAG", themename="cosmo")
    app = EMAGApp(root)
    root.mainloop()