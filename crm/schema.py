import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from crm.models import Product
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# ==========================
# GraphQL Object Types
# ==========================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        filterset_class = CustomerFilter


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        filterset_class = ProductFilter


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        filterset_class = OrderFilter


# ==========================
# Query with Filtering and Sorting
# ==========================
class Query(graphene.ObjectType):
    all_customers = graphene.Field(
        graphene.List(CustomerType),
        order_by=graphene.String(),
        name_Icontains=graphene.String(),
        email_Icontains=graphene.String(),
    )
    all_products = graphene.Field(
        graphene.List(ProductType),
        order_by=graphene.String(),
        price_Gte=graphene.Float(),
        price_Lte=graphene.Float(),
    )
    all_orders = graphene.Field(
        graphene.List(OrderType),
        order_by=graphene.String(),
        total_amount_Gte=graphene.Float(),
        total_amount_Lte=graphene.Float(),
    )

    # ==========================
    # CUSTOMERS
    # ==========================
    def resolve_all_customers(self, info, order_by=None, **filters):
        qs = Customer.objects.all()
        name = filters.get("name_Icontains")
        email = filters.get("email_Icontains")

        if name:
            qs = qs.filter(name__icontains=name)
        if email:
            qs = qs.filter(email__icontains=email)
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    # ==========================
    # PRODUCTS
    # ==========================
    def resolve_all_products(self, info, order_by=None, **filters):
        qs = Product.objects.all()
        price_gte = filters.get("price_Gte")
        price_lte = filters.get("price_Lte")

        if price_gte:
            qs = qs.filter(price__gte=price_gte)
        if price_lte:
            qs = qs.filter(price__lte=price_lte)
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    # ==========================
    # ORDERS
    # ==========================
    def resolve_all_orders(self, info, order_by=None, **filters):
        qs = Order.objects.all()
        amount_gte = filters.get("total_amount_Gte")
        amount_lte = filters.get("total_amount_Lte")

        if amount_gte:
            qs = qs.filter(total_amount__gte=amount_gte)
        if amount_lte:
            qs = qs.filter(total_amount__lte=amount_lte)
        if order_by:
            qs = qs.order_by(order_by)
        return qs


# ==========================
# Mutation for Low-Stock Products
# ==========================
class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        # No arguments needed for this mutation
        pass

    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(ProductType)

    def mutate(self, info):
        # Find products with stock < 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []

        for product in low_stock_products:
            product.stock += 10  # simulate restocking
            product.save()
            updated.append(product)

        if updated:
            message = f"{len(updated)} products restocked successfully."
        else:
            message = "No low-stock products found."

        return UpdateLowStockProducts(
            success=True,
            message=message,
            updated_products=updated
        )


# ==========================
# Root Mutation Placeholder
# ==========================
class Mutation(graphene.ObjectType):
    dummy = graphene.String(description="Placeholder field for schema validation")

    def resolve_dummy(root, info):
        return "Mutation root active"


# ==========================
# Schema Export
# ==========================
schema = graphene.Schema(query=Query, mutation=Mutation)