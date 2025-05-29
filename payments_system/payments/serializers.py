from rest_framework import serializers

from payments.models import Organization, Payment


class WebhookSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField(
        help_text="Уникальный идентификатор операции. Должен быть в формате UUID (например, '550e8400-e29b-41d4-a716-446655440000'). Используется для идентификации платежа и предотвращения дублирования."
    )
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Сумма платежа. Должна быть положительным числом с максимум 15 знаками, из которых 2 после запятой (например, 1234567890123.45). Минимальное значение: 0.01.",
    )
    payer_inn = serializers.CharField(
        max_length=12,
        help_text="ИНН организации-плательщика. Должен состоять из 10 или 12 цифр и соответствовать существующей организации в базе данных (например, '1234567890' или '123456789012').",
    )
    document_number = serializers.CharField(
        max_length=50,
        help_text="Уникальный номер документа. Строка длиной до 50 символов, которая не должна повторяться в других платежах (например, 'DOC-2023-001').",
    )
    document_date = serializers.DateTimeField(
        help_text="Дата и время документа в формате ISO 8601 (например, '2024-04-27T21:00:00Z'). Указывает, когда был создан документ."
    )

    def validate_payer_inn(self, value):
        if not Organization.objects.filter(inn=value).exists():
            raise serializers.ValidationError("Организации с таким ИНН не существует.")
        return value

    def validate_document_number(self, value):
        if Payment.objects.filter(document_number=value).exists():
            raise serializers.ValidationError("Номер документа должен быть уникальным.")
        return value


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["inn", "balance"]
        extra_kwargs = {
            "inn": {
                "help_text": "ИНН организации. Уникальный идентификатор из 10 или 12 цифр (например, '1234567890' или '123456789012')."
            },
            "balance": {
                "help_text": "Текущий баланс организации. Число с максимум 15 знаками, из которых 2 после запятой (например, 1500.75). Отражает сумму доступных средств."
            },
        }
