from rest_framework import generics
from rest_framework.permissions import AllowAny

from ..models import SiteSettings, TeamMember
from ..serializers import SiteSettingsSerializer, TeamMemberSerializer
from .common import cache_public_api


@cache_public_api
class SiteSettingsView(generics.RetrieveAPIView):
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return SiteSettings.get_settings()


@cache_public_api
class TeamMemberListView(generics.ListAPIView):
    queryset = TeamMember.objects.filter(is_active=True)
    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]
