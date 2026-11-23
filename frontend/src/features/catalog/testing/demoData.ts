import type { Ingredient } from "../../ingredients/types/ingredient";
export const demoIngredients:Ingredient[]=[
{id:1,name:"Куриная грудка",purchasePrice:360,packageWeight:1000,currentRemainder:800,unit:"g",caloriesPer100g:165,nutrientLabel:"Белки 31 г",category:"Мясо и рыба"},
{id:2,name:"Помидор",purchasePrice:180,packageWeight:1000,currentRemainder:500,unit:"g",caloriesPer100g:18,nutrientLabel:"Клетчатка 1.2 г",category:"Овощи"},
{id:3,name:"Рис белый",purchasePrice:110,packageWeight:1000,currentRemainder:900,unit:"g",caloriesPer100g:130,nutrientLabel:"Углеводы 28 г",category:"Крупы"},
{id:4,name:"Яблоко",purchasePrice:160,packageWeight:1000,currentRemainder:650,unit:"g",caloriesPer100g:52,nutrientLabel:"Клетчатка 2.4 г",category:"Фрукты"},
{id:5,name:"Творог 5%",purchasePrice:145,packageWeight:500,currentRemainder:350,unit:"g",caloriesPer100g:121,nutrientLabel:"Белки 17 г",category:"Молочные"},
{id:6,name:"Брокколи",purchasePrice:210,packageWeight:500,currentRemainder:250,unit:"g",caloriesPer100g:34,nutrientLabel:"Клетчатка 2.6 г",category:"Овощи"},
{id:7,name:"Лосось",purchasePrice:650,packageWeight:500,currentRemainder:300,unit:"g",caloriesPer100g:208,nutrientLabel:"Жиры 13 г",category:"Мясо и рыба"},
{id:8,name:"Овсяные хлопья",purchasePrice:120,packageWeight:500,currentRemainder:400,unit:"g",caloriesPer100g:366,nutrientLabel:"Углеводы 62 г",category:"Крупы"}];
export const demoRecipes=[{id:1,name:"Паста с курицей",minutes:25,calories:420,tone:"peach"},{id:2,name:"Овсяная каша",minutes:10,calories:280,tone:"blue"},{id:3,name:"Томатный суп",minutes:30,calories:190,tone:"peach"},{id:4,name:"Рис с овощами",minutes:20,calories:310,tone:"green"},{id:5,name:"Сырники",minutes:25,calories:360,tone:"lavender"},{id:6,name:"Запечённая рыба",minutes:35,calories:390,tone:"peach"}];
