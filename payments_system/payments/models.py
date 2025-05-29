from django.db import models
from django.core.validators import RegexValidator
import uuid


class Organization(models.Model):
    inn_validator = RegexValidator(
        regex=r"^\d{10}$|^\d{12}$", message="ИНН должен состоять из 10 или 12 цифр."
    )
    inn = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        validators=[inn_validator],
        verbose_name="ИНН",
        help_text="Идентификационный Номер Налогоплательщика организации.",
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Баланс",
        help_text="Текущий баланс организации.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "organizations"
        ordering = ["inn"]
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return f"Организация ИНН: {self.inn} | Баланс: {self.balance}"


class Payment(models.Model):
    operation_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name="Идентификатор операции",
    )
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Сумма платежа"
    )
    payer = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Плательщик",
    )
    document_number = models.CharField(
        max_length=50, unique=True, verbose_name="Номер документа"
    )
    document_date = models.DateTimeField(verbose_name="Дата документа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = "payments"
        ordering = ["-document_date"]
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"Платеж {self.operation_id} | Сумма: {self.amount} | Документ: {self.document_number} | Плательщик: {self.payer.inn}"


class BalanceLog(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="balance_logs",
        verbose_name="Организация",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="balance_logs",
        verbose_name="Платеж",
    )
    amount_changed = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Сумма изменения"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Время изменения"
    )

    class Meta:
        db_table = "balance_logs"
        ordering = ["-timestamp"]
        verbose_name = "Лог изменения баланса"
        verbose_name_plural = "Логи изменения баланса"

    def __str__(self):
        return f"Лог для {self.organization.inn} | Изменение: {self.amount_changed} | Время: {self.timestamp}"
