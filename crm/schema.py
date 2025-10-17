import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
from decimal import Decimal
import re
from django.utils import timezone


# === Types ===
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


# === Mutations ===
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            return CreateCustomer(success=False, message="Email already exists.")

        # Validate phone format if provided
        if phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
            return CreateCustomer(success=False, message="Invalid phone format.")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, success=True, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(graphene.JSONString, required=True)

    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, customers):
        created_customers = []
        errors = []

        for data in customers:
            name = data.get("name")
            email = data.get("email")
            phone = data.get("phone")

            if not name or not email:
                errors.append(f"Missing name or email for record: {data}")
                continue

            if Customer.objects.filter(email=email).exists():
                errors.append(f"Email already exists: {email}")
                continue

            if phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
                errors.append(f"Invalid phone format: {phone}")
                continue

            customer = Customer.objects.create(name=name, email=email, phone=phone)
            created_customers.append(customer)

        return BulkCreateCustomers(created_customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(default_value=0)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, price, stock):
        if price <= 0:
            return CreateProduct(success=False, message="Price must be positive.")
        if stock < 0:
            return CreateProduct(success=False, message="Stock cannot be negative.")

        product = Product.objects.create(name=name, price=Decimal(price), stock=stock)
        return CreateProduct(product=product, success=True, message="Product created successfully.")


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(default_value=timezone.now)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(success=False, message="Invalid customer ID.")

        if not product_ids:
            return CreateOrder(success=False, message="At least one product must be selected.")

        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            return CreateOrder(success=False, message="One or more invalid product IDs.")

        total = sum([p.price for p in products])

        order = Order.objects.create(customer=customer, order_date=order_date or timezone.now(), total_amount=total)
        order.products.set(products)
        order.save()

        return CreateOrder(order=order, success=True, message="Order created successfully.")


# === Root Schema ===
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()


schema = graphene.Schema(query=Query, mutation=Mutation)