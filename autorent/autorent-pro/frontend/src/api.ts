import axios from "axios";
import type {
  AdminOverview,
  AuditLogListResponse,
  CarListResponse,
  Car,
  ChatMessage,
  ChargingAnalytics,
  ChargingBooking,
  ChargingBookingListResponse,
  ChargingNotification,
  ChargingNotificationListResponse,
  ChargingReview,
  ChargingReviewListResponse,
  ChargingSession,
  ChargingSessionListResponse,
  ChargingStation,
  ChargingStationListResponse,
  ClientRequest,
  ClientRequestListResponse,
  Expense,
  ExpenseListResponse,
  Rental,
  RentalListResponse,
  RentalTimelineResponse,
  TokenResponse,
  User,
  UserDocument,
  WaitlistEntry
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: BASE_URL
});

export async function login(email: string, password: string): Promise<TokenResponse> {
  const data = new URLSearchParams();
  data.append("username", email);
  data.append("password", password);
  const response = await api.post<TokenResponse>("/auth/login", data, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" }
  });
  return response.data;
}

export async function requestRegisterCode(email: string) {
  await api.post("/auth/register/request-code", { email });
}

export async function confirmRegister(payload: {
  email: string;
  password: string;
  code: string;
  full_name?: string;
  phone?: string;
}) {
  await api.post("/auth/register/confirm", payload);
}

export async function getCars(params: {
  q?: string;
  status?: string;
  category?: "econom" | "budget" | "comfort" | "lux";
  is_electric?: boolean;
  min_price?: number;
  max_price?: number;
  page?: number;
  limit?: number;
  sort_by?: "price_per_day" | "year" | "brand";
  sort_order?: "asc" | "desc";
}) {
  const response = await api.get<CarListResponse>("/cars/", { params });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}

export async function getAdminUsers(): Promise<User[]> {
  const response = await api.get<User[]>("/admin/users");
  return response.data;
}

export async function transferAdminRole(userId: number): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>(`/admin/transfer/${userId}`);
  return response.data;
}

export async function updateUserBlacklist(
  userId: number,
  payload: { is_blacklisted: boolean; reason?: string }
): Promise<User> {
  const response = await api.patch<User>(`/admin/users/${userId}/blacklist`, payload);
  return response.data;
}

export async function updateCarService(
  carId: number,
  payload: { next_service_date?: string | null; service_note?: string | null }
): Promise<Car> {
  const response = await api.patch<Car>(`/admin/cars/${carId}/service`, payload);
  return response.data;
}

export async function createCar(payload: {
  brand: string;
  model: string;
  year: number;
  price_per_day: number;
  status: "available" | "rented" | "service";
  main_image_url?: string;
  category?: "econom" | "budget" | "comfort" | "lux";
  is_electric?: boolean;
  battery_capacity_kwh?: number | null;
  range_km?: number | null;
  charge_port?: string | null;
  next_service_date?: string | null;
  service_note?: string | null;
  image_urls?: string[];
}): Promise<Car> {
  const response = await api.post<Car>("/cars/", payload);
  return response.data;
}

export async function deleteCar(carId: number): Promise<void> {
  await api.delete(`/cars/${carId}`);
}

export async function getMyDocuments(): Promise<UserDocument[]> {
  const response = await api.get<UserDocument[]>("/profile/documents");
  return response.data;
}

export async function uploadMyDocument(payload: {
  document_type: string;
  document_number: string;
  file: File;
}): Promise<UserDocument> {
  const form = new FormData();
  form.append("document_type", payload.document_type);
  form.append("document_number", payload.document_number);
  form.append("file", payload.file);
  const response = await api.post<UserDocument>("/profile/documents/upload", form);
  return response.data;
}

export async function getAuditLogs(params: {
  user_id?: number;
  action?: string;
  page?: number;
  limit?: number;
}): Promise<AuditLogListResponse> {
  const response = await api.get<AuditLogListResponse>("/admin/audit-logs", { params });
  return response.data;
}

