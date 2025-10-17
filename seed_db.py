from django.utils import timezone
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql_crm.settings")
django.setup()

from crm.models import Customer, Product, Order

def run():
    # Seed Customers
    customers = [
        {"name": "Alice", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol", "email": "carol@example.com"}
    ]
    for c in customers:
        Customer.objects.get_or_create(**c)

    # Seed Products
    products = [
        {"name": "Laptop", "price": 999.99, "stock": 10},
        {"name": "Mouse", "price": 25.50, "stock": 50},
        {"name": "Keyboard", "price": 75.00, "stock": 20}
    ]
    for p in products:
        Product.objects.get_or_create(**p)

    # Example order
    customer = Customer.objects.first()
    product_items = Product.objects.all()[:2]
    total = sum(p.price for p in product_items)
    order, _ = Order.objects.get_or_create(
        customer=customer,
        total_amount=total,
        order_date=timezone.now()
    )
    order.products.set(product_items)

    print("Database seeded successfully!")

if __name__ == "__main__":
    run()
