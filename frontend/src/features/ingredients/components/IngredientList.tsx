import { PackageOpen } from "lucide-react";
import IngredientCard from "./IngredientCard";
import type { Ingredient } from "../types/ingredient";
interface Props{ingredients:Ingredient[];onEdit?:(item:Ingredient)=>void;onDelete?:(item:Ingredient)=>void}
export default function IngredientList({ingredients,onEdit,onDelete}:Props){if(!ingredients.length)return <div className="empty-state"><PackageOpen size={26}/><strong>Ингредиенты не найдены</strong><span>Попробуйте изменить поиск или категорию.</span></div>;return <div className="ingredient-grid">{ingredients.map(item=><IngredientCard key={item.id} ingredient={item} onEdit={onEdit} onDelete={onDelete}/>)}</div>}