export async function getAdminOverview(): Promise<AdminOverview> {
  const response = await api.get<AdminOverview>("/admin/overview");
  return response.data;
}

export async function getRentalTimeline(params: {
  page?: number;
  limit?: number;
  user_id?: number;
  car_id?: number;
  status_filter?: string;
}): Promise<RentalTimelineResponse> {
  const response = await api.get<RentalTimelineResponse>("/admin/rental-timeline", { params });
  return response.data;
}

export async function getExpenses(params: { page?: number; limit?: number }): Promise<ExpenseListResponse> {
  const response = await api.get<ExpenseListResponse>("/admin/expenses", { params });
  return response.data;
}

export async function createExpense(payload: {
  title: string;
  amount: number;
  category: string;
  expense_date: string;
  note?: string;
}): Promise<Expense> {
  const response = await api.post<Expense>("/admin/expenses", payload);
  return response.data;
}

export async function getClientRequests(params: {
  page?: number;
  limit?: number;
  status_filter?: string;
}): Promise<ClientRequestListResponse> {
  const response = await api.get<ClientRequestListResponse>("/admin/client-requests", { params });
  return response.data;
}

export async function updateClientRequest(
  requestId: number,
  payload: { status?: "open" | "in_progress" | "resolved" | "rejected"; admin_comment?: string }
): Promise<ClientRequest> {
  const response = await api.patch<ClientRequest>(`/admin/client-requests/${requestId}`, payload);
  return response.data;
}

export async function getMyClientRequests(): Promise<ClientRequest[]> {
  const response = await api.get<ClientRequest[]>("/profile/requests");
  return response.data;
}

export async function createMyClientRequest(payload: { subject: string; message: string }): Promise<ClientRequest> {
  const response = await api.post<ClientRequest>("/profile/requests", payload);
  return response.data;
}

export async function createRental(payload: {
  car_id: number;
  start_date: string;
  end_date: string;
}): Promise<Rental> {
  const response = await api.post<Rental>("/rentals/", payload);
  return response.data;
}

export async function createWaitlistEntry(payload: {
  car_id: number;
  start_date: string;
  end_date: string;
}): Promise<WaitlistEntry> {
  const response = await api.post<WaitlistEntry>("/rentals/waitlist", payload);
  return response.data;
}

export async function getMyWaitlist(): Promise<WaitlistEntry[]> {
  const response = await api.get<WaitlistEntry[]>("/rentals/waitlist/my");
  return response.data;
}

export async function getMyRentals(params?: { page?: number; limit?: number }): Promise<RentalListResponse> {
  const response = await api.get<RentalListResponse>("/rentals/my", { params });
  return response.data;
}

export async function completeRental(rentalId: number): Promise<{ message: string }> {
  const response = await api.patch<{ message: string }>(`/rentals/${rentalId}/complete`);
  return response.data;
}

export async function getChargingStations(params?: {
  page?: number;
  limit?: number;
  city?: string;
  connector_type?: string;
  available_only?: boolean;
  sort_by?: "price_per_kwh" | "power_kw" | "city" | "name";
  sort_order?: "asc" | "desc";
}): Promise<ChargingStationListResponse> {
  const response = await api.get<ChargingStationListResponse>("/charging-stations/", { params });
  return response.data;
}

export async function createChargingStation(payload: {
  name: string;
  city: string;
  address: string;
  charger_type: string;
  connector_types: string;
  slot_count: number;
  power_kw: number;
  price_per_kwh: number;
  latitude?: number;
  longitude?: number;
  is_available?: boolean;
  note?: string;
}): Promise<ChargingStation> {
  const response = await api.post<ChargingStation>("/charging-stations/", payload);
  return response.data;
}

export async function updateChargingStationAvailability(
  stationId: number,
  payload: { is_available: boolean }
): Promise<ChargingStation> {
  const response = await api.patch<ChargingStation>(`/charging-stations/${stationId}/availability`, payload);
  return response.data;
}

