export interface MarketplaceInventoryLot {
  id: number;
  lot_number: string;
  material_category_id: number;
  material_category_name: string;
  material_description: string | null;
  weight_kg: number;
  unit_price_per_kg_snapshot: number;
  total_listed_amount: number;
  currency_code: string | null;
  source_city: string;
  quality_grade: string | null;
  status: "available" | "reserved" | "sold";
  seller_name: string | null;
  reserved_at: string | null;
  reservation_expires_at: string | null;
  is_reserved_by_me: boolean;
  created_at: string;
}

export interface MarketplaceInventoryPage {
  items: MarketplaceInventoryLot[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface MarketplaceInventoryQuery {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  material_category_id?: number;
  city?: string;
  search?: string;
}

export interface MarketplaceOrder {
  id: number;
  order_number: string;
  inventory_lot_id: number;
  lot_number: string;
  material_category_id: number;
  material_category_name: string;
  material_description: string | null;
  dealer_id: number;
  dealer_name: string | null;
  quantity_kg: number;
  unit_price_per_kg_snapshot: number;
  total_amount: number;
  currency_code: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface MarketplaceOrderDetail extends MarketplaceOrder {
  transactions: MarketplaceTransaction[];
}

export interface MarketplaceOrderPage {
  items: MarketplaceOrder[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export type MarketplaceTransactionType =
  | "reservation"
  | "cancellation"
  | "purchase"
  | "reservation_expired";

export interface MarketplaceTransaction {
  id: number;
  order_id: number | null;
  inventory_lot_id: number;
  lot_number: string;
  material_category_name: string;
  dealer_id: number;
  dealer_name: string | null;
  transaction_type: MarketplaceTransactionType;
  status: string;
  quantity_kg: number;
  unit_price_per_kg_snapshot: number;
  total_amount: number;
  currency_code: string;
  created_at: string;
}

export interface MarketplaceTransactionPage {
  items: MarketplaceTransaction[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}
