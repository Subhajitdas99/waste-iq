export interface DealerInventoryLot {
  id: number;
  material_category_id: number;
  material_category_name: string;
  material_description: string | null;
  weight_kg: number;
  unit_price_per_kg_snapshot: number;
  total_listed_amount: number;
  source_city: string;
  status: string;
  created_at: string;
}

export interface DealerInventoryLotPage {
  items: DealerInventoryLot[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface DealerInventoryQuery {
  page?: number;
  page_size?: number;
  material_category_id?: number;
  city?: string;
}