export async function createChargingSession(payload: {
  rental_id: number;
  station_id: number;
  charged_at: string;
  kwh_amount: number;
  price_per_kwh?: number;
  duration_minutes?: number;
  battery_percent_start?: number;
  battery_percent_end?: number;
  payment_status?: "paid" | "pending";
  note?: string;
}): Promise<ChargingSession> {
  const response = await api.post<ChargingSession>("/charging-stations/sessions", payload);
  return response.data;
}

export async function getMyChargingSessions(params?: {
  page?: number;
  limit?: number;
}): Promise<ChargingSessionListResponse> {
  const response = await api.get<ChargingSessionListResponse>("/charging-stations/sessions/my", { params });
  return response.data;
}

export async function getAllChargingSessions(params?: {
  page?: number;
  limit?: number;
}): Promise<ChargingSessionListResponse> {
  const response = await api.get<ChargingSessionListResponse>("/charging-stations/sessions", { params });
  return response.data;
}

export async function createChargingBooking(payload: {
  station_id: number;
  booking_date: string;
  start_time: string;
  end_time: string;
  note?: string;
}): Promise<ChargingBooking> {
  const response = await api.post<ChargingBooking>("/charging-stations/bookings", payload);
  return response.data;
}

export async function getMyChargingBookings(params?: {
  page?: number;
  limit?: number;
}): Promise<ChargingBookingListResponse> {
  const response = await api.get<ChargingBookingListResponse>("/charging-stations/bookings/my", { params });
  return response.data;
}

export async function getAllChargingBookings(params?: {
  page?: number;
  limit?: number;
}): Promise<ChargingBookingListResponse> {
  const response = await api.get<ChargingBookingListResponse>("/charging-stations/bookings", { params });
  return response.data;
}

export async function updateChargingBooking(
  bookingId: number,
  payload: { status: "booked" | "completed" | "canceled" }
): Promise<ChargingBooking> {
  const response = await api.patch<ChargingBooking>(`/charging-stations/bookings/${bookingId}`, payload);
  return response.data;
}

export async function createChargingReview(payload: {
  station_id: number;
  rating: number;
  comment?: string;
}): Promise<ChargingReview> {
  const response = await api.post<ChargingReview>("/charging-stations/reviews", payload);
  return response.data;
}

export async function getChargingReviews(params?: {
  page?: number;
  limit?: number;
  station_id?: number;
}): Promise<ChargingReviewListResponse> {
  const response = await api.get<ChargingReviewListResponse>("/charging-stations/reviews", { params });
  return response.data;
}

export async function getMyChargingAnalytics(): Promise<ChargingAnalytics> {
  const response = await api.get<ChargingAnalytics>("/charging-stations/analytics/my");
  return response.data;
}

export async function getMyChargingNotifications(params?: {
  page?: number;
  limit?: number;
}): Promise<ChargingNotificationListResponse> {
  const response = await api.get<ChargingNotificationListResponse>("/charging-stations/notifications/my", { params });
  return response.data;
}

export async function updateChargingNotification(
  notificationId: number,
  payload: { is_read: boolean }
): Promise<ChargingNotification> {
  const response = await api.patch<ChargingNotification>(`/charging-stations/notifications/${notificationId}`, payload);
  return response.data;
}

export async function getAllRentals(params?: {
  page?: number;
  limit?: number;
  sort_order?: "asc" | "desc";
}): Promise<RentalListResponse> {
  const response = await api.get<RentalListResponse>("/rentals/", { params });
  return response.data;
}

export async function getMyChat(): Promise<ChatMessage[]> {
  const response = await api.get<ChatMessage[]>("/chat/my");
  return response.data;
}

export async function sendChatMessage(payload: { message: string; user_id?: number }): Promise<ChatMessage> {
  const response = await api.post<ChatMessage>("/chat/send", payload);
  return response.data;
}

export async function getAdminChatUsers(): Promise<User[]> {
  const response = await api.get<User[]>("/chat/users");
  return response.data;
}

export async function getAdminUserChat(userId: number): Promise<ChatMessage[]> {
  const response = await api.get<ChatMessage[]>(`/chat/user/${userId}`);
  return response.data;
}

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}
