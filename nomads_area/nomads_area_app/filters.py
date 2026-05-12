import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import Tour


class TourFilter(django_filters.FilterSet):
    TOUR_TYPE_CHOICES = (
        ("group", "Групповой"),
        ("private", "Приватный"),
    )
    SEASON_CHOICES = (
        ("all_year", "Круглый год"),
        ("warm", "Тёплый сезон"),
        ("winter", "Зима"),
    )
    DIFFICULTY_CHOICES = (
        (1, "Лёгкий"),
        (2, "Средний"),
        (3, "Сложный"),
    )

    country = django_filters.NumberFilter(field_name="country_id")
    city = django_filters.NumberFilter(field_name="city_id")
    tour_type = django_filters.ChoiceFilter(
        field_name="tour_type",
        choices=TOUR_TYPE_CHOICES
    )
    difficulty = django_filters.ChoiceFilter(
        field_name="difficulty",
        choices=DIFFICULTY_CHOICES
    )
    season = django_filters.ChoiceFilter(
        field_name="season",
        choices=SEASON_CHOICES
    )
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    duration_min = django_filters.NumberFilter(field_name="duration_days", lookup_expr="gte")
    duration_max = django_filters.NumberFilter(field_name="duration_days", lookup_expr="lte")
    category = django_filters.NumberFilter(field_name="categories__id")
    date_from = django_filters.DateFilter(method="filter_by_date_from")
    exclude_sold_out = django_filters.BooleanFilter(method="filter_exclude_sold_out")

    class Meta:
        model = Tour
        fields = ["country", "city", "tour_type", "difficulty", "season",
                  "price_min", "price_max", "duration_min", "duration_max",
                  "category", "date_from", "exclude_sold_out"]

    def filter_by_date_from(self, queryset, name, value):
        return queryset.filter(
            tour_type="group",
            dates__start_date__gte=value,
            dates__available_spots__gte=1
        ).distinct()

    def filter_exclude_sold_out(self, queryset, name, value):
        if not value:
            return queryset
        today = timezone.now().date()
        return queryset.filter(
            Q(tour_type="private") | Q(
                tour_type="group",
                dates__start_date__gte=today,
                dates__available_spots__gte=1
            )
        ).distinct()
