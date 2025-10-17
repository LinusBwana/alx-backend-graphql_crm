import graphene
from django.utils import timezone
from .models import Customer, Product, Order


# ==========================
# GraphQL Object Types
# ==========================

# Define your GraphQL type
class CustomerType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    email = graphene.String()
    phone = graphene.String()

class ProductType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    price = graphene.Float()
    stock = graphene.Int()

class OrderType(graphene.ObjectType):
    id = graphene.ID()
    customer = graphene.Field(CustomerType)
    products = graphene.List(ProductType)
    total_amount = graphene.Float()
    order_date = graphene.DateTime()

    def resolve_products(self, info):
        return self.products.all() if hasattr(self, "products") else []


# ==========================
# Input Types
# ==========================

# Define an input type correctly
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=True)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
    order_date = graphene.DateTime()


# ==========================
# Customer Mutations
# ==========================

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone):
        if Customer.objects.filter(email=email).exists():
            return CreateCustomer(customer=None, message="Email already exists.")
        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully!")


# Fixed BulkCreateCustomers mutation
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(graphene.NonNull(CustomerInput), required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        created_customers = []
        errors = []
        for data in customers:
            if Customer.objects.filter(email=data.email).exists():
                errors.append(f"Email already exists: {data.email}")
                continue
            created_customers.append(Customer.objects.create(
                name=data.name,
                email=data.email,
                phone=data.phone
            ))
        return BulkCreateCustomers(customers=created_customers, errors=errors)


# ==========================
# Product Mutations
# ==========================

# Existing CreateProduct mutation
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)
    message = graphene.String()

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            return CreateProduct(product=None, message="Price must be positive.")
        if stock < 0:
            return CreateProduct(product=None, message="Stock cannot be negative.")
        if Product.objects.filter(name=name).exists():
            return CreateProduct(product=None, message="Product already exists.")
        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product, message="Product created successfully!")


# ==========================
# Order Mutations
# ==========================

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(order=None, message="Invalid customer ID.")

        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            return CreateOrder(order=None, message="No valid products found.")

        if len(products) != len(product_ids):
            return CreateOrder(order=None, message="Some product IDs are invalid.")

        total_amount = sum([p.price for p in products])
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=order_date or timezone.now()
        )
        order.products.set(products)
        return CreateOrder(order=order, message="Order created successfully!")


# ==========================
# Root query
# ==========================

class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()


# ==========================
# Root mutation
# ==========================

class Mutation(graphene.ObjectType):
    # Customer mutations
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()

    # Product mutations
    create_product = CreateProduct.Field()

    # Order mutations
    create_order = CreateOrder.Field()