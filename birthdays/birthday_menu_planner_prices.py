from dataclasses import dataclass, field
from math import ceil
from typing import Dict, List, Optional


@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str
    price_per_unit: float
    category: str = "Andet"

    @property
    def estimated_price(self) -> float:
        return self.quantity * self.price_per_unit


@dataclass
class Dish:
    name: str
    ingredients: List[Ingredient]
    servings: int = 16
    selected: bool = True

    def scaled_ingredients(self, guests: int) -> List[Ingredient]:
        factor = guests / self.servings
        return [
            Ingredient(
                name=i.name,
                quantity=i.quantity * factor,
                unit=i.unit,
                price_per_unit=i.price_per_unit,
                category=i.category,
            )
            for i in self.ingredients
        ]


@dataclass
class Snack:
    name: str
    quantity_per_guest: float
    unit: str
    pack_size: float
    pack_price: float
    selected: bool = True
    category: str = "Snacks"

    def quantity_needed(self, guests: int) -> float:
        return guests * self.quantity_per_guest

    def packs_needed(self, guests: int) -> int:
        return ceil(self.quantity_needed(guests) / self.pack_size)

    def purchased_quantity(self, guests: int) -> float:
        return self.packs_needed(guests) * self.pack_size

    def estimated_price(self, guests: int) -> float:
        return self.packs_needed(guests) * self.pack_price


@dataclass
class Drink:
    name: str
    quantity_per_guest: float
    unit: str
    pack_size: float
    pack_price: float
    category: str = "Drikkevarer"
    selected: bool = True

    def quantity_needed(self, guests: int) -> float:
        return guests * self.quantity_per_guest

    def packs_needed(self, guests: int) -> int:
        return ceil(self.quantity_needed(guests) / self.pack_size)

    def purchased_quantity(self, guests: int) -> float:
        return self.packs_needed(guests) * self.pack_size
    def estimated_price(self, guests: int) -> float:
        return self.packs_needed(guests) * self.pack_price


@dataclass
class PartyPlan:
    guests: int = 16
    budget: float = 1500
    dishes: List[Dish] = field(default_factory=list)
    snacks: List[Snack] = field(default_factory=list)
    drinks: List[Drink] = field(default_factory=list)

    def selected_dishes(self) -> List[Dish]:
        return [dish for dish in self.dishes if dish.selected]

    def selected_snacks(self) -> List[Snack]:
        return [snack for snack in self.snacks if snack.selected]

    def selected_drinks(self) -> List[Drink]:
        return [drink for drink in self.drinks if drink.selected]

    def ingredient_totals(self) -> Dict[str, Ingredient]:
        totals: Dict[str, Ingredient] = {}
        for dish in self.selected_dishes():
            for ingredient in dish.scaled_ingredients(self.guests):
                key = f"{ingredient.name.lower()}|{ingredient.unit}"
                if key not in totals:
                    totals[key] = Ingredient(
                        name=ingredient.name,
                        quantity=0,
                        unit=ingredient.unit,
                        price_per_unit=ingredient.price_per_unit,
                        category=ingredient.category,
                    )
                totals[key].quantity += ingredient.quantity
        return totals
    
    def dish_cost(self, dish: Dish) -> float:
        return sum(
            ingredient.estimated_price
            for ingredient in dish.scaled_ingredients(self.guests)
        )


    def food_cost(self) -> float:
        return sum(i.estimated_price for i in self.ingredient_totals().values())

    def snack_cost(self) -> float:
        return sum(snack.estimated_price(self.guests) for snack in self.selected_snacks())

    def drink_cost(self) -> float:
        return sum(drink.estimated_price(self.guests) for drink in self.selected_drinks())

    def total_cost(self) -> float:
        return self.food_cost() + self.snack_cost() + self.drink_cost()

    def shopping_list(self) -> str:
        lines = ["INDKØBSLISTE", "=" * 40]
        grouped: Dict[str, List[Ingredient]] = {}

        for ingredient in self.ingredient_totals().values():
            grouped.setdefault(ingredient.category, []).append(ingredient)

        for category in sorted(grouped):
            lines.append(f"\n{category.upper()}")
            for ingredient in sorted(grouped[category], key=lambda x: x.name.lower()):
                lines.append(
                    f"- {format_quantity(ingredient.quantity)} {ingredient.unit} "
                    f"{ingredient.name} — {ingredient.estimated_price:.2f} kr."
                )

        if self.selected_snacks():
            lines.append("\nSNACKS")
            for snack in self.selected_snacks():
                needed = snack.quantity_needed(self.guests)
                packs = snack.packs_needed(self.guests)
                purchased = snack.purchased_quantity(self.guests)
                price = snack.estimated_price(self.guests)
                lines.append(
                    f"- {packs} x {format_quantity(snack.pack_size)} {snack.unit} "
                    f"{snack.name} "
                    f"(behov: {format_quantity(needed)} {snack.unit}; "
                    f"køb: {format_quantity(purchased)} {snack.unit}) "
                    f"— {price:.2f} kr."
                )

        if self.selected_drinks():
            lines.append("\nDRIKKEVARER")
            for drink in self.selected_drinks():
                needed = drink.quantity_needed(self.guests)
                packs = drink.packs_needed(self.guests)
                purchased = drink.purchased_quantity(self.guests)
                price = drink.estimated_price(self.guests)
                lines.append(
                    f"- {packs} x {format_quantity(drink.pack_size)} {drink.unit} "
                    f"{drink.name} "
                    f"(behov: {format_quantity(needed)} {drink.unit}; "
                    f"køb: {format_quantity(purchased)} {drink.unit}) "
                    f"— {price:.2f} kr."
                )

        return "\n".join(lines)

    def summary(self) -> str:
        total = self.total_cost()
        difference = self.budget - total
        status = "UNDER BUDGET" if difference >= 0 else "OVER BUDGET"
        lines = [
            "MENUOVERSIGT",
            "=" * 40,
            f"Gæster: {self.guests}",
            f"Budget: {self.budget:.2f} kr.",
            f"Mad: {self.food_cost():.2f} kr.",
            f"Snacks: {self.snack_cost():.2f} kr.",
            f"Drikkevarer: {self.drink_cost():.2f} kr.",
            f"Totalestimat: {total:.2f} kr.",
            f"Difference: {difference:+.2f} kr. ({status})",
            "",
            "VALGT MENU",
        ]
        for dish in self.selected_dishes():
            lines.append(f"- {dish.name} -- {self.dish_cost(dish):.2f} kr.")

        if self.selected_snacks():
            lines.append(f"- Snacks -- {self.snack_cost():.2f} kr.")

        return "\n".join(lines)

