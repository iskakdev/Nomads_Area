from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import ExtraService, FAQ, SiteSettings, TeamMember
from .common import LocalizedModelSerializer, _file_url


class SiteSettingsSerializer(LocalizedModelSerializer):
    localized_fields = ("about_text", "privacy_policy")
    class Meta:
        model = SiteSettings
        fields = ["id", "phone", "whatsapp", "email",
                  "instagram_url", "facebook_url", "youtube_url", "tiktok_url", "tripadvisor_url",
                  "about_text", "about_video_url",
                  "years_experience", "tourists_count", "routes_count",
                  "reviews_enabled", "elfsight_google_reviews_app_id", "privacy_policy"]

class TeamMemberSerializer(LocalizedModelSerializer):
    localized_fields = ("full_name", "position", "description")
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = ["id", "full_name", "position", "description", "photo", "photo_url"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo_url(self, obj):
        return _file_url(obj, "photo", self.context.get("request"))

class FAQSerializer(LocalizedModelSerializer):
    localized_fields = ("question", "answer")
    class Meta:
        model = FAQ
        fields = ["question", "answer"]

class ExtraServiceSerializer(LocalizedModelSerializer):
    localized_fields = ("title", "description", "features", "price_label")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ExtraService
        fields = ["id", "title", "description", "image", "image_url", "features", "price", "currency", "price_label"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))
