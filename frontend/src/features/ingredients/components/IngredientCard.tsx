import { Sparkles } from "lucide-react";
import type { Ingredient } from "../types/ingredient";
interface Props{ingredient:Ingredient;onEdit?:(ingredient:Ingredient)=>void;onDelete?:(ingredient:Ingredient)=>void}
const tones=["peach","blue","lavender","green"];
export default function IngredientCard({ingredient,onEdit,onDelete}:Props){return <article className="ingredient-card"><div className={`ingredient-symbol ${tones[(ingredient.id-1)%tones.length]}`}><Sparkles size={21} fill="currentColor" strokeWidth={1.2}/></div><div className="ingredient-details"><h3>{ingredient.name}</h3><span>{ingredient.caloriesPer100g} ккал / 100 г</span></div><div className="ingredient-nutrient">{ingredient.nutrientLabel}</div>{(onEdit||onDelete)&&<div className="ingredient-actions">{onEdit&&<button type="button" onClick={()=>onEdit(ingredient)} aria-label="Редактировать">✎</button>}{onDelete&&<button type="button" onClick={()=>onDelete(ingredient)} aria-label="Удалить">×</button>}</div>}</article>}