def format_quantity(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def ingredient(name, quantity, unit, price, category):
    return Ingredient(name, quantity, unit, price, category)


# Ændr primært her. Mængderne er beregnet til 16 personer.
dishes = [
    Dish("Hel kylling", [
        ingredient("Hel kylling", 5, "stk.", 39, "Kød"),
    ]),
    Dish("Flødekartofler", [
        ingredient("Kartofler", 5, "kg", 10, "Frugt og grønt"),
        ingredient("Løg", 5, "stk.", 2.50, "Frugt og grønt"),
        ingredient("Hvidløg", 5, "fed", 1, "Frugt og grønt"),
        ingredient("Fløde", 2.5, "L", 25, "Køl"),
        ingredient("Smør", 0.2, "kg", 60, "Køl"),
        ingredient("Revet ost", 0.5, "kg", 70, "Køl"),
    ]),
    Dish("Focaccia", [
        ingredient("Hvedemel / tipo 00", 0.5, "kg", 18, "Tørvarer"),
        ingredient("Gær", 1, "pakke", 5, "Køl"),
        ingredient("Olivenolie", 1, "L", 70, "Tørvarer"),
        ingredient("Rosmarin", 1, "bundt", 15, "Frugt og grønt"),
    ]),
    Dish("Græsk salat uden oliven", [
        ingredient("Tomater", 0.8, "kg", 35, "Frugt og grønt"),
        ingredient("Agurk", 2, "stk.", 10, "Frugt og grønt"),
        ingredient("Rødløg", 2, "stk.", 4, "Frugt og grønt"),
        ingredient("Peberfrugt", 3, "stk.", 10, "Frugt og grønt"),
        ingredient("Feta", 0.6, "kg", 80, "Køl"),
        ingredient("Citron", 2, "stk.", 4, "Frugt og grønt"),
    ]),
]


snacks = [
    Snack("Chips", quantity_per_guest=0.04, unit="kg", pack_size=0.2, pack_price=10),
    Snack("Gulerødder", quantity_per_guest=0.04, unit="kg", pack_size=1, pack_price=10),
    Snack("Agurk", quantity_per_guest=0.04, unit="kg", pack_size=0.2, pack_price=10),
    Snack("Creme fraiche", quantity_per_guest=0.05, unit="kg", pack_size=0.5, pack_price=20),
    Snack("Dip pulver", quantity_per_guest=0.1, unit="pack", pack_size=1, pack_price=12),
]


drinks = [
    Drink("Øl", quantity_per_guest=3, unit="stk.", pack_size=30, pack_price=105),
    Drink("Vin", quantity_per_guest=2 / 5, unit="flaske", pack_size=1, pack_price=70),
    Drink("Sodavand", quantity_per_guest=0.5, unit="L", pack_size=1.5, pack_price=15),
]


plan = PartyPlan(
    guests=16,
    budget=1500,
    dishes=dishes,
    snacks=snacks,
    drinks=drinks,
)


if __name__ == "__main__":
    print(plan.summary())
    print("\n" + plan.shopping_list())
