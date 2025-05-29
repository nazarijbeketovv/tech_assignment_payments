from django.db import transaction, IntegrityError
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
import logging
from .models import Payment, Organization, BalanceLog
from .serializers import WebhookSerializer, BalanceSerializer

logger = logging.getLogger(__name__)


class BankWebhookView(APIView):
    @swagger_auto_schema(
        operation_description="Обработка вебхука от банка для начисления баланса организации.",
        request_body=WebhookSerializer,
        responses={
            201: "Вебхук успешно обработан",
            200: "Дублирующий вебхук проигнорирован",
            400: "Неверный формат данных или бизнес-правила",
            404: "Организация не найдена",
            500: "Ошибка сервера",
        },
    )
    def post(self, request):
        serializer = WebhookSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Неверные данные вебхука: {serializer.errors}")
            return Response(
                {"error": "Неверный формат данных", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        operation_id = data["operation_id"]
        payer_inn = data["payer_inn"]
        document_number = data["document_number"]

        # Проверка дублирования операции
        if Payment.objects.filter(operation_id=operation_id).exists():
            logger.info(
                f"Дублирующий вебхук проигнорирован для operation_id: {operation_id}"
            )
            return Response({"status": "success"}, status=status.HTTP_200_OK)

        # Проверка существования организации
        try:
            organization = Organization.objects.get(inn=payer_inn)
        except Organization.DoesNotExist:
            logger.error(f"Организация с ИНН {payer_inn} не найдена")
            return Response(
                {"error": "Организация не найдена"}, status=status.HTTP_404_NOT_FOUND
            )

        # Проверка уникальности номера документа
        if Payment.objects.filter(document_number=document_number).exists():
            logger.error(f"Дублирующий номер документа: {document_number}")
            return Response(
                {"error": "Номер документа должен быть уникальным"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создание платежа и обновление баланса в транзакции
        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    operation_id=operation_id,
                    amount=data["amount"],
                    payer=organization,
                    document_number=document_number,
                    document_date=data["document_date"],
                )
                organization.balance += data["amount"]
                organization.save()

                BalanceLog.objects.create(
                    organization=organization,
                    payment=payment,
                    amount_changed=data["amount"],
                )

            logger.info(
                f"Обработан платеж {operation_id} для ИНН {organization.inn}: {data['amount']}"
            )
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            logger.error(f"Ошибка базы данных при обработке вебхука: {str(e)}")
            return Response(
                {"error": "Ошибка базы данных"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке вебхука: {str(e)}")
            return Response(
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BalanceView(APIView):
    @swagger_auto_schema(
        operation_description="Получение текущего баланса организации по её ИНН.",
        manual_parameters=[
            openapi.Parameter(
                "inn",
                openapi.IN_PATH,
                description="ИНН организации (10 или 12 цифр)",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешный ответ",
                schema=BalanceSerializer,
                examples={
                    "application/json": {"inn": "1234567890", "balance": 145000.00}
                },
            ),
            404: "Организация не найдена",
            500: "Ошибка сервера",
        },
    )
    def get(self, request, inn):
        try:
            organization = Organization.objects.get(inn=inn)
            serializer = BalanceSerializer(organization)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Organization.DoesNotExist:
            logger.error(f"Организация с ИНН {inn} не найдена")
            return Response(
                {"error": "Организация не найдена"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Ошибка при получении баланса для ИНН {inn}: {str(e)}")
            return Response(
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
