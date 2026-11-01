from dataclasses import dataclass, field
from math import ceil
from typing import Dict, List


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
class Drink:
    name: str
    quantity_per_guest: float
    unit: str
    pack_size: float
    pack_price: float
    category: str = "Drikkevarer"

    def packs_needed(self, guests: int) -> int:
        return ceil(guests * self.quantity_per_guest / self.pack_size)

    def estimated_price(self, guests: int) -> float:
        return self.packs_needed(guests) * self.pack_price


@dataclass
class PartyPlan:
    guests: int = 16
    budget: float = 1500
    dishes: List[Dish] = field(default_factory=list)
    drinks: List[Drink] = field(default_factory=list)

    def selected_dishes(self) -> List[Dish]:
        return [dish for dish in self.dishes if dish.selected]

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

    def food_cost(self) -> float:
        return sum(i.estimated_price for i in self.ingredient_totals().values())

    def drink_cost(self) -> float:
        return sum(drink.estimated_price(self.guests) for drink in self.drinks)

    def total_cost(self) -> float:
        return self.food_cost() + self.drink_cost()

    def shopping_list(self) -> str:
        lines = ["INDKØBSLISTE", "=" * 40]
        grouped = {}
        for ingredient in self.ingredient_totals().values():
            grouped.setdefault(ingredient.category, []).append(ingredient)

        for category in sorted(grouped):
            lines.append(f"\n{category.upper()}")
            for ingredient in sorted(grouped[category], key=lambda x: x.name.lower()):
                lines.append(
                    f"- {format_quantity(ingredient.quantity)} {ingredient.unit} {ingredient.name}"
                )

        if self.drinks:
            lines.append("\nDRIKKEVARER")
            for drink in self.drinks:
                packs = drink.packs_needed(self.guests)
                total_units = packs * drink.pack_size
                lines.append(
                    f"- {packs} x {format_quantity(drink.pack_size)} {drink.unit} "
                    f"{drink.name} ({format_quantity(total_units)} i alt)"
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
            f"Drikkevarer: {self.drink_cost():.2f} kr.",
            f"Totalestimat: {total:.2f} kr.",
            f"Difference: {difference:+.2f} kr. ({status})",
            "",
            "VALGT MENU",
        ]
        lines.extend(f"- {dish.name}" for dish in self.selected_dishes())
        return "\n".join(lines)

    def find_ingredient(self, name: str) -> Ingredient | None:
        name = name.lower()
        totals = self.ingredient_totals()
        for key, ing in totals.items():
            if name in ing.name.lower():
                return ing
        return None

    def find_drink(self, name: str) -> Drink | None:
        name = name.lower()

        for drink in self.drinks:
            if name in drink.name.lower():
                return drink

        return None

def format_quantity(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def ingredient(name, quantity, unit, price, category):
    return Ingredient(name, quantity, unit, price, category)


# Ændr primært her. Mængderne nedenfor er beregnet til 16 personer.
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
        ingredient("Citron", 2, "stk.", 4, "Frugt og grønt")    ]),
]


drinks = [
    Drink("Øl", quantity_per_guest=3, unit="stk.", pack_size=30, pack_price=105),
    Drink("Vin", quantity_per_guest=2 / 5, unit="flaske", pack_size=1, pack_price=70),
    Drink("Sodavand", quantity_per_guest=0.5, unit="L", pack_size=1.5, pack_price=15),
]


plan = PartyPlan(guests=16, budget=1500, dishes=dishes, drinks=drinks)


if __name__ == "__main__":
    print(plan.summary())
    print("\n" + plan.shopping_list())

    smør = plan.find_ingredient("smør")
    olivenolie = plan.find_ingredient("olivenolie")
    øl = plan.find_drink("øl")
    vin = plan.find_drink("vin")
    sodavand = plan.find_drink("sodavand")
    
    udvalgte_varer = [smør, olivenolie, øl, vin, sodavand]
    
    for vare in udvalgte_varer:
        if vare is None:
            print("\nVare ikke fundet i indkøbslisten.")
        elif isinstance(vare, Drink):
            packs = vare.packs_needed(plan.guests)
            print(
                f"\n{vare.name}: {packs} x {vare.pack_size} {vare.unit} "
                f"til en estimeret pris på {vare.estimated_price(plan.guests):.2f} kr."
            )
        else:
            print(
                f"\n{vare.name}: {vare.quantity} {vare.unit} "
                f"til en estimeret pris på {vare.estimated_price:.2f} kr."
            )