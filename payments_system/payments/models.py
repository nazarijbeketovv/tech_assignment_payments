from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
import uuid


class Organization(models.Model):
    """
    Модель для хранения данных об организации.

    Эта модель используется для учета организаций, участвующих в платежной системе.
    Каждая организация идентифицируется по уникальному ИНН (Идентификационный Номер Налогоплательщика),
    имеет баланс средств и временные метки создания и обновления для отслеживания изменений.
    """

    inn_validator = RegexValidator(
        regex=r"^\d{10}$|^\d{12}$", message="ИНН должен состоять из 10 или 12 цифр."
    )
    inn = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        validators=[inn_validator],
        verbose_name="ИНН",
        help_text="Идентификационный Номер Налогоплательщика организации. Уникальный номер, состоящий из 10 или 12 цифр, используемый для идентификации организации в системе.",
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Баланс",
        help_text="Текущий баланс организации в денежных единицах. Указывает доступную сумму средств с точностью до двух знаков после запятой. По умолчанию равен 0.00.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата и время создания записи об организации в базе данных. Устанавливается автоматически при создании.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Дата и время последнего обновления записи об организации. Автоматически обновляется при каждом изменении данных.",
    )

    class Meta:
        db_table = "organizations"
        ordering = ["inn"]
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return f"Организация ИНН: {self.inn} | Баланс: {self.balance}"


class Payment(models.Model):
    """
    Модель для учета платежей, совершаемых организациями.

    Хранит информацию о каждом платеже, включая уникальный идентификатор, сумму, плательщика,
    номер и дату документа. Используется для отслеживания финансовых операций и их связи с организациями.
    """

    operation_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name="Идентификатор операции",
        help_text="Уникальный идентификатор платежа в формате UUID. Генерируется автоматически и используется для однозначной идентификации каждой операции.",
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Сумма платежа",
        help_text="Сумма платежа в денежных единицах. Должна быть положительной (не менее 0.01) и указывается с точностью до двух знаков после запятой.",
    )
    payer = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Плательщик",
        help_text="Организация, которая совершает платеж. Ссылается на модель Organization. При удалении организации все связанные платежи также удаляются.",
    )
    document_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Номер документа",
        help_text="Уникальный номер документа, подтверждающего платеж. Используется для идентификации платежа в бухгалтерских системах.",
    )
    document_date = models.DateTimeField(
        verbose_name="Дата документа",
        help_text="Дата и время, указанные в документе платежа. Определяет, когда платеж был официально зарегистрирован.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата и время создания записи о платеже в базе данных. Устанавливается автоматически при добавлении записи.",
    )

    class Meta:
        db_table = "payments"
        ordering = ["-document_date"]
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"Платеж {self.operation_id} | Сумма: {self.amount} | Документ: {self.document_number}"


class BalanceLog(models.Model):
    """
    Модель для логирования изменений баланса организаций.

    Используется для записи всех изменений баланса, связанных с платежами. Фиксирует, какая организация,
    какой платеж и на какую сумму изменили баланс, а также время этих изменений.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="balance_logs",
        verbose_name="Организация",
        help_text="Организация, чей баланс был изменен. Ссылается на модель Organization. При удалении организации все связанные логи удаляются.",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="balance_logs",
        verbose_name="Платеж",
        help_text="Платеж, который вызвал изменение баланса. Ссылается на модель Payment. При удалении платежа связанные логи также удаляются.",
    )
    amount_changed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Сумма изменения",
        help_text="Сумма, на которую был изменен баланс организации. Указывается с точностью до двух знаков после запятой и должна быть не менее 0.01.",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Время изменения",
        help_text="Дата и время, когда произошло изменение баланса. Устанавливается автоматически и индексируется для ускорения поиска.",
    )

    class Meta:
        db_table = "balance_logs"
        ordering = ["-timestamp"]
        verbose_name = "Лог изменения баланса"
        verbose_name_plural = "Логи изменения баланса"

    def __str__(self):
        return f"Лог для {self.organization.inn} | Изменение: {self.amount_changed} | Время: {self.timestamp}"
