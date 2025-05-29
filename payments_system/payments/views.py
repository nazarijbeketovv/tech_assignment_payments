from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
from .models import Payment, Organization, BalanceLog
from .serializers import WebhookSerializer, BalanceSerializer

logger = logging.getLogger(__name__)


class BankWebhookView(APIView):
    @swagger_auto_schema(
        operation_description="Обработка вебхука от банка для начисления баланса организации. "
        "Эндпоинт принимает данные о платеже и обновляет баланс организации, "
        "если операция не является дублирующей.",
        request_body=WebhookSerializer,
        responses={
            201: "Вебхук успешно обработан",
            200: "Дублирующий вебхук проигнорирован",
            400: "Неверный формат данных",
            500: "Ошибка сервера",
        },
    )
    def post(self, request):
        serializer = WebhookSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Неверные данные вебхука: {serializer.errors}")
            return Response(
                {"ошибка": "Неверный формат данных"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        operation_id = data["operation_id"]

        if Payment.objects.filter(operation_id=operation_id).exists():
            logger.info(
                f"Дублирующий вебхук проигнорирован для operation_id: {operation_id}"
            )
            return Response({"статус": "успех"}, status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                (
                    organization,
                    created,
                ) = Organization.objects.select_for_update().get_or_create(
                    inn=data["payer_inn"], defaults={"balance": 0}
                )
                payment = Payment.objects.create(
                    operation_id=operation_id,
                    amount=data["amount"],
                    payer_inn=data["payer_inn"],
                    document_number=data["document_number"],
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
                f"Обработан платеж {operation_id} для ИНН {data['payer_inn']}: {data['amount']}"
            )
            return Response({"статус": "успех"}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            logger.error(f"Ошибка базы данных при обработке вебхука: {str(e)}")
            return Response(
                {"ошибка": "Ошибка базы данных"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке вебхука: {str(e)}")
            return Response(
                {"ошибка": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BalanceView(APIView):
    @swagger_auto_schema(
        operation_description="Получение текущего баланса организации по её ИНН. "
        "Эндпоинт возвращает данные об организации, если она существует.",
        manual_parameters=[
            openapi.Parameter(
                "inn",
                openapi.IN_PATH,
                description="ИНН организации (12 символов)",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: BalanceSerializer,
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
                {"ошибка": "Организация не найдена"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Ошибка при получении баланса для ИНН {inn}: {str(e)}")
            return Response(
                {"ошибка": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
