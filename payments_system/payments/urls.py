from django.urls import path
from . import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Payments System API",
        default_version="v1",
        description="API for processing bank webhooks and retrieving organization balances",
        terms_of_service="https://www.example.com/terms/",
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("api/webhook/bank/", views.BankWebhookView.as_view(), name="bank_webhook"),
    path(
        "api/organizations/<str:inn>/balance/",
        views.BalanceView.as_view(),
        name="get_balance",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
