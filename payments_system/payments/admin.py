from django.contrib import admin
from django.utils.html import format_html
from .models import Organization, Payment, BalanceLog


class BalanceLogInline(admin.TabularInline):
    model = BalanceLog
    extra = 0
    readonly_fields = ("amount_changed", "timestamp", "payment_link")
    fields = ("payment_link", "amount_changed", "timestamp")
    can_delete = False

    def payment_link(self, obj):
        if obj.payment_id:
            url = f"/admin/{obj.payment._meta.app_label}/{obj.payment._meta.model_name}/{obj.payment_id}/change/"
            return format_html("<a href='{}'>{}</a>", url, obj.payment.document_number)
        return "-"

    payment_link.short_description = "Платеж"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "inn",
        "formatted_balance",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at",)
    search_fields = ("inn",)
    list_per_page = 25
    ordering = ("inn",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [BalanceLogInline]

    fieldsets = (
        (None, {"fields": ("inn", "balance")}),
        (
            "Метаданные",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def formatted_balance(self, obj):
        return f"{obj.balance:,.2f} RUB"

    formatted_balance.short_description = "Баланс"

    actions = ["reset_balances"]

    @admin.action(description="Сбросить балансы всех выбранных организаций в 0")
    def reset_balances(self, request, queryset):
        updated = queryset.update(balance=0)
        self.message_user(request, f"Сброшено балансов для {updated} организаций.")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "operation_id",
        "amount",
        "payer_link",
        "document_number",
        "document_date",
        "created_at",
    )
    list_filter = ("document_date", "payer__inn")
    search_fields = ("operation_id", "document_number", "payer__inn")
    date_hierarchy = "document_date"
    ordering = ("-document_date",)
    readonly_fields = ("created_at",)
    inlines = [BalanceLogInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "operation_id",
                    "payer",
                    "amount",
                    "document_number",
                    "document_date",
                )
            },
        ),
        (
            "Дополнительно",
            {
                "classes": ("collapse",),
                "fields": ("created_at",),
            },
        ),
    )

    def payer_link(self, obj):
        url = f"/admin/{obj.payer._meta.app_label}/{obj.payer._meta.model_name}/{obj.payer_id}/change/"
        return format_html("<a href='{}'>{}</a>", url, obj.payer.inn)

    payer_link.short_description = "Плательщик"


@admin.register(BalanceLog)
class BalanceLogAdmin(admin.ModelAdmin):
    list_display = (
        "organization_link",
        "payment_link",
        "amount_changed",
        "timestamp",
    )
    list_filter = ("timestamp", "organization__inn")
    search_fields = ("organization__inn", "payment__document_number")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
    readonly_fields = (
        "organization",
        "payment",
        "amount_changed",
        "timestamp",
    )

    def organization_link(self, obj):
        url = f"/admin/{obj.organization._meta.app_label}/{obj.organization._meta.model_name}/{obj.organization_id}/change/"
        return format_html("<a href='{}'>{}</a>", url, obj.organization.inn)

    organization_link.short_description = "Организация"

    def payment_link(self, obj):
        url = f"/admin/{obj.payment._meta.app_label}/{obj.payment._meta.model_name}/{obj.payment_id}/change/"
        return format_html("<a href='{}'>{}</a>", url, obj.payment.document_number)

    payment_link.short_description = "Платеж"
