from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Sighting, SightingStatus
from .serializers import SightingCreateSerializer, SightingSerializer
from .throttling import AnonSightingThrottle, UserSightingThrottle


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

        return Response(SightingSerializer(sighting).data, status=201)


class SightingDetailView(generics.RetrieveAPIView):
    """GET /api/v1/sightings/<id>/ — одна отметка.

    Скрытые и помеченные спамом наружу не отдаются (раздел 9).
    """

    serializer_class = SightingSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Sighting.objects.filter(status=SightingStatus.VISIBLE)
