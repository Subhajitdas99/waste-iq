export type DealerInventoryStatus = 'available' | 'reserved' | 'sold';

export interface DealerInventoryBase {
  pickup_request_id: number;
  material_type: string;
  category: string;
  quantity_kg: number;
  price_per_kg: number;
  quality_grade?: string;
}

export interface DealerInventory extends DealerInventoryBase {
  id: number;
  dealer_id: number;
  total_value: number;
  status: DealerInventoryStatus;
  created_at: string;
  updated_at: string;
}

export interface DealerInventoryPage {
  items: DealerInventory[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface DealerInventoryUpdate {
  material_type?: string;
  category?: string;
  quantity_kg?: number;
  price_per_kg?: number;
  quality_grade?: string;
}
