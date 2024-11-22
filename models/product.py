class Part:
    """Reprezentuje pojedynczą część w magazynie."""
    def __init__(self, name, quantity):
        self.name = name
        self.quantity = quantity

    def __str__(self):
        return f"{self.name} (Ilość: {self.quantity})"


class Product:
    """Reprezentuje produkt finalny, np. głowicę studzienną."""
    def __init__(self, name):
        self.name = name
        self.parts = []

    def add_part(self, part, quantity):
        """Dodaje część do produktu."""
        self.parts.append({"part": part, "quantity": quantity})

    def __str__(self):
        parts_details = "\n".join([f"- {p['part'].name} (Ilość: {p['quantity']})" for p in self.parts])
        return f"Produkt: {self.name}\nCzęści składowe:\n{parts_details}"
