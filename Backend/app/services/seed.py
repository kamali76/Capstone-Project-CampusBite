"""Optional demo data (SEED_DEMO_DATA=true) so the app is usable right after startup."""
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..constants import Role
from ..models import MenuItem, Restaurant, User
from ..security import hash_password

logger = logging.getLogger("campusbite.seed")

DEFAULT_DEMO_PASSWORD = "Demo@1234"

RESTAURANTS = [
    {
        "owner": ("Campus Cafe Owner", "owner1@campusbite.com"),
        "name": "Campus Cafe",
        "cuisine": "Snacks & Beverages",
        "description": "Quick bites and hot drinks near the main block.",
        "address": "Main Block, Ground Floor",
        "menu": [
            ("Snacks", "Veg Sandwich", "Grilled with cheese and veggies", 60, True),
            ("Snacks", "French Fries", "Crispy salted fries", 80, True),
            ("Beverages", "Masala Chai", "Hot, strong and sweet", 20, True),
            ("Beverages", "Cold Coffee", "Blended with ice cream", 90, False),
        ],
    },
    {
        "owner": ("Spice Route Owner", "owner2@campusbite.com"),
        "name": "Spice Route",
        "cuisine": "South Indian",
        "description": "Home-style meals, dosas and tiffin favourites.",
        "address": "Food Court, Stall 2",
        "menu": [
            ("Tiffin", "Masala Dosa", "Crispy dosa with potato filling", 70, True),
            ("Tiffin", "Idli (3 pcs)", "Served with sambar and chutney", 45, True),
            ("Meals", "Veg Meals", "Rice, sambar, rasam, poriyal, curd", 120, True),
            ("Meals", "Curd Rice", "Cool and comforting", 60, True),
        ],
    },
    {
        "owner": ("Pizza Point Owner", "owner3@campusbite.com"),
        "name": "Pizza Point",
        "cuisine": "Italian",
        "description": "Fresh pizzas and pasta, baked to order.",
        "address": "Hostel Road",
        "menu": [
            ("Pizza", "Margherita Pizza", "Classic cheese and tomato", 199, True),
            ("Pizza", "Farmhouse Pizza", "Loaded with veggies", 279, True),
            ("Pasta", "White Sauce Pasta", "Creamy penne pasta", 169, True),
        ],
    },
    {
        "owner": ("Wok & Roll Owner", "owner4@campusbite.com"),
        "name": "Wok & Roll",
        "cuisine": "Chinese",
        "description": "Noodles, fried rice and rolls.",
        "address": "Food Court, Stall 5",
        "menu": [
            ("Noodles", "Hakka Noodles", "Stir-fried with vegetables", 110, True),
            ("Rice", "Veg Fried Rice", "Wok-tossed with sauces", 100, True),
            ("Rolls", "Paneer Roll", "Spicy paneer in a soft wrap", 85, False),
        ],
    },
]


def seed_demo_data(db: Session) -> bool:
    """Insert demo users, restaurants and menus. Does nothing if users already exist."""
    if db.scalar(select(func.count()).select_from(User)):
        return False

    password = get_settings().seed_demo_password or DEFAULT_DEMO_PASSWORD
    password_hash = hash_password(password)

    db.add(
        User(
            name="Demo Customer",
            email="customer@campusbite.com",
            phone="9000000001",
            password_hash=password_hash,
            role=Role.CUSTOMER,
        )
    )
    for n in (1, 2):
        db.add(
            User(
                name=f"Delivery Partner {n}",
                email=f"delivery{n}@campusbite.com",
                phone=f"900000010{n}",
                password_hash=password_hash,
                role=Role.DELIVERY,
            )
        )

    for spec in RESTAURANTS:
        owner = User(
            name=spec["owner"][0],
            email=spec["owner"][1],
            password_hash=password_hash,
            role=Role.OWNER,
        )
        db.add(owner)
        db.flush()
        restaurant = Restaurant(
            owner_id=owner.id,
            name=spec["name"],
            cuisine=spec["cuisine"],
            description=spec["description"],
            address=spec["address"],
        )
        db.add(restaurant)
        db.flush()
        for category, name, description, price, available in spec["menu"]:
            db.add(
                MenuItem(
                    restaurant_id=restaurant.id,
                    category=category,
                    name=name,
                    description=description,
                    price=price,
                    is_available=available,
                )
            )
    db.commit()
    logger.info("Demo data created (customer@, owner1-4@, delivery1-2@campusbite.com)")
    return True
