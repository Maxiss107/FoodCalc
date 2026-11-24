from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient

User = get_user_model()

# Базовые ингредиенты для кондитеров и крафтовых пекарей
INITIAL_INGREDIENTS = [
    {
        "name": "Мука пшеничная в/с (Макфа)",
        "purchase_price": Decimal("140.00"),
        "package_weight": Decimal("2000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("342.00"),
        "proteins": Decimal("10.30"),
        "fats": Decimal("1.10"),
        "carbs": Decimal("70.60"),
    },
    {
        "name": "Сахар-песок",
        "purchase_price": Decimal("75.00"),
        "package_weight": Decimal("1000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("398.00"),
        "proteins": Decimal("0.00"),
        "fats": Decimal("0.00"),
        "carbs": Decimal("99.70"),
    },
    {
        "name": "Сливочное масло 82.5% (Экомилк)",
        "purchase_price": Decimal("220.00"),
        "package_weight": Decimal("180.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("748.00"),
        "proteins": Decimal("0.60"),
        "fats": Decimal("82.50"),
        "carbs": Decimal("0.80"),
    },
    {
        "name": "Яйцо куриное С0 (10 шт)",
        "purchase_price": Decimal("130.00"),
        "package_weight": Decimal("600.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("157.00"),
        "proteins": Decimal("12.70"),
        "fats": Decimal("11.50"),
        "carbs": Decimal("0.70"),
    },
    {
        "name": "Молоко цельное 3.2% (Простоквашино)",
        "purchase_price": Decimal("95.00"),
        "package_weight": Decimal("950.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("60.00"),
        "proteins": Decimal("3.00"),
        "fats": Decimal("3.20"),
        "carbs": Decimal("4.70"),
    },
    {
        "name": "Сливки 33% для взбивания (Петмол)",
        "purchase_price": Decimal("340.00"),
        "package_weight": Decimal("500.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("322.00"),
        "proteins": Decimal("2.20"),
        "fats": Decimal("33.00"),
        "carbs": Decimal("4.00"),
    },
    {
        "name": "Творожный сыр Cremette (Hochland)",
        "purchase_price": Decimal("590.00"),
        "package_weight": Decimal("800.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("287.00"),
        "proteins": Decimal("6.00"),
        "fats": Decimal("28.00"),
        "carbs": Decimal("3.00"),
    },
    {
        "name": "Шоколад тёмный 54.5% (Callebaut 811)",
        "purchase_price": Decimal("1650.00"),
        "package_weight": Decimal("1000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("550.00"),
        "proteins": Decimal("5.10"),
        "fats": Decimal("36.60"),
        "carbs": Decimal("46.00"),
    },
    {
        "name": "Шоколад белый 28% (Callebaut W2)",
        "purchase_price": Decimal("1750.00"),
        "package_weight": Decimal("1000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("569.00"),
        "proteins": Decimal("6.00"),
        "fats": Decimal("35.80"),
        "carbs": Decimal("55.40"),
    },
    {
        "name": "Какао-порошок Extra Brute (Cacao Barry)",
        "purchase_price": Decimal("1200.00"),
        "package_weight": Decimal("1000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("384.00"),
        "proteins": Decimal("22.50"),
        "fats": Decimal("21.00"),
        "carbs": Decimal("12.00"),
    },
    {
        "name": "Мёд цветочный натуральный",
        "purchase_price": Decimal("320.00"),
        "package_weight": Decimal("500.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("329.00"),
        "proteins": Decimal("0.80"),
        "fats": Decimal("0.00"),
        "carbs": Decimal("81.50"),
    },
    {
        "name": "Ванильный экстракт натуральный (Бурбон)",
        "purchase_price": Decimal("450.00"),
        "package_weight": Decimal("50.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("288.00"),
        "proteins": Decimal("0.10"),
        "fats": Decimal("0.10"),
        "carbs": Decimal("12.70"),
    },
    {
        "name": "Разрыхлитель теста (Dr. Oetker)",
        "purchase_price": Decimal("25.00"),
        "package_weight": Decimal("10.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("104.00"),
        "proteins": Decimal("0.10"),
        "fats": Decimal("0.10"),
        "carbs": Decimal("25.00"),
    },
    {
        "name": "Желатин листовой (Ewald, 160 bloom)",
        "purchase_price": Decimal("550.00"),
        "package_weight": Decimal("100.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("336.00"),
        "proteins": Decimal("87.20"),
        "fats": Decimal("0.40"),
        "carbs": Decimal("0.70"),
    },
    {
        "name": "Пюре клубничное без сахара (AGROBAR)",
        "purchase_price": Decimal("680.00"),
        "package_weight": Decimal("1000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("41.00"),
        "proteins": Decimal("0.80"),
        "fats": Decimal("0.40"),
        "carbs": Decimal("7.50"),
    },
    {
        "name": "Соль поваренная пищевая мелкая",
        "purchase_price": Decimal("25.00"),
        "package_weight": Decimal("1000.00"),
        "stock_amount": Decimal("0.00"),
        "calories": Decimal("0.00"),
        "proteins": Decimal("0.00"),
        "fats": Decimal("0.00"),
        "carbs": Decimal("0.00"),
    },
]

# Базовые технологические карты и полуфабрикаты
INITIAL_RECIPES = [
    {
        "name": "Бисквит классический ванильный",
        "instructions": (
            "1. Разделить яйца или взбить целыми с сахаром на высокой скорости до пышной светлой пены (8-10 минут).\n"
            "2. Ввести ванильный экстракт.\n"
            "3. Аккуратно лопаткой в три приема вмешать просеянную муку.\n"
            "4. Выпекать при 175°C около 30-35 минут до сухой шпажки.\n"
            "5. Остудить на решетке, завернуть в пленку и убрать в холод на 4-6 часов."
        ),
        "is_semi_finished": True,
        "output_weight": Decimal("500.00"),
        "safety_margin_percent": Decimal("5.00"),
        "items": [
            ("Яйцо куриное С0 (10 шт)", Decimal("240.00")),
            ("Сахар-песок", Decimal("150.00")),
            ("Мука пшеничная в/с (Макфа)", Decimal("150.00")),
            ("Ванильный экстракт натуральный (Бурбон)", Decimal("5.00")),
        ],
    },
    {
        "name": "Крем Чиз на сливках",
        "instructions": (
            "1. Охлажденный творожный сыр, холодные сливки 33% и сахарную пудру соединить в чаше миксера.\n"
            "2. Начать взбивание на низкой скорости до объединения, затем увеличить до средней.\n"
            "3. Взбивать до плотного устойчивого крема (около 2-3 минут). Не перевзбить!"
        ),
        "is_semi_finished": True,
        "output_weight": Decimal("650.00"),
        "safety_margin_percent": Decimal("5.00"),
        "items": [
            ("Творожный сыр Cremette (Hochland)", Decimal("400.00")),
            ("Сливки 33% для взбивания (Петмол)", Decimal("150.00")),
            ("Сахар-песок", Decimal("100.00")),
        ],
    },
    {
        "name": "Шоколадный ганаш на тёмном шоколаде",
        "instructions": (
            "1. Сливки прогреть до 80°C (до первых пузырьков, не кипятить).\n"
            "2. Вылить горячие сливки на тёмный шоколад, оставить на 1 минуту.\n"
            "3. Пробить блендером до гладкой блестящей эмульсии.\n"
            "4. Остудить до 40°C, ввести сливочное масло, повторно пробить.\n"
            "5. Накрыть пленкой в контакт, стабилизировать в холодильнике."
        ),
        "is_semi_finished": True,
        "output_weight": Decimal("400.00"),
        "safety_margin_percent": Decimal("7.00"),
        "items": [
            ("Шоколад тёмный 54.5% (Callebaut 811)", Decimal("200.00")),
            ("Сливки 33% для взбивания (Петмол)", Decimal("150.00")),
            ("Сливочное масло 82.5% (Экомилк)", Decimal("50.00")),
        ],
    },
    {
        "name": "Торт Медовик домашний",
        "instructions": (
            "1. В сотейнике растопить сливочное масло, сахар и мёд до растворения.\n"
            "2. Ввести яйца при постоянном помешивании, заварить массу.\n"
            "3. Добавить муку, замесить мягкое медовое тесто.\n"
            "4. Раскатать и выпечь 8-10 тонких коржей при 180°C (4-5 мин каждый).\n"
            "5. Прослоить коржи кремом из взбитых сливок и сахара.\n"
            "6. Дать пропитаться в холодильнике 8-12 часов."
        ),
        "is_semi_finished": False,
        "output_weight": Decimal("1500.00"),
        "safety_margin_percent": Decimal("10.00"),
        "items": [
            ("Мука пшеничная в/с (Макфа)", Decimal("400.00")),
            ("Сахар-песок", Decimal("200.00")),
            ("Мёд цветочный натуральный", Decimal("100.00")),
            ("Сливочное масло 82.5% (Экомилк)", Decimal("100.00")),
            ("Яйцо куриное С0 (10 шт)", Decimal("120.00")),
            ("Сливки 33% для взбивания (Петмол)", Decimal("500.00")),
        ],
    },
]


class Command(BaseCommand):
    help = "Загрузка базовых системных шаблонов ингредиентов и технологических карт в FoodCalc"

    def handle(self, *args, **options) -> None:
        self.stdout.write("Инициализация системного пользователя шаблонов...")
        system_user = User.objects.get_system_user()

        with transaction.atomic():
            # 1. Загрузка ингредиентов
            self.stdout.write("Загрузка системных шаблонов ингредиентов...")
            ingredient_map: dict[str, Ingredient] = {}
            created_ing_count = 0

            for ing_data in INITIAL_INGREDIENTS:
                name = ing_data["name"]
                defaults = {
                    "purchase_price": ing_data["purchase_price"],
                    "package_weight": ing_data["package_weight"],
                    "stock_amount": ing_data["stock_amount"],
                    "calories": ing_data["calories"],
                    "proteins": ing_data["proteins"],
                    "fats": ing_data["fats"],
                    "carbs": ing_data["carbs"],
                }
                ingredient, created = Ingredient.objects.update_or_create(
                    owner=system_user,
                    name=name,
                    defaults=defaults,
                )
                ingredient_map[name] = ingredient
                if created:
                    created_ing_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Ингредиенты готовы: {len(ingredient_map)} (новых: {created_ing_count})"
                )
            )

            # 2. Загрузка рецептов и технологических карт
            self.stdout.write("Загрузка системных шаблонов рецептов...")
            created_recipe_count = 0

            for recipe_data in INITIAL_RECIPES:
                name = recipe_data["name"]
                defaults = {
                    "instructions": recipe_data["instructions"],
                    "is_semi_finished": recipe_data["is_semi_finished"],
                    "output_weight": recipe_data["output_weight"],
                    "safety_margin_percent": recipe_data["safety_margin_percent"],
                }
                recipe, created = Recipe.objects.update_or_create(
                    owner=system_user,
                    name=name,
                    defaults=defaults,
                )
                if created:
                    created_recipe_count += 1

                # Обновляем состав ингредиентов
                recipe.recipe_ingredients.all().delete()
                for ing_name, amount in recipe_data["items"]:
                    target_ing = ingredient_map.get(ing_name)
                    if target_ing:
                        RecipeIngredient.objects.create(
                            recipe=recipe,
                            ingredient=target_ing,
                            amount_grams=amount,
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Рецепты готовы: {len(INITIAL_RECIPES)} (новых: {created_recipe_count})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Начальная база FoodCalc успешно загружена! "
                f"Всего: {len(ingredient_map)} ингредиентов, {len(INITIAL_RECIPES)} рецептов."
            )
        )
