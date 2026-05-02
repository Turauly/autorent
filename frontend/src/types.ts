export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: number;
  full_name?: string | null;
  phone?: string | null;
  email: string;
  role: "user" | "admin";
  is_verified?: boolean;
  is_blacklisted?: boolean;
  loyalty_points?: number;
  created_at: string;
};

export type Car = {
  id: number;
  brand: string;
  model: string;
  category: "econom" | "budget" | "comfort" | "lux";
  year: number;
  transmission: string;
  fuel_type: string;
  seats: number;
  has_ac: boolean;
  has_gps: boolean;
  has_bluetooth: boolean;
  price_per_day: number;
  status: string;
  main_image_url: string | null;
  next_service_date: string | null;
  service_note: string | null;
  photos: Array<{ id: number; url: string }>;
};

export type CarListResponse = {
  items: Car[];
  total: number;
  page: number;
  limit: number;
};

export type UserDocument = {
  id: number;
  user_id: number;
  document_type: string;
  document_number: string;
  file_url: string | null;
  uploaded_at: string;
};

export type AuditLog = {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  ip_address: string | null;
  user_agent: string | null;
  details: string | null;
  created_at: string;
};

export type AuditLogListResponse = {
  items: AuditLog[];
  total: number;
  page: number;
  limit: number;
};

export type AdminOverview = {
  total_users: number;
  total_cars: number;
  active_rentals: number;
  completed_rentals: number;
  monthly_revenue: number;
  monthly_expenses: number;
  monthly_profit: number;
  avg_check: number;
};

export type RentalTimelineItem = {
  rental_id: number;
  start_date: string;
  end_date: string;
  total_price: number;
  status: string;
  user_id: number;
  user_email: string;
  user_full_name: string | null;
  car_id: number;
  car_brand: string;
  car_model: string;
  car_category: string;
};

export type RentalTimelineResponse = {
  items: RentalTimelineItem[];
  total: number;
  page: number;
  limit: number;
};

export type Expense = {
  id: number;
  title: string;
  amount: number;
  category: string;
  expense_date: string;
  note: string | null;
};

export type ExpenseListResponse = {
  items: Expense[];
  total: number;
  page: number;
  limit: number;
};

export type ClientRequest = {
  id: number;
  user_id: number;
  user_email: string | null;
  user_full_name: string | null;
  subject: string;
  message: string;
  status: "open" | "in_progress" | "resolved" | "rejected";
  admin_comment: string | null;
  created_at: string;
  updated_at: string | null;
};

export type ClientRequestListResponse = {
  items: ClientRequest[];
  total: number;
  page: number;
  limit: number;
};

export type Rental = {
  id: number;
  user_id: number;
  car_id: number;
  start_date: string;
  end_date: string;
  total_price: number;
  status: "active" | "completed" | "canceled";
  price_variant?: "A" | "B";
};

export type RentalListResponse = {
  items: Rental[];
  total: number;
  page: number;
  limit: number;
};

export type WaitlistEntry = {
  id: number;
  user_id: number;
  car_id: number;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
};

export type ChatMessage = {
  id: number;
  user_id: number;
  sender_role: "user" | "admin";
  message: string;
  created_at: string;
};

export type TourRequest = {
  id: string;
  packageId: string;
  packageTitle: string;
  route: string;
  days: number;
  price: number;
  userId: number;
  userEmail: string;
  userFullName?: string | null;
  userPhone?: string | null;
  source: string;
  status: string;
  createdAt: string | null;
};
