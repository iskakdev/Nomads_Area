import base64
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import override

from nomads_area_app.models import (
    Attraction, AttractionImage, City, Country, ExtraService, FAQ,
    ItineraryDay, QuizAnswerOption, QuizQuestion, SiteSettings,
    TeamMember, Tour, TourCategory, TourDate, TourImage, TourPriceTier,
    TourRoutePoint, TransferRoute, VehicleType
)

DEMO_IMAGE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def demo_image(path):
    return ContentFile(base64.b64decode(DEMO_IMAGE_BASE64), name=path)


class Command(BaseCommand):
    help = "Seed realistic bilingual demo data for Nomads Area"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Очистка старых данных..."))

        for model in [AttractionImage, TourRoutePoint, TourImage, ItineraryDay, QuizAnswerOption,
                      QuizQuestion, FAQ, ExtraService, TourDate, TourPriceTier, VehicleType, TransferRoute,
                      Attraction, Tour, TeamMember, TourCategory, City, Country, SiteSettings]:
            model.objects.all().delete()

        today = date.today()

        self.stdout.write("1. Настройки сайта...")

        with override("ru"):
            settings = SiteSettings.objects.create(
                phone="+996 555 778 899", whatsapp="+996 555 778 899", email="hello@nomadsarea.com",
                instagram_url="https://instagram.com/nomads_area", facebook_url="https://facebook.com/nomads_area",
                youtube_url="https://youtube.com/@nomads_area", tiktok_url="https://tiktok.com/@nomads_area",
                tripadvisor_url="https://tripadvisor.com",
                about_text="Мы -- команда профессиональных гидов, организующих аутентичные приключения по Центральной Азии.",
                about_video_url="https://youtube.com/watch?v=example",
                years_experience=6, tourists_count=1850, routes_count=42,
                reviews_enabled=True,
                elfsight_google_reviews_app_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                tripadvisor_widget_code='<div id="TA_cdsscrollingreviewsnarrow123" class="TA_cdsscrollingreviewsnarrow"></div>',
                privacy_policy="Ваши данные используются только для обработки заявок.",
            )
        with override("en"):
            settings.about_text = "We are a team of professional guides organizing authentic adventures across Central Asia."
            settings.privacy_policy = "Your data is used only to process requests."
            settings.save()

        self.stdout.write("2. Страны и города...")

        countries_data = [
            ("Кыргызстан", "Kyrgyzstan",
             "Страна небесных гор, кристальных озёр и первозданной кочевой культуры.",
             "The land of celestial mountains, alpine lakes, and pristine nomadic culture."),
            ("Казахстан", "Kazakhstan",
             "Бескрайние степи, космические каньоны и футуристичные города.",
             "Endless steppes, cosmic canyons, and futuristic cities."),
            ("Узбекистан", "Uzbekistan",
             "Сказочные города Великого Шёлкового пути: мечети, медресе и восточные базары.",
             "Fairy-tale cities of the Great Silk Road: mosques, madrassas, and oriental bazaars."),
        ]

        countries = {}
        for index, (name_ru, name_en, desc_ru, desc_en) in enumerate(countries_data, start=1):
            with override("ru"):
                country = Country.objects.create(
                    country_name=name_ru, hero_description=desc_ru,
                    country_image=demo_image(f"countries/country-{index}.png"),
                    symbol_image=demo_image(f"countries/symbols/country-symbol-{index}.png"),
                )
            with override("en"):
                country.country_name = name_en
                country.hero_description = desc_en
                country.save()
            countries[name_en] = country

        cities_data = [
            ("Kyrgyzstan", "Бишкек", "Bishkek", "Зелёная столица у подножия Киргизского хребта.", "A green capital at the foot of the Kyrgyz Range."),
            ("Kyrgyzstan", "Каракол", "Karakol", "Уютный город на восточном берегу Иссык-Куля.", "A cozy town on the eastern shore of Issyk-Kul."),
            ("Kyrgyzstan", "Ош", "Osh", "Южная столица с базаром и горой Сулейман-Тоо.", "The southern capital with its ancient bazaar and Suleiman-Too mountain."),
            ("Kyrgyzstan", "Нарын", "Naryn", "Горный город у ворот в Центральный Тянь-Шань.", "A highland town at the gateway to the Central Tien Shan."),
            ("Kyrgyzstan", "Чолпон-Ата", "Cholpon-Ata", "Курортный город на северном берегу Иссык-Куля.", "A resort town on the northern shore of Issyk-Kul."),
            ("Kazakhstan", "Алматы", "Almaty", "Бывшая столица в предгорьях Заилийского Алатау.", "Former capital at the foot of the Trans-Ili Alatau."),
            ("Kazakhstan", "Астана", "Astana", "Футуристичная столица в центре степей.", "Futuristic capital in the heart of the steppe."),
            ("Kazakhstan", "Шымкент", "Shymkent", "Третий по величине город на юге Казахстана.", "The third-largest city in southern Kazakhstan."),
            ("Uzbekistan", "Самарканд", "Samarkand", "Жемчужина Шёлкового пути с ансамблем Регистан.", "Pearl of the Silk Road with the Registan ensemble."),
            ("Uzbekistan", "Бухара", "Bukhara", "Средневековый город-музей с тысячелетней историей.", "A medieval open-air museum with a thousand-year history."),
        ]

        cities = {}
        for index, (country_key, name_ru, name_en, desc_ru, desc_en) in enumerate(cities_data, start=1):
            with override("ru"):
                city = City.objects.create(
                    country=countries[country_key], city_name=name_ru, description=desc_ru,
                    city_image=demo_image(f"cities/city-{index}.png"),
                )
            with override("en"):
                city.city_name = name_en
                city.description = desc_en
                city.save()
            cities[name_en] = city

        self.stdout.write("3. Категории...")

        categories_data = [
            ("Джип-туры", "Jeep Tours", "Маршруты на внедорожниках по высокогорью.", "Off-road routes through high-altitude terrain."),
            ("Треккинг", "Trekking", "Пешие походы к озёрам и перевалам.", "Hiking routes to lakes and mountain passes."),
            ("Конные туры", "Horseback Tours", "Путешествия верхом по кочевым угодьям.", "Journeys on horseback through nomadic lands."),
            ("Культурные туры", "Cultural Tours", "Знакомство с историей и традициями региона.", "Immersion in the history and traditions of the region."),
            ("Велотуры", "Cycling Tours", "Маршруты на велосипеде по живописным дорогам.", "Cycling routes along scenic roads."),
            ("Зимние туры", "Winter Tours", "Лыжи, снегоходы и зимние пейзажи.", "Skiing, snowmobiles, and winter landscapes."),
            ("Экотуризм", "Ecotourism", "Туры с минимальным воздействием на природу.", "Low-impact tours connecting you with nature."),
            ("Шёлковый путь", "Silk Road", "Маршруты по древним городам торговых путей.", "Routes through ancient Silk Road trading cities."),
            ("Фотографические туры", "Photography Tours", "Туры для тех, кто хочет поймать лучший кадр.", "Tours designed for those seeking the perfect shot."),
            ("Кулинарные туры", "Culinary Tours", "Погружение в гастрономию Центральной Азии.", "Deep dive into Central Asian gastronomy."),
        ]

        categories = []
        for index, (name_ru, name_en, desc_ru, desc_en) in enumerate(categories_data, start=1):
            with override("ru"):
                category = TourCategory.objects.create(
                    name=name_ru, description=desc_ru,
                    image=demo_image(f"categories/category-{index}.png"),
                    is_active=True, order=index,
                )
            with override("en"):
                category.name = name_en
                category.description = desc_en
                category.save()
            categories.append(category)

        cat_jeep, cat_trek, cat_horse, cat_cult, cat_bike, cat_winter, cat_eco, cat_silk, cat_photo, cat_food = categories

        self.stdout.write("4. Туры...")

        tours_data = [
            (countries["Kyrgyzstan"], cities["Bishkek"], "group", "warm", 2, 7, 950, 12,
             "Сокровища Тянь-Шаня: Сон-Куль и каньоны", "Treasures of Tien Shan: Son-Kul & Canyons",
             "Путешествие на внедорожниках к озеру Сон-Куль с ночёвкой в юртах.",
             "An off-road journey to Son-Kul lake with overnight stays in yurts.",
             "Джипы 4x4, юрты и отели, питание, гид.", "4x4 SUVs, yurts and hotels, meals, guide.",
             "Авиабилеты, страховка, личные расходы.", "Flights, insurance, personal expenses.",
             [cat_jeep, cat_photo]),
            (countries["Kyrgyzstan"], cities["Karakol"], "private", "warm", 3, 5, 850, 10,
             "Экспедиция к озеру Ала-Куль", "Expedition to Ala-Kul Lake",
             "Индивидуальный треккинг к бирюзовому Ала-Кулю.",
             "Private trekking to turquoise Ala-Kul lake.",
             "Гид, палатки, питание, трансфер.", "Guide, tents, meals, transfer.",
             "Портеры, аренда спальников.", "Porters, sleeping bag rental.",
             [cat_trek, cat_eco]),
            (countries["Kyrgyzstan"], cities["Bishkek"], "group", "warm", 1, 3, 320, 8,
             "Конный тур в долину Кегеты", "Horseback Tour in Keget Valley",
             "Конный маршрут по живописной долине Кегеты.",
             "Horse ride through scenic Keget valley.",
             "Лошади, инструктор, юрта, питание.", "Horses, instructor, yurt, meals.",
             "Страховка и личные расходы.", "Insurance and personal expenses.",
             [cat_horse]),
            (countries["Uzbekistan"], cities["Samarkand"], "group", "all_year", 1, 5, 680, 15,
             "Жемчужины Шёлкового пути", "Silk Road Gems",
             "Самарканд, Бухара, Регистан и древние базары.",
             "Samarkand, Bukhara, Registan and ancient bazaars.",
             "Транспорт, отели, завтраки, гид.", "Transport, hotels, breakfasts, guide.",
             "Авиабилеты и ужины.", "Flights and dinners.",
             [cat_silk, cat_cult]),
            (countries["Kazakhstan"], cities["Almaty"], "private", "warm", 2, 4, 720, 10,
             "Горное кольцо Алматы", "Almaty Mountain Ring",
             "Приватный джип-тур к Чарыну и Кольсаю.",
             "Private jeep tour to Charyn and Kolsay.",
             "Внедорожник, гид, питание, проживание.", "SUV, guide, meals, accommodation.",
             "Авиабилеты и личные расходы.", "Flights and personal expenses.",
             [cat_jeep, cat_photo]),
            (countries["Kyrgyzstan"], cities["Naryn"], "group", "warm", 2, 6, 780, 10,
             "Сердце Кыргызстана: Нарын и Ташрабат", "Heart of Kyrgyzstan: Naryn & Tash-Rabat",
             "Маршрут к каравансараю Ташрабат.",
             "Route to the Tash-Rabat caravanserai.",
             "Транспорт, юрты, питание, гид.", "Transport, yurts, meals, guide.",
             "Авиабилеты и страховка.", "Flights and insurance.",
             [cat_jeep, cat_cult]),
            (countries["Kyrgyzstan"], cities["Cholpon-Ata"], "group", "warm", 1, 8, 1100, 12,
             "Большое кольцо Иссык-Куля", "Grand Issyk-Kul Circuit",
             "Объезд озера Иссык-Куль с каньонами и ущельями.",
             "Full circuit of Issyk-Kul lake with canyons and gorges.",
             "Автобус, отели, завтраки, гид.", "Bus, hotels, breakfasts, guide.",
             "Обеды, ужины, личные расходы.", "Lunches, dinners, personal expenses.",
             [cat_jeep, cat_eco]),
            (countries["Kyrgyzstan"], cities["Osh"], "private", "all_year", 1, 3, 420, 10,
             "Южный Кыргызстан: Ош и Фергана", "Southern Kyrgyzstan: Osh & Fergana",
             "Приватная экскурсия по Ошу и Ферганской долине.",
             "Private tour of Osh and Fergana Valley.",
             "Транспорт, гид, входные билеты.", "Transport, guide, entrance fees.",
             "Питание и отель.", "Meals and hotel.",
             [cat_cult, cat_food]),
            (countries["Kazakhstan"], cities["Astana"], "group", "winter", 1, 5, 890, 14,
             "Зимний Казахстан", "Winter Kazakhstan",
             "Астана и горнолыжные склоны.",
             "Astana and ski slopes.",
             "Отели, завтраки, ски-пасс, гид.", "Hotels, breakfasts, ski pass, guide.",
             "Аренда снаряжения.", "Equipment rental.",
             [cat_winter]),
            (countries["Uzbekistan"], cities["Bukhara"], "group", "all_year", 1, 4, 590, 15,
             "Бухара: Город вне времени", "Bukhara: City Out of Time",
             "Средневековая Бухара, крепость Арк и старый город.",
             "Medieval Bukhara, Ark Citadel and old town.",
             "Отели, завтраки, гид, билеты.", "Hotels, breakfasts, guide, tickets.",
             "Авиабилеты и ужины.", "Flights and dinners.",
             [cat_silk, cat_food]),
        ]

        tours = []
        for index, data in enumerate(tours_data, start=1):
            (country, city, tour_type, season, difficulty, days, price, max_group_size,
             title_ru, title_en, desc_ru, desc_en, inc_ru, inc_en, exc_ru, exc_en, tour_categories) = data

            with override("ru"):
                tour = Tour.objects.create(
                    country=country, city=city, tour_type=tour_type, season=season,
                    difficulty=difficulty, duration_days=days, price=price, currency="USD",
                    max_group_size=max_group_size, title=title_ru, description=desc_ru,
                    included=inc_ru, not_included=exc_ru, is_active=True,
                )
            with override("en"):
                tour.title = title_en
                tour.description = desc_en
                tour.included = inc_en
                tour.not_included = exc_en
                tour.save()

            tour.categories.set(tour_categories)

            for image_index in range(1, 4):
                TourImage.objects.create(
                    tour=tour,
                    image=demo_image(f"tours/tour-{index}-{image_index}.png"),
                    alt_text=f"{tour.title} image {image_index}",
                    order=image_index,
                )

            for day in range(1, days + 1):
                with override("ru"):
                    itinerary = ItineraryDay.objects.create(
                        tour=tour, day_number=day,
                        title=f"День {day}",
                        description=f"Описание маршрута дня {day}.",
                        image=demo_image(f"itinerary/tour-{index}-day-{day}.png"),
                        altitude="1500-3000 м",
                        walking_distance="3-8 км",
                        driving_distance="40-180 км",
                        accommodation="Отель / юрта",
                    )
                with override("en"):
                    itinerary.title = f"Day {day}"
                    itinerary.description = f"Route description for day {day}."
                    itinerary.altitude = "1500-3000 m"
                    itinerary.walking_distance = "3-8 km"
                    itinerary.driving_distance = "40-180 km"
                    itinerary.accommodation = "Hotel / yurt"
                    itinerary.save()

            for point_index in range(1, 4):
                TourRoutePoint.objects.create(
                    tour=tour,
                    title=f"Point {point_index}",
                    latitude=42.870000 + point_index,
                    longitude=74.590000 + point_index,
                    order=point_index,
                )

            if tour_type == "group":
                for shift in [10, 35, 65]:
                    TourDate.objects.create(
                        tour=tour,
                        start_date=today + timedelta(days=shift),
                        end_date=today + timedelta(days=shift + days),
                        available_spots=max_group_size,
                    )

            if tour_type == "private":
                TourPriceTier.objects.create(tour=tour, min_people=1, max_people=2, price_per_person=price)
                TourPriceTier.objects.create(tour=tour, min_people=3, max_people=5, price_per_person=int(price * 0.8))
                TourPriceTier.objects.create(tour=tour, min_people=6, max_people=None, price_per_person=int(price * 0.65))

            tours.append(tour)

        self.stdout.write("5. FAQ и дополнительные услуги...")

        for index, tour in enumerate(tours, start=1):
            with override("ru"):
                faq = FAQ.objects.create(
                    tour=tour, question="Что входит в стоимость?",
                    answer="В стоимость входят услуги, указанные в программе.",
                    order=1, is_active=True,
                )
                extra = ExtraService.objects.create(
                    tour=tour, title="Индивидуальная фотосессия",
                    description="Профессиональная фотосессия во время тура.",
                    features=["20 фото", "обработка", "онлайн-галерея"],
                    price=80, currency="USD", price_label="за сессию",
                    is_active=True, image=demo_image(f"services/service-{index}.png"),
                )
            with override("en"):
                faq.question = "What is included in the price?"
                faq.answer = "The price includes the services listed in the itinerary."
                faq.save()
                extra.title = "Private photo session"
                extra.description = "Professional photo session during the tour."
                extra.price_label = "per session"
                extra.save()

        self.stdout.write("6. Достопримечательности...")

        attractions_data = [
            (cities["Bishkek"], "Башня Бурана", "Burana Tower", "Минарет XI века в Чуйской долине.", "11th-century minaret in the Chuy Valley."),
            (cities["Karakol"], "Каньон Сказка", "Skazka Canyon", "Красные скалы причудливых форм.", "Red rock formations in fairy-tale shapes."),
            (cities["Karakol"], "Джеты-Огуз", "Jeti-Oguz", "Красные скалы и альпийское ущелье.", "Red cliffs and alpine gorge."),
            (cities["Naryn"], "Ташрабат", "Tash-Rabat", "Средневековый каменный каравансарай.", "Medieval stone caravanserai."),
            (cities["Cholpon-Ata"], "Петроглифы Чолпон-Аты", "Cholpon-Ata Petroglyphs", "Скальные рисунки эпохи бронзы.", "Bronze-age rock carvings."),
            (cities["Osh"], "Сулейман-Тоо", "Suleiman-Too", "Священная гора в центре Оша.", "Sacred mountain in the heart of Osh."),
            (cities["Samarkand"], "Регистан", "Registan", "Главная площадь Самарканда.", "Main square of Samarkand."),
            (cities["Bukhara"], "Крепость Арк", "Ark Citadel", "Древняя цитадель Бухары.", "Ancient citadel of Bukhara."),
            (cities["Almaty"], "Каньон Чарын", "Charyn Canyon", "Грандиозный каньон Казахстана.", "Grand canyon of Kazakhstan."),
            (cities["Almaty"], "Шымбулак", "Shymbulak", "Горнолыжный курорт над Алматы.", "Ski resort above Almaty."),
        ]

        for index, (city, name_ru, name_en, desc_ru, desc_en) in enumerate(attractions_data, start=1):
            with override("ru"):
                attraction = Attraction.objects.create(
                    city=city, name=name_ru, description=desc_ru,
                    image=demo_image(f"attractions/attraction-{index}.png"),
                    is_active=True,
                )
            with override("en"):
                attraction.name = name_en
                attraction.description = desc_en
                attraction.save()

            attraction.tours.set(tours[:3])

            for image_index in range(1, 3):
                AttractionImage.objects.create(
                    attraction=attraction,
                    image=demo_image(f"attractions/gallery/attraction-{index}-{image_index}.png"),
                    alt_text=f"{attraction.name} image {image_index}",
                    order=image_index,
                )

        self.stdout.write("7. Трансферы...")

        routes_data = [
            ("Аэропорт Манас", "Manas Airport", "Бишкек центр", "Bishkek city center"),
            ("Бишкек", "Bishkek", "Каракол", "Karakol"),
            ("Бишкек", "Bishkek", "Чолпон-Ата", "Cholpon-Ata"),
            ("Бишкек", "Bishkek", "Ош", "Osh"),
            ("Каракол", "Karakol", "Аэропорт Тамчы", "Tamchy Airport"),
            ("Аэропорт Алматы", "Almaty Airport", "Алматы центр", "Almaty city center"),
            ("Алматы", "Almaty", "Каньон Чарын", "Charyn Canyon"),
            ("Алматы", "Almaty", "Озёра Кольсай", "Kolsay Lakes"),
            ("Аэропорт Ташкента", "Tashkent Airport", "Самарканд", "Samarkand"),
            ("Самарканд", "Samarkand", "Бухара", "Bukhara"),
        ]

        for index, (dep_ru, dep_en, arr_ru, arr_en) in enumerate(routes_data, start=1):
            with override("ru"):
                route = TransferRoute.objects.create(departure_point=dep_ru, arrival_point=arr_ru)
            with override("en"):
                route.departure_point = dep_en
                route.arrival_point = arr_en
                route.save()

            VehicleType.objects.create(route=route, category="sedan", price=20 + index * 5, seats=3, bags=2)
            VehicleType.objects.create(route=route, category="minivan", price=35 + index * 8, seats=6, bags=4)
            VehicleType.objects.create(route=route, category="minibus", price=60 + index * 12, seats=15, bags=12)

        self.stdout.write("8. Команда...")

        team_data = [
            ("Бекзат Иманкулов", "Bekzat Imankulov", "Старший горный гид", "Senior Mountain Guide"),
            ("Айнура Асанова", "Ainura Asanova", "Координатор туров", "Tour Coordinator"),
            ("Даниил Ким", "Daniel Kim", "Фотограф", "Photographer"),
            ("Нурлан Сейткали", "Nurlan Seitkali", "Водитель-механик", "Driver & Mechanic"),
            ("Гульмира Токтосун", "Gulmira Toktosun", "Кулинарный гид", "Culinary Guide"),
            ("Алексей Воронов", "Alexei Voronov", "Гид по Шёлковому пути", "Silk Road Guide"),
            ("Диана Сагынбек", "Diana Sagynbek", "Гид по экотуризму", "Ecotourism Guide"),
            ("Марат Омуркул", "Marat Omurkul", "Инструктор по верховой езде", "Horseback Riding Instructor"),
            ("Зарина Хасанова", "Zarina Khasanova", "Гид по Казахстану", "Kazakhstan Guide"),
            ("Тимур Алибеков", "Timur Alibekov", "Координатор трансферов", "Transfer Coordinator"),
        ]

        for index, (name_ru, name_en, position_ru, position_en) in enumerate(team_data, start=1):
            with override("ru"):
                member = TeamMember.objects.create(
                    full_name=name_ru, position=position_ru,
                    description="Опытный член команды Nomads Area.",
                    photo=demo_image(f"team/member-{index}.png"),
                    order=index, is_active=True,
                )
            with override("en"):
                member.full_name = name_en
                member.position = position_en
                member.description = "Experienced member of the Nomads Area team."
                member.save()

        self.stdout.write("9. Квиз...")

        questions_data = [
            ("single", "Какой тип отдыха вам ближе?", "What type of holiday suits you best?",
             [("Джип-тур", "Jeep tour"), ("Треккинг", "Trekking"), ("Конный тур", "Horseback riding")]),
            ("single", "Когда планируете поездку?", "When are you planning your trip?",
             [("Скоро", "Soon"), ("Летом", "In summer"), ("Осенью", "In autumn")]),
            ("single", "Сколько человек в группе?", "How many people are in your group?",
             [("1-2", "1-2"), ("3-5", "3-5"), ("6+", "6+")]),
            ("single", "Какой бюджет на человека?", "What is your budget per person?",
             [("До 500 USD", "Up to USD 500"), ("500-1000 USD", "USD 500-1000"), ("1000+ USD", "USD 1000+")]),
            ("single", "Уровень подготовки?", "Fitness level?",
             [("Лёгкий", "Easy"), ("Средний", "Moderate"), ("Высокий", "High")]),
            ("multiple", "Что важно в туре?", "What is important in a tour?",
             [("Комфорт", "Comfort"), ("Фото", "Photos"), ("Гид", "Guide")]),
            ("single", "Какую страну хотите?", "Which country?",
             [("Кыргызстан", "Kyrgyzstan"), ("Казахстан", "Kazakhstan"), ("Узбекистан", "Uzbekistan")]),
            ("single", "Тип проживания?", "Accommodation type?",
             [("Юрта", "Yurt"), ("Отель", "Hotel"), ("Глэмпинг", "Glamping")]),
            ("single", "Есть опыт походов?", "Do you have hiking experience?",
             [("Нет", "No"), ("Немного", "A little"), ("Да", "Yes")]),
            ("text", "Особые пожелания?", "Special requests?", []),
        ]

        previous_question = None
        for order, (question_type, text_ru, text_en, options) in enumerate(questions_data, start=1):
            with override("ru"):
                question = QuizQuestion.objects.create(
                    question_text=text_ru, question_type=question_type,
                    order=order, is_active=True,
                )
            with override("en"):
                question.question_text = text_en
                question.save()

            if previous_question:
                previous_question.options.update(next_question=question)

            for option_ru, option_en in options:
                with override("ru"):
                    option = QuizAnswerOption.objects.create(question=question, option_text=option_ru)
                with override("en"):
                    option.option_text = option_en
                    option.save()

            previous_question = question

        self.stdout.write(self.style.SUCCESS("Демо-данные успешно загружены."))
