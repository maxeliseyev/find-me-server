from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.images import ImageProcessingError

from .models import Sighting, SightingStatus
from .serializers import (
    SightingCreateSerializer,
    SightingPhotoSerializer,
    SightingPhotoUploadSerializer,
    SightingSerializer,
)
from .services import (
    PhotoLimitReached,
    accept_sighting_photo,
    can_upload_photo,
    photo_upload_token,
)
from .throttling import (
    AnonSightingPhotoThrottle,
    AnonSightingThrottle,
    UserSightingPhotoThrottle,
    UserSightingThrottle,
)


class SightingCreateView(generics.CreateAPIView):
    """POST /api/v1/sightings/ — «Я видел животное».

    Ноль экранов регистрации до сохранения (инвариант 1): авторизация
    предлагается после, чтобы очевидец мог получить ответ владельца.
    """

    serializer_class = SightingCreateSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonSightingThrottle, UserSightingThrottle]

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.is_banned:
            raise PermissionDenied("Аккаунт заблокирован.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sighting = serializer.save()

        # TODO(этап 1, PR фан-аута): fanout_new_sighting.delay(sighting.pk)
        # и recalc_search_zone.delay(sighting.report_id) — задачи ещё заглушки.

        data = SightingSerializer(sighting).data
        # Только в ответе на создание: это единственное доказательство авторства
        # анонимной отметки, в публичной выдаче его быть не должно.
        data["photo_upload_token"] = photo_upload_token(sighting)
        return Response(data, status=201)


class SightingDetailView(generics.RetrieveAPIView):
    """GET /api/v1/sightings/<id>/ — одна отметка.

    Скрытые и помеченные спамом наружу не отдаются (раздел 9).
    """

    serializer_class = SightingSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Sighting.objects.filter(status=SightingStatus.VISIBLE).prefetch_related("photos")


class SightingPhotoUploadView(generics.GenericAPIView):
    """POST /api/v1/sightings/<id>/photos/ — фото к своей отметке.

    Файл кладётся в карантин и обрабатывается Celery; ответ 202 со статусом
    `pending`, ссылка появится в отметке после публикации безопасной копии.
    """

    serializer_class = SightingPhotoUploadSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [AnonSightingPhotoThrottle, UserSightingPhotoThrottle]

    def post(self, request, pk: int):
        user = request.user
        if user.is_authenticated and user.is_banned:
            raise PermissionDenied("Аккаунт заблокирован.")

        sighting = get_object_or_404(Sighting, pk=pk, status=SightingStatus.VISIBLE)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not can_upload_photo(sighting, user, serializer.validated_data.get("upload_token")):
            raise PermissionDenied("Фото добавляет только автор отметки.")

        try:
            photo = accept_sighting_photo(sighting, serializer.validated_data["image"])
        except ImageProcessingError as error:
            raise ValidationError({"image": [str(error)]}) from error
        except PhotoLimitReached as error:
            raise ValidationError({"image": ["У отметки уже максимум фото."]}) from error

        return Response(SightingPhotoSerializer(photo).data, status=202)
