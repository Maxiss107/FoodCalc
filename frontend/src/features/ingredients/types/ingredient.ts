export type IngredientUnit="g"|"ml"|"pcs";
export interface Ingredient{id:number;name:string;purchasePrice:number;packageWeight:number;currentRemainder:number;unit:IngredientUnit;caloriesPer100g:number;nutrientLabel:string;category:string}
export interface IngredientApiDto{id:number;name:string;purchase_price:number;package_weight:number;current_remainder:number;unit?:IngredientUnit;calories_per_100g?:number;nutrient_label?:string;category?:string}
export function mapIngredientDto(dto:IngredientApiDto):Ingredient{return{id:dto.id,name:dto.name,purchasePrice:dto.purchase_price,packageWeight:dto.package_weight,currentRemainder:dto.current_remainder,unit:dto.unit??"g",caloriesPer100g:dto.calories_per_100g??0,nutrientLabel:dto.nutrient_label??"",category:dto.category??"Другое"}}
