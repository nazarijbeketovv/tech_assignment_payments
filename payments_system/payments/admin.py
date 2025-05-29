from django.contrib import admin

from payments.models import Organization, Payment, BalanceLog


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("inn", "balance", "created_at", "updated_at")
    search_fields = ("inn",)
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "operation_id",
        "amount",
        "payer",
        "document_number",
        "document_date",
        "created_at",
    )
    search_fields = ("operation_id", "document_number", "payer__inn")
    list_filter = ("document_date", "created_at")
    readonly_fields = ("created_at",)


@admin.register(BalanceLog)
class BalanceLogAdmin(admin.ModelAdmin):
    list_display = ("organization", "payment", "amount_changed", "timestamp")
    search_fields = ("organization__inn", "payment__operation_id")
    list_filter = ("timestamp",)
    readonly_fields = ("timestamp",)
