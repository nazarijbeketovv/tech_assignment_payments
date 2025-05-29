from rest_framework import serializers
from .models import Organization


class WebhookSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField(
        help_text="Уникальный идентификатор операции в формате UUID."
    )
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, help_text="Сумма платежа."
    )
    payer_inn = serializers.CharField(max_length=12, help_text="ИНН плательщика.")
    document_number = serializers.CharField(
        max_length=50, help_text="Уникальный номер документа."
    )
    document_date = serializers.DateTimeField(help_text="Дата и время документа.")


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["inn", "balance"]
