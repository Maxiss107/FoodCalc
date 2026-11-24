import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

import CatalogTabs, { type CatalogTab } from "../components/CatalogTabs";
import IngredientList from "../../ingredients/components/IngredientList";
import type { Ingredient } from "../../ingredients/types/ingredient";
import { demoIngredients, demoRecipes } from "../testing/demoData";

import "./catalog.css";

interface CatalogPageProps {
  ingredients?: Ingredient[];
  onAddIngredient?: () => void;
  onEditIngredient?: (item: Ingredient) => void;
  onDeleteIngredient?: (item: Ingredient) => void;
}

const ingredientCategories = [
  "Овощи",
  "Фрукты",
  "Молочные",
  "Мясо и рыба",
  "Крупы",
];

const recipeCategories = [
  "Завтраки",
  "Обеды",
  "Ужины",
  "Десерты",
  "Перекусы",
];

export default function CatalogPage({
  ingredients = demoIngredients,
  onAddIngredient,
  onEditIngredient,
  onDeleteIngredient,
}: CatalogPageProps) {
  const [activeTab, setActiveTab] = useState<CatalogTab>("ingredients");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");

  const normalizedSearch = search.trim().toLocaleLowerCase("ru-RU");

  const filteredIngredients = useMemo(
    () =>
      ingredients.filter((ingredient) => {
        const matchesName = ingredient.name
          .toLocaleLowerCase("ru-RU")
          .includes(normalizedSearch);

        const matchesCategory =
          !category || ingredient.category === category;

        return matchesName && matchesCategory;
      }),
    [ingredients, normalizedSearch, category],
  );

  const filteredRecipes = useMemo(
    () =>
      demoRecipes.filter((recipe) =>
        recipe.name
          .toLocaleLowerCase("ru-RU")
          .includes(normalizedSearch),
      ),
    [normalizedSearch],
  );

  const categories =
    activeTab === "ingredients"
      ? ingredientCategories
      : recipeCategories;

  const handleTabChange = (tab: CatalogTab) => {
    setActiveTab(tab);
    setSearch("");
    setCategory("");
  };

  const handleAddIngredient = () => {
    if (onAddIngredient) {
      onAddIngredient();
      return;
    }

    window.alert("Подключите модальное окно из задачи Глеба.");
  };

  return (
    <main className="catalog-page">
      <div className="catalog-heading">
        <h1>
          {activeTab === "ingredients"
            ? "Каталог ингредиентов"
            : "Каталог рецептов"}
        </h1>

        <p>
          {activeTab === "ingredients"
            ? "Составляйте рецепты и следите за пищевой ценностью"
            : "Идеи для вкусного и сбалансированного меню"}
        </p>
      </div>

      <div className="catalog-search-row">
        <label className="search-input">
          <Search size={16} />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={
              activeTab === "ingredients"
                ? "Найти ингредиент..."
                : "Найти рецепт..."
            }
            aria-label={
              activeTab === "ingredients"
                ? "Поиск ингредиентов"
                : "Поиск рецептов"
            }
          />
        </label>

        {activeTab === "ingredients" ? (
          <button
            className="add-button"
            type="button"
            onClick={handleAddIngredient}
          >
            <Plus size={16} />
            Добавить ингредиент
          </button>
        ) : (
          <button className="add-button" type="button">
            Найти рецепт
          </button>
        )}
      </div>

      <div className="category-chips">
        {categories.map((item, index) => (
          <button
            key={item}
            className={`category-chip chip-${index} ${
              category === item ? "chip-active" : ""
            }`}
            type="button"
            aria-pressed={category === item}
            onClick={() =>
              setCategory((currentCategory) =>
                currentCategory === item ? "" : item,
              )
            }
          >
            {item}
          </button>
        ))}
      </div>

      <CatalogTabs
        activeTab={activeTab}
        onChange={handleTabChange}
      />

      {activeTab === "ingredients" ? (
        <>
          <div className="section-title">
            <h2>Все ингредиенты</h2>
            <span>{filteredIngredients.length} позиций</span>
          </div>

          <IngredientList
            ingredients={filteredIngredients}
            onEdit={onEditIngredient}
            onDelete={onDeleteIngredient}
          />
        </>
      ) : (
        <>
          <div className="section-title">
            <h2>Подборка для вас</h2>
            <span>{filteredRecipes.length} рецептов</span>
          </div>

          <div className="recipe-grid">
            {filteredRecipes.map((recipe) => (
              <article className="recipe-card" key={recipe.id}>
                <div className={`recipe-art ${recipe.tone}`}>
                  <div className="plate">
                    <span />
                    <i />
                    <b />
                  </div>
                </div>

                <div className="recipe-info">
                  <h3>{recipe.name}</h3>

                  <div className="recipe-meta">
                    <span>{recipe.minutes} мин</span>
                    <strong>{recipe.calories} ккал</strong>
                  </div>

                  <button type="button">Открыть рецепт</button>
                </div>
              </article>
            ))}
          </div>

          <p className="recipe-note">
            Иллюстрации блюд — временные векторные заглушки; замените их
            фотографиями в финальном контенте.
          </p>
        </>
      )}
    </main>
  );
}
