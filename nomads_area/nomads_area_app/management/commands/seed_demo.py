from datetime import timedelta
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from nomads_area_app.models import (
    SiteSettings,
    Country,
    City,
    TourCategory,
    Tour,
    TourDate,
    Attraction,
    TransferRoute,
    VehicleType,
    TeamMember,
)


TRIPADVISOR_URL = "https://www.tripadvisor.com/Attraction_Review-g293948-d27931796-Reviews-Nomads_Area-Bishkek.html"


class Command(BaseCommand):
    help = "Seed clean realistic bilingual demo data"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Deleting old data..."))

        TourDate.objects.all().delete()
        VehicleType.objects.all().delete()
        TransferRoute.objects.all().delete()
        Attraction.objects.all().delete()
        Tour.objects.all().delete()
        TeamMember.objects.all().delete()
        TourCategory.objects.all().delete()
        City.objects.all().delete()
        Country.objects.all().delete()
        SiteSettings.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Creating site settings..."))

        SiteSettings.objects.create(
            phone="+996 555 000 000",
            whatsapp="+996 555 000 000",
            email="info@nomadsarea.com",
            instagram_url="https://www.instagram.com/nomads_area",
            youtube_url="https://www.youtube.com/@NomadsArea",
            tiktok_url="https://www.tiktok.com/@nomads.area",
            tripadvisor_url=TRIPADVISOR_URL,
            about_text="Nomads Area organizes authentic tours across Kyrgyzstan and Central Asia with local guides, mountain routes, cultural experiences and comfortable transfers.",
            about_text_ru="Nomads Area организует аутентичные туры по Кыргызстану и Центральной Азии с местными гидами, горными маршрутами, культурными программами и комфортабельными трансферами.",
            about_text_en="Nomads Area organizes authentic tours across Kyrgyzstan and Central Asia with local guides, mountain routes, cultural experiences and comfortable transfers.",
            about_video_url="https://www.youtube.com/@NomadsArea",
            years_experience=5,
            tourists_count=1250,
            routes_count=42,
        )

        self.stdout.write(self.style.SUCCESS("Creating countries..."))

        kyrgyzstan = Country.objects.create(
            country_name="Kyrgyzstan",
            country_name_ru="Кыргызстан",
            country_name_en="Kyrgyzstan",
            hero_description="Mountain country with alpine lakes, nomadic culture, horse trekking and yurt camps.",
            hero_description_ru="Горная страна с высокогорными озёрами, кочевой культурой, конными походами и юрточными лагерями.",
            hero_description_en="Mountain country with alpine lakes, nomadic culture, horse trekking and yurt camps.",
        )

        kazakhstan = Country.objects.create(
            country_name="Kazakhstan",
            country_name_ru="Казахстан",
            country_name_en="Kazakhstan",
            hero_description="Central Asian country with canyons, mountains, steppe landscapes and modern cities.",
            hero_description_ru="Центральноазиатская страна с каньонами, горами, степными ландшафтами и современными городами.",
            hero_description_en="Central Asian country with canyons, mountains, steppe landscapes and modern cities.",
        )

        uzbekistan = Country.objects.create(
            country_name="Uzbekistan",
            country_name_ru="Узбекистан",
            country_name_en="Uzbekistan",
            hero_description="Silk Road destination with ancient cities, bazaars, Islamic architecture and rich culture.",
            hero_description_ru="Направление Шёлкового пути с древними городами, базарами, исламской архитектурой и богатой культурой.",
            hero_description_en="Silk Road destination with ancient cities, bazaars, Islamic architecture and rich culture.",
        )

        self.stdout.write(self.style.SUCCESS("Creating cities..."))

        cities_data = [
            (kyrgyzstan, "Бишкек", "Bishkek"),
            (kyrgyzstan, "Каракол", "Karakol"),
            (kyrgyzstan, "Нарын", "Naryn"),
            (kyrgyzstan, "Ош", "Osh"),
            (kazakhstan, "Алматы", "Almaty"),
            (kazakhstan, "Астана", "Astana"),
            (kazakhstan, "Шымкент", "Shymkent"),
            (uzbekistan, "Ташкент", "Tashkent"),
            (uzbekistan, "Самарканд", "Samarkand"),
            (uzbekistan, "Бухара", "Bukhara"),
            (uzbekistan, "Хива", "Khiva"),
        ]

        city_map = {}

        for country, name_ru, name_en in cities_data:
            city = City.objects.create(
                country=country,
                city_name=name_en,
                city_name_ru=name_ru,
                city_name_en=name_en,
            )
            city_map[name_en] = city

        self.stdout.write(self.style.SUCCESS("Creating categories..."))

        categories_data = [
            ("Приключения", "Adventure"),
            ("Конный туризм", "Horse Trekking"),
            ("Культурные туры", "Cultural Tours"),
            ("Зимние туры", "Winter Tours"),
            ("Фототуры", "Photography"),
            ("Трекинг", "Hiking"),
            ("Люкс", "Luxury"),
            ("Кочевой опыт", "Nomad Experience"),
        ]

        category_map = {}

        for name_ru, name_en in categories_data:
            category = TourCategory.objects.create(
                name=name_en,
                name_ru=name_ru,
                name_en=name_en,
            )
            category_map[name_en] = category

        self.stdout.write(self.style.SUCCESS("Creating tours..."))

        tours_data = [
            {
                "title_ru": "Конный тур на Сонг-Кёль",
                "title_en": "Song Kol Horse Trek",
                "country": kyrgyzstan,
                "city": "Naryn",
                "tour_type": "group",
                "season": "warm",
                "duration": 5,
                "difficulty": 2,
                "price": 890,
                "categories": ["Adventure", "Horse Trekking", "Nomad Experience"],
                "tags": ["mountains", "horse riding", "nomads"],
                "desc_ru": "Пятидневный конный тур к высокогорному озеру Сонг-Кёль. Ночёвки в юртах, встреча с кочевниками, горные пейзажи и незабываемые закаты.",
                "desc_en": "Five-day horse trek to the high-altitude Song Kol Lake. Yurt stays, meetings with nomads, mountain landscapes and unforgettable sunsets.",
            },
            {
                "title_ru": "Экспедиция на озеро Кель-Суу",
                "title_en": "Kel Suu Lake Expedition",
                "country": kyrgyzstan,
                "city": "Naryn",
                "tour_type": "group",
                "season": "warm",
                "duration": 6,
                "difficulty": 3,
                "price": 1180,
                "categories": ["Adventure", "Hiking", "Photography"],
                "tags": ["lake", "mountains", "offroad"],
                "desc_ru": "Сложная экспедиция на джипах и пешком к бирюзовому озеру Кель-Суу на высоте около 3500 метров.",
                "desc_en": "Challenging jeep and hiking expedition to the turquoise Kel Suu Lake at around 3500 meters.",
            },
            {
                "title_ru": "Побег на Иссык-Куль",
                "title_en": "Issyk Kul Escape",
                "country": kyrgyzstan,
                "city": "Karakol",
                "tour_type": "private",
                "season": "all_year",
                "duration": 3,
                "difficulty": 1,
                "price": 520,
                "categories": ["Adventure", "Cultural Tours"],
                "tags": ["lake", "culture", "comfort"],
                "desc_ru": "Расслабляющий частный тур на озеро Иссык-Куль с ущельями, горячими источниками и комфортным трансфером.",
                "desc_en": "Relaxing private tour to Issyk Kul Lake with canyons, hot springs and comfortable transfers.",
            },
            {
                "title_ru": "Путешествие в Джеты-Огуз",
                "title_en": "Jeti Oguz Journey",
                "country": kyrgyzstan,
                "city": "Karakol",
                "tour_type": "group",
                "season": "warm",
                "duration": 4,
                "difficulty": 2,
                "price": 640,
                "categories": ["Adventure", "Photography"],
                "tags": ["canyon", "mountains", "trekking"],
                "desc_ru": "Поход по живописному ущелью Джеты-Огуз со скалами красного цвета, юртами и горными видами.",
                "desc_en": "Hike through the scenic Jeti Oguz gorge with red rock formations, yurts and mountain views.",
            },
            {
                "title_ru": "Зима в Караколе",
                "title_en": "Winter in Karakol",
                "country": kyrgyzstan,
                "city": "Karakol",
                "tour_type": "group",
                "season": "winter",
                "duration": 5,
                "difficulty": 2,
                "price": 760,
                "categories": ["Winter Tours", "Adventure"],
                "tags": ["winter", "mountains", "ski"],
                "desc_ru": "Зимний тур в Каракол с катанием на лыжах, баней, уютными вечерами и горными пейзажами.",
                "desc_en": "Winter tour in Karakol with skiing, banya, cozy evenings and mountain scenery.",
            },
            {
                "title_ru": "Однодневный тур в Ала-Арчу",
                "title_en": "Ala Archa One Day Tour",
                "country": kyrgyzstan,
                "city": "Bishkek",
                "tour_type": "private",
                "season": "all_year",
                "duration": 1,
                "difficulty": 1,
                "price": 120,
                "categories": ["Hiking", "Photography"],
                "tags": ["hiking", "nature", "bishkek"],
                "desc_ru": "Лёгкий треккинг в национальном парке Ала-Арча в 40 минутах от Бишкека.",
                "desc_en": "Easy trekking in Ala Archa National Park, just 40 minutes from Bishkek.",
            },
            {
                "title_ru": "Культурный уикенд в Оше",
                "title_en": "Osh Cultural Weekend",
                "country": kyrgyzstan,
                "city": "Osh",
                "tour_type": "private",
                "season": "all_year",
                "duration": 2,
                "difficulty": 1,
                "price": 300,
                "categories": ["Cultural Tours"],
                "tags": ["history", "bazaar", "culture"],
                "desc_ru": "Знакомство с древним Ошем: базар, гора Сулайман-Тоо, местная кухня и ремёсла.",
                "desc_en": "Explore ancient Osh: bazaar, Sulaiman Too mountain, local cuisine and crafts.",
            },
            {
                "title_ru": "Уикенд в Чарынском каньоне",
                "title_en": "Charyn Canyon Weekend",
                "country": kazakhstan,
                "city": "Almaty",
                "tour_type": "group",
                "season": "warm",
                "duration": 2,
                "difficulty": 1,
                "price": 300,
                "categories": ["Adventure", "Photography"],
                "tags": ["canyon", "nature", "weekend"],
                "desc_ru": "Двухдневный тур в Чарынский каньон с прогулкой по дну каньона и ночёвкой в кемпинге.",
                "desc_en": "Two-day tour to Charyn Canyon with a walk along the canyon floor and overnight camping.",
            },
            {
                "title_ru": "Приключение на озёрах Кольсай",
                "title_en": "Kolsai Lakes Adventure",
                "country": kazakhstan,
                "city": "Almaty",
                "tour_type": "group",
                "season": "warm",
                "duration": 3,
                "difficulty": 2,
                "price": 520,
                "categories": ["Adventure", "Hiking", "Photography"],
                "tags": ["lakes", "hiking", "mountains"],
                "desc_ru": "Поход к озёрам Кольсай с ночёвками у воды, горными тропами и красивыми видами.",
                "desc_en": "Trek to Kolsai Lakes with lakeside stays, mountain trails and beautiful views.",
            },
            {
                "title_ru": "Горы Алматы",
                "title_en": "Almaty Mountains Private Tour",
                "country": kazakhstan,
                "city": "Almaty",
                "tour_type": "private",
                "season": "all_year",
                "duration": 2,
                "difficulty": 1,
                "price": 430,
                "categories": ["Luxury", "Adventure"],
                "tags": ["mountains", "comfort", "city"],
                "desc_ru": "Комфортный частный тур по горам вокруг Алматы: Медеу, Шымбулак и Большое Алматинское озеро.",
                "desc_en": "Comfortable private tour around Almaty mountains: Medeu, Shymbulak and Big Almaty Lake.",
            },
            {
                "title_ru": "Уикенд в Астане",
                "title_en": "Astana City Break",
                "country": kazakhstan,
                "city": "Astana",
                "tour_type": "private",
                "season": "all_year",
                "duration": 2,
                "difficulty": 1,
                "price": 350,
                "categories": ["Cultural Tours"],
                "tags": ["city", "architecture", "culture"],
                "desc_ru": "Знакомство с современной столицей Казахстана: Байтерек, мечети, музеи и городская архитектура.",
                "desc_en": "Explore Kazakhstan's modern capital: Bayterek, mosques, museums and city architecture.",
            },
            {
                "title_ru": "Культурный маршрут в Туркестан",
                "title_en": "Turkistan Cultural Route",
                "country": kazakhstan,
                "city": "Shymkent",
                "tour_type": "group",
                "season": "all_year",
                "duration": 4,
                "difficulty": 1,
                "price": 690,
                "categories": ["Cultural Tours", "Photography"],
                "tags": ["history", "architecture", "culture"],
                "desc_ru": "Маршрут через Шымкент и Туркестан с посещением мавзолея Ходжи Ахмеда Ясави.",
                "desc_en": "Route through Shymkent and Turkistan with a visit to the Mausoleum of Khoja Ahmed Yasawi.",
            },
            {
                "title_ru": "Самарканд - жемчужина Шёлкового пути",
                "title_en": "Samarkand Silk Road",
                "country": uzbekistan,
                "city": "Samarkand",
                "tour_type": "group",
                "season": "all_year",
                "duration": 4,
                "difficulty": 1,
                "price": 720,
                "categories": ["Cultural Tours", "Photography"],
                "tags": ["silk road", "history", "architecture"],
                "desc_ru": "Погружение в историю Самарканда: Регистан, Шахи-Зинда, базары и традиционная кухня.",
                "desc_en": "Immersion in Samarkand history: Registan, Shah-i-Zinda, bazaars and traditional cuisine.",
            },
            {
                "title_ru": "Древняя Бухара",
                "title_en": "Bukhara Ancient City",
                "country": uzbekistan,
                "city": "Bukhara",
                "tour_type": "group",
                "season": "all_year",
                "duration": 3,
                "difficulty": 1,
                "price": 580,
                "categories": ["Cultural Tours"],
                "tags": ["old city", "history", "bazaar"],
                "desc_ru": "Прогулка по древней Бухаре с медресе, минаретами, базарами и восточной атмосферой.",
                "desc_en": "A walk through ancient Bukhara with madrasahs, minarets, bazaars and oriental atmosphere.",
            },
            {
                "title_ru": "Открытие Хивы",
                "title_en": "Khiva Discovery",
                "country": uzbekistan,
                "city": "Khiva",
                "tour_type": "private",
                "season": "all_year",
                "duration": 3,
                "difficulty": 1,
                "price": 610,
                "categories": ["Cultural Tours", "Luxury"],
                "tags": ["old town", "history", "culture"],
                "desc_ru": "Частный тур по Хиве с прогулкой по Ичан-Кале и комфортным проживанием.",
                "desc_en": "Private tour in Khiva with a walk through Itchan Kala and comfortable accommodation.",
            },
            {
                "title_ru": "Гастротур по Узбекистану",
                "title_en": "Uzbek Food Discovery",
                "country": uzbekistan,
                "city": "Tashkent",
                "tour_type": "private",
                "season": "all_year",
                "duration": 2,
                "difficulty": 1,
                "price": 390,
                "categories": ["Cultural Tours"],
                "tags": ["food", "bazaar", "city"],
                "desc_ru": "Гастрономическое путешествие по Ташкенту: базар Чорсу, плов, лепёшки и сладости.",
                "desc_en": "Gastronomic journey through Tashkent: Chorsu Bazaar, plov, bread and sweets.",
            },
            {
                "title_ru": "Большой тур по Узбекистану",
                "title_en": "Uzbekistan Culture Tour",
                "country": uzbekistan,
                "city": "Tashkent",
                "tour_type": "group",
                "season": "all_year",
                "duration": 7,
                "difficulty": 1,
                "price": 1350,
                "categories": ["Cultural Tours", "Photography"],
                "tags": ["silk road", "history", "culture"],
                "desc_ru": "Недельный тур по Узбекистану: Ташкент, Самарканд, Бухара и Хива с гидом и трансферами.",
                "desc_en": "One-week tour across Uzbekistan: Tashkent, Samarkand, Bukhara and Khiva with guide and transfers.",
            },
        ]

        included_ru = "Услуги гида\nТранспорт по программе\nПроживание\nЗавтраки\nЛокальные активности"
        included_en = "Guide services\nTransport during the tour\nAccommodation\nBreakfast\nLocal experiences"
        not_included_ru = "Международные перелёты\nСтраховка\nЛичные расходы\nДополнительные активности"
        not_included_en = "International flights\nTravel insurance\nPersonal expenses\nExtra activities"

        tours = []

        for item in tours_data:
            tour = Tour.objects.create(
                title=item["title_en"],
                title_ru=item["title_ru"],
                title_en=item["title_en"],
                tour_type=item["tour_type"],
                season=item["season"],
                country=item["country"],
                city=city_map[item["city"]],
                duration_days=item["duration"],
                difficulty=item["difficulty"],
                currency="USD",
                price=item["price"],
                max_people=random.randint(4, 10),
                description=item["desc_en"],
                description_ru=item["desc_ru"],
                description_en=item["desc_en"],
                included=included_en,
                included_ru=included_ru,
                included_en=included_en,
                not_included=not_included_en,
                not_included_ru=not_included_ru,
                not_included_en=not_included_en,
                activity_tags=item["tags"],
                tripadvisor_url=TRIPADVISOR_URL,
                is_active=True,
            )

            tour.categories.set([category_map[name] for name in item["categories"]])
            tours.append(tour)

        self.stdout.write(self.style.SUCCESS("Creating tour dates..."))

        today = timezone.now().date()

        for tour in tours:
            if tour.tour_type == "group":
                for i in range(4):
                    start = today + timedelta(days=14 + i * 21 + random.randint(0, 5))
                    TourDate.objects.create(
                        tour=tour,
                        start_date=start,
                        end_date=start + timedelta(days=tour.duration_days),
                        available_spots=random.randint(1, min(10, tour.max_people or 10)),
                    )

        self.stdout.write(self.style.SUCCESS("Creating attractions..."))

        attractions_data = [
            ("Озеро Сонг-Кёль", "Song Kol Lake", "Naryn"),
            ("Озеро Кель-Суу", "Kel Suu Lake", "Naryn"),
            ("Караван-сарай Таш-Рабат", "Tash Rabat Caravanserai", "Naryn"),
            ("Озеро Иссык-Куль", "Issyk Kul Lake", "Karakol"),
            ("Каньон Джеты-Огуз", "Jeti Oguz Canyon", "Karakol"),
            ("Долина Алтын-Арашан", "Altyn Arashan Valley", "Karakol"),
            ("Каньон Сказка", "Skazka Canyon", "Karakol"),
            ("Национальный парк Ала-Арча", "Ala Archa National Park", "Bishkek"),
            ("Башня Бурана", "Burana Tower", "Bishkek"),
            ("Гора Сулайман-Тоо", "Sulaiman Too Mountain", "Osh"),
            ("Чарынский каньон", "Charyn Canyon", "Almaty"),
            ("Озёра Кольсай", "Kolsai Lakes", "Almaty"),
            ("Большое Алматинское озеро", "Big Almaty Lake", "Almaty"),
            ("Медеу", "Medeu Mountain Area", "Almaty"),
            ("Парк Панфилова", "Panfilov Park", "Almaty"),
            ("Башня Байтерек", "Bayterek Tower", "Astana"),
            ("Мечеть Хазрет Султан", "Hazrat Sultan Mosque", "Astana"),
            ("Мавзолей Ходжи Ахмеда Ясави", "Khoja Ahmed Yasawi Mausoleum", "Shymkent"),
            ("Площадь Регистан", "Registan Square", "Samarkand"),
            ("Шахи-Зинда", "Shah-i-Zinda Complex", "Samarkand"),
            ("Самаркандский базар", "Samarkand Bazaar", "Samarkand"),
            ("Крепость Арк", "Ark Fortress", "Bukhara"),
            ("Старый город Бухары", "Bukhara Old Town", "Bukhara"),
            ("Пои-Калян", "Poi Kalyan Complex", "Bukhara"),
            ("Ичан-Кала", "Itchan Kala", "Khiva"),
            ("Старый город Хивы", "Khiva Old City", "Khiva"),
            ("Базар Чорсу", "Chorsu Bazaar", "Tashkent"),
            ("Ташкентское метро", "Tashkent Metro", "Tashkent"),
        ]

        attractions = []

        for name_ru, name_en, city_name in attractions_data:
            city = city_map[city_name]
            desc_ru = f"{name_ru} - одна из самых посещаемых достопримечательностей вблизи {city.city_name_ru}."
            desc_en = f"{name_en} is one of the most visited attractions near {city.city_name_en}."

            attraction = Attraction.objects.create(
                city=city,
                name=name_en,
                name_ru=name_ru,
                name_en=name_en,
                description=desc_en,
                description_ru=desc_ru,
                description_en=desc_en,
                is_active=True,
            )
            attractions.append(attraction)

        self.stdout.write(self.style.SUCCESS("Linking attractions to tours by same country..."))

        for tour in tours:
            same_country_attractions = [
                attraction for attraction in attractions
                if attraction.city.country_id == tour.country_id
            ]

            selected_attractions = random.sample(
                same_country_attractions,
                min(len(same_country_attractions), random.randint(3, 5)),
            )

            for attraction in selected_attractions:
                attraction.tours.add(tour)

        self.stdout.write(self.style.SUCCESS("Creating transfer routes..."))

        transfer_routes = [
            ("Бишкек", "Bishkek", "Каракол", "Karakol", 400),
            ("Бишкек", "Bishkek", "Нарын", "Naryn", 315),
            ("Бишкек", "Bishkek", "Ош", "Osh", 610),
            ("Каракол", "Karakol", "Нарын", "Naryn", 420),
            ("Алматы", "Almaty", "Астана", "Astana", 1200),
            ("Алматы", "Almaty", "Шымкент", "Shymkent", 680),
            ("Ташкент", "Tashkent", "Самарканд", "Samarkand", 310),
            ("Самарканд", "Samarkand", "Бухара", "Bukhara", 270),
            ("Бухара", "Bukhara", "Хива", "Khiva", 450),
        ]

        for dep_ru, dep_en, arr_ru, arr_en, distance in transfer_routes:
            route = TransferRoute.objects.create(
                departure_point=dep_en,
                departure_point_ru=dep_ru,
                departure_point_en=dep_en,
                arrival_point=arr_en,
                arrival_point_ru=arr_ru,
                arrival_point_en=arr_en,
                distance_km=distance,
            )

            VehicleType.objects.create(
                route=route,
                category="sedan",
                price=random.randint(50, 130),
                seats=4,
                bags=2,
            )

            VehicleType.objects.create(
                route=route,
                category="minivan",
                price=random.randint(130, 260),
                seats=6,
                bags=5,
            )

            VehicleType.objects.create(
                route=route,
                category="minibus",
                price=random.randint(260, 520),
                seats=12,
                bags=10,
            )

        self.stdout.write(self.style.SUCCESS("Creating team members..."))

        team_data = [
            ("Азамат Токторов", "Azamat Toktorov", "Основатель и гид", "Founder & Guide"),
            ("Аида Садыкова", "Aida Sadykova", "Менеджер туров", "Travel Manager"),
            ("Бекзат Иманкулов", "Bekzat Imankulov", "Горный гид", "Mountain Guide"),
            ("Айнура Асанова", "Ainura Asanova", "Координатор туров", "Tour Coordinator"),
            ("Даниил Ким", "Daniel Kim", "Фотограф", "Photographer"),
            ("Мадина Исаева", "Madina Isaeva", "Эксперт по приключениям", "Adventure Expert"),
            ("Нурсултан Абдыров", "Nursultan Abdyrov", "Гид-водитель", "Driver Guide"),
        ]

        for index, (full_name_ru, full_name_en, position_ru, position_en) in enumerate(team_data):
            description_ru = f"{full_name_ru} имеет многолетний опыт в туризме и организации путешествий по Центральной Азии."
            description_en = f"{full_name_en} has many years of experience in tourism and travel organization across Central Asia."

            TeamMember.objects.create(
                full_name=full_name_en,
                full_name_ru=full_name_ru,
                full_name_en=full_name_en,
                position=position_en,
                position_ru=position_ru,
                position_en=position_en,
                description=description_en,
                description_ru=description_ru,
                description_en=description_en,
                order=index,
                is_active=True,
            )

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Bilingual demo data successfully seeded!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))