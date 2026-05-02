
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  completeRental,
  confirmRegister,
  createCar,
  createExpense,
  createMyClientRequest,
  createWaitlistEntry,
  createRental,
  deleteCar,
  getAdminChatUsers,
  getAdminUserChat,
  getAdminUsers,
  getAllRentals,
  getAdminOverview,
  getAuditLogs,
  getCars,
  getClientRequests,
  getExpenses,
  getMe,
  getMyChat,
  getMyClientRequests,
  getMyDocuments,
  getMyRentals,
  getMyWaitlist,
  getRentalTimeline,
  login,
  requestRegisterCode,
  sendChatMessage,
  setAuthToken,
  transferAdminRole,
  updateCarService,
  updateClientRequest,
  updateUserBlacklist,
  uploadMyDocument
} from "./api";
import { createTourRequest, listTourRequests } from "./firestore";
import type {
  AdminOverview,
  AuditLog,
  Car,
  ChatMessage,
  ClientRequest,
  Expense,
  Rental,
  RentalTimelineItem,
  TourRequest,
  User,
  UserDocument,
  WaitlistEntry
} from "./types";

type StatusFilter = "all" | "available" | "rented" | "service";
type CategoryFilter = "all" | "econom" | "budget" | "comfort" | "lux";
type AdminView = "fleet" | "ops" | "audit" | "users" | "rentals" | "chat" | "tourRequests";
type ClientView = "fleet" | "rentals" | "docs" | "support" | "tours";
type SortBy = "price_per_day" | "year" | "brand";
type SortOrder = "asc" | "desc";
type RequestStatus = "open" | "in_progress" | "resolved" | "rejected";
type Lang = "kz" | "ru";
type TourPackage = {
  id: string;
  titleKz: string;
  titleRu: string;
  routeKz: string;
  routeRu: string;
  days: number;
  price: number;
  carClassKz: string;
  carClassRu: string;
  perksKz: string[];
  perksRu: string[];
};

const TOKEN_KEY = "autorent_token";
const LANG_KEY = "autorent_lang";
const TOUR_PACKAGES: TourPackage[] = [
  {
    id: "almaty-lakes",
    titleKz: "Алматы көлдері уикенді",
    titleRu: "Уикенд по озерам Алматы",
    routeKz: "Алматы - Қапшағай - Көлсай - Қайыңды - Алматы",
    routeRu: "Алматы - Капшагай - Кольсай - Каинды - Алматы",
    days: 3,
    price: 145000,
    carClassKz: "Comfort SUV",
    carClassRu: "Comfort SUV",
    perksKz: ["Көлік + сақтандыру", "Маршрут жоспары", "Фото-тоқтау нүктелері", "24/7 қолдау"],
    perksRu: ["Авто + страховка", "План маршрута", "Фото-точки", "Поддержка 24/7"]
  },
  {
    id: "turkistan-family",
    titleKz: "Түркістан family road trip",
    titleRu: "Семейный road trip в Туркестан",
    routeKz: "Шымкент - Түркістан - Отырар - Арыстанбаб - Шымкент",
    routeRu: "Шымкент - Туркестан - Отрар - Арыстанбаб - Шымкент",
    days: 2,
    price: 98000,
    carClassKz: "Minivan",
    carClassRu: "Minivan",
    perksKz: ["Отбасылық пакет", "Балаларға ыңғайлы көлік", "Гидсіз еркін саяхат", "Қонақүй ұсыныстары"],
    perksRu: ["Семейный пакет", "Комфортное авто для детей", "Свободная поездка без гида", "Подборка отелей"]
  },
  {
    id: "astana-burabay",
    titleKz: "Астана - Бурабай premium",
    titleRu: "Астана - Бурабай premium",
    routeKz: "Астана - Щучинск - Бурабай - Астана",
    routeRu: "Астана - Щучинск - Боровое - Астана",
    days: 2,
    price: 132000,
    carClassKz: "Business sedan",
    carClassRu: "Business sedan",
    perksKz: ["Premium трансфер стилі", "Кофе-тоқтау картасы", "Чек-лист маршрут", "Ерте бронь жеңілдігі"],
    perksRu: ["Стиль premium-трансфера", "Карта coffee stop", "Чек-лист маршрута", "Скидка за раннее бронирование"]
  }
];
const STARTUP_IDEAS = [
  {
    kz: "Dynamic package builder: клиент күн санын, қаланы, көлік класын таңдап, баға автоматты жиналсын.",
    ru: "Dynamic package builder: клиент выбирает город, дни и класс авто, а цена собирается автоматически."
  },
  {
    kz: "Partner marketplace: қонақүй, кафе, экскурсия, жанармай бекеті бойынша серіктес ұсыныстар қосу.",
    ru: "Partner marketplace: добавить партнерские предложения отелей, кафе, экскурсий и АЗС."
  },
  {
    kz: "Travel concierge subscription: ай сайынғы жазылыммен VIP support, маршрут update, airport pickup ұсыну.",
    ru: "Travel concierge subscription: ежемесячная подписка с VIP support, обновлением маршрута и airport pickup."
  },
  {
    kz: "User-generated routes: клиенттер өз маршрутын жариялап, рейтинг жинайтын community модуль.",
    ru: "User-generated routes: community-модуль, где клиенты публикуют свои маршруты и получают рейтинг."
  },
  {
    kz: "Corporate getaway packs: компанияларға тимбилдинг және оффсайт пакет сату.",
    ru: "Corporate getaway packs: продавать компаниям пакеты для тимбилдинга и оффсайта."
  }
];

function formatMoney(v: number) {
  return `${Math.round(v).toLocaleString()} тг`;
}

function tr(lang: Lang, kz: string, ru: string) {
  return lang === "kz" ? kz : ru;
}

function apiErrorMessage(error: unknown, fallback: string) {
  if (typeof error === "object" && error && "response" in error) {
    const response = (error as { response?: { data?: { detail?: string; message?: string } } }).response;
    const detail = response?.data?.detail || response?.data?.message;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  return fallback;
}

function downloadCsv(filename: string, headers: string[], rows: Array<Array<string | number | null | undefined>>) {
  const escape = (value: string | number | null | undefined) => {
    const raw = String(value ?? "");
    return `"${raw.replace(/"/g, '""')}"`;
  };
  const content = [headers.map(escape).join(","), ...rows.map((row) => row.map(escape).join(","))].join("\n");
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function openReceiptAsPdf(rental: Rental, lang: Lang) {
  const html = `
    <html>
      <head>
        <title>AutoRent Receipt #${rental.id}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 24px; color: #111827; }
          h1 { margin: 0 0 16px; }
          .row { margin: 8px 0; }
          .label { color: #4b5563; width: 180px; display: inline-block; }
        </style>
      </head>
      <body>
        <h1>AutoRent ${lang === "kz" ? "Чек" : "Чек"}</h1>
        <div class="row"><span class="label">${lang === "kz" ? "Бронь ID" : "Бронь ID"}:</span> #${rental.id}</div>
        <div class="row"><span class="label">${lang === "kz" ? "Клиент ID" : "Клиент ID"}:</span> ${rental.user_id}</div>
        <div class="row"><span class="label">${lang === "kz" ? "Көлік ID" : "Авто ID"}:</span> ${rental.car_id}</div>
        <div class="row"><span class="label">${lang === "kz" ? "Күні" : "Период"}:</span> ${rental.start_date} - ${rental.end_date}</div>
        <div class="row"><span class="label">${lang === "kz" ? "Сома" : "Сумма"}:</span> ${Math.round(rental.total_price).toLocaleString()} тг</div>
        <div class="row"><span class="label">${lang === "kz" ? "Статус" : "Статус"}:</span> ${rental.status}</div>
        <script>window.print()</script>
      </body>
    </html>
  `;
  const w = window.open("", "_blank");
  if (!w) return;
  w.document.write(html);
  w.document.close();
}

function getRequestStatusLabel(status: RequestStatus, lang: Lang) {
  if (status === "open") return tr(lang, "Жаңа", "Новый");
  if (status === "in_progress") return tr(lang, "Өңделуде", "В работе");
  if (status === "resolved") return tr(lang, "Шешілді", "Решено");
  return tr(lang, "Қабылданбады", "Отклонено");
}

function TourPackagesPanel({ lang, user }: { lang: Lang; user: User }) {
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submitTourRequest = async (tour: TourPackage) => {
    setSubmittingId(tour.id);
    setMessage(null);
    setError(null);
    try {
      await createTourRequest({
        packageId: tour.id,
        packageTitle: lang === "kz" ? tour.titleKz : tour.titleRu,
        route: lang === "kz" ? tour.routeKz : tour.routeRu,
        days: tour.days,
        price: tour.price,
        userId: user.id,
        userEmail: user.email,
        userFullName: user.full_name,
        userPhone: user.phone
      });
      setMessage(tr(lang, "Сұраныс Firestore-ға сақталды", "Заявка сохранена в Firestore"));
    } catch (err) {
      setError(
        apiErrorMessage(
          err,
          tr(
            lang,
            "Firestore баптауы жоқ немесе сұраныс сақталмады",
            "Нет настройки Firestore или заявка не сохранилась"
          )
        )
      );
    } finally {
      setSubmittingId(null);
    }
  };

  return (
    <section className="panel section-panel">
      <div className="section-head">
        <div>
          <h2>{tr(lang, "Tour Packages", "Tour Packages")}</h2>
          <p className="panel-subtitle">
            {tr(
              lang,
              "Қалалар арасында көлікпен саяхатқа арналған дайын пакеттер.",
              "Готовые пакеты для путешествий между городами на арендованных авто."
            )}
          </p>
        </div>
      </div>

      <div className="stats-grid tour-stats">
        <article className="stat-card">
          <p>{tr(lang, "Дайын пакет", "Готовых пакетов")}</p>
          <strong>{TOUR_PACKAGES.length}</strong>
        </article>
        <article className="stat-card">
          <p>{tr(lang, "Орташа чек", "Средний чек")}</p>
          <strong>{formatMoney(TOUR_PACKAGES.reduce((acc, row) => acc + row.price, 0) / TOUR_PACKAGES.length)}</strong>
        </article>
        <article className="stat-card">
          <p>{tr(lang, "Фокус", "Фокус")}</p>
          <strong>{tr(lang, "Road trip", "Road trip")}</strong>
        </article>
      </div>
      {message && <p className="info-banner">{message}</p>}
      {error && <p className="error">{error}</p>}

      <div className="tour-grid">
        {TOUR_PACKAGES.map((tour) => (
          <article key={tour.id} className="tour-card">
            <span className="panel-tag">{tour.days} {tr(lang, "күн", "дня")}</span>
            <h3>{lang === "kz" ? tour.titleKz : tour.titleRu}</h3>
            <p className="tour-route">{lang === "kz" ? tour.routeKz : tour.routeRu}</p>
            <div className="doc-row tour-meta">
              <span>{tr(lang, "Ұсынылатын көлік", "Рекомендуемое авто")}: {lang === "kz" ? tour.carClassKz : tour.carClassRu}</span>
              <span>{tr(lang, "Баға", "Цена")}: {formatMoney(tour.price)}</span>
            </div>
            <ul className="tour-list">
              {(lang === "kz" ? tour.perksKz : tour.perksRu).map((perk) => (
                <li key={perk}>{perk}</li>
              ))}
            </ul>
            <button onClick={() => void submitTourRequest(tour)} disabled={submittingId === tour.id}>
              {submittingId === tour.id
                ? tr(lang, "Жіберілуде...", "Отправка...")
                : tr(lang, "Пакетке сұраныс жіберу", "Отправить запрос на пакет")}
            </button>
          </article>
        ))}
      </div>

      <div className="tour-ideas">
        <h3>{tr(lang, "Стартап ретінде қосатын идеялар", "Идеи для стартап-роста")}</h3>
        <div className="ideas-grid">
          {STARTUP_IDEAS.map((idea) => (
            <article key={idea.kz} className="idea-card">
              <strong>{tr(lang, "Growth idea", "Growth idea")}</strong>
              <p>{lang === "kz" ? idea.kz : idea.ru}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function LoginView({ onLogin, lang }: { onLogin: (email: string, password: string) => Promise<void>; lang: Lang }) {
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [code, setCode] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const submitLogin = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await onLogin(loginEmail, loginPassword);
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Кіру қатесі", "Ошибка входа")));
    }
  };

  const loginDemo = async (email: string, password: string) => {
    setError(null);
    setMessage(null);
    try {
      await onLogin(email, password);
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Demo кіру қатесі", "Ошибка demo-входа")));
    }
  };

  const sendCode = async () => {
    setError(null);
    setMessage(null);
    try {
      await requestRegisterCode(registerEmail);
      setMessage(tr(lang, "Код email-ға жіберілді", "Код отправлен на email"));
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Код жіберу қатесі", "Ошибка отправки кода")));
    }
  };

  const submitRegister = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await confirmRegister({
        email: registerEmail,
        password: registerPassword,
        code,
        full_name: fullName || undefined,
        phone: phone || undefined
      });
      setMessage(tr(lang, "Тіркелу аяқталды", "Регистрация завершена"));
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Тіркелу қатесі", "Ошибка регистрации")));
    }
  };

  return (
    <section className="auth-grid">
      <article className="panel auth-card">
        <h2>{tr(lang, "AutoRent Pro - Кіру", "AutoRent Pro - Вход")}</h2>
        <form className="form-stack" onSubmit={submitLogin}>
          <input type="email" placeholder="Email" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} required />
          <input type="password" placeholder={tr(lang, "Құпиясөз", "Пароль")} value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} required />
          <button type="submit">{tr(lang, "Кіру", "Войти")}</button>
        </form>
        <div className="demo-row">
          <button className="soft" onClick={() => void loginDemo("usmanovamaftuna95@gmail.com", "Admin123!")}>
            {tr(lang, "Demo Admin", "Demo Admin")}
          </button>
          <button className="soft" onClick={() => void loginDemo("muhammaddin.turauli@mail.ru", "Mtzs2023!")}>
            {tr(lang, "Demo Client", "Demo Client")}
          </button>
        </div>
      </article>

      <article className="panel auth-card">
        <h2>{tr(lang, "Код арқылы тіркелу", "Регистрация по коду")}</h2>
        <form className="form-stack" onSubmit={submitRegister}>
          <input type="email" placeholder="Email" value={registerEmail} onChange={(e) => setRegisterEmail(e.target.value)} required />
          <input type="password" placeholder={tr(lang, "Құпиясөз", "Пароль")} value={registerPassword} onChange={(e) => setRegisterPassword(e.target.value)} required />
          <input type="text" placeholder={tr(lang, "Толық аты", "Полное имя")} value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <input type="text" placeholder={tr(lang, "Телефон", "Телефон")} value={phone} onChange={(e) => setPhone(e.target.value)} />
          <input type="text" placeholder={tr(lang, "Растау коды", "Код подтверждения")} value={code} onChange={(e) => setCode(e.target.value)} required />
          <button type="button" className="soft" onClick={() => void sendCode()}>{tr(lang, "Код жіберу", "Отправить код")}</button>
          <button type="submit">{tr(lang, "Тіркелуді растау", "Подтвердить регистрацию")}</button>
        </form>
      </article>
      {message && <p className="info-banner">{message}</p>}
      {error && <p className="error">{error}</p>}
    </section>
  );
}

function StatsBar({ cars, lang }: { cars: Car[]; lang: Lang }) {
  const total = cars.length;
  const free = cars.filter((c) => c.status === "available").length;
  const busy = cars.filter((c) => c.status === "rented").length;
  const avg = total ? Math.round(cars.reduce((acc, c) => acc + c.price_per_day, 0) / total) : 0;

  return (
    <div className="stats-grid">
      <article className="stat-card"><p>{tr(lang, "Жалпы көлік", "Всего авто")}</p><strong>{total}</strong></article>
      <article className="stat-card"><p>{tr(lang, "Бос", "Свободно")}</p><strong>{free}</strong></article>
      <article className="stat-card"><p>{tr(lang, "Жалдауда", "В аренде")}</p><strong>{busy}</strong></article>
      <article className="stat-card"><p>{tr(lang, "Орташа баға", "Средняя цена")}</p><strong>{formatMoney(avg)}</strong></article>
    </div>
  );
}
function CarsGrid({
  adminMode,
  lang,
  onBooked
}: {
  adminMode: boolean;
  lang: Lang;
  onBooked?: () => void;
}) {
  const [cars, setCars] = useState<Car[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [sortBy, setSortBy] = useState<SortBy>("price_per_day");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [minPrice, setMinPrice] = useState(0);
  const [maxPrice, setMaxPrice] = useState(100000);
  const [showFilters, setShowFilters] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState(2024);
  const [pricePerDay, setPricePerDay] = useState(25000);
  const [mainImageUrl, setMainImageUrl] = useState("");
  const [bookingCarId, setBookingCarId] = useState<number | null>(null);
  const [bookingStartDate, setBookingStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [bookingEndDate, setBookingEndDate] = useState("");
  const [bookingMessage, setBookingMessage] = useState<string | null>(null);
  const [waitlistMessage, setWaitlistMessage] = useState<string | null>(null);
  const selectedBookingCar = useMemo(
    () => cars.find((car) => car.id === bookingCarId) || null,
    [cars, bookingCarId]
  );
  const bookingDays = useMemo(() => {
    if (!bookingStartDate || !bookingEndDate) return 0;
    const start = new Date(bookingStartDate);
    const end = new Date(bookingEndDate);
    const diffMs = end.getTime() - start.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  }, [bookingStartDate, bookingEndDate]);
  const bookingPreviewPrice = useMemo(() => {
    if (!selectedBookingCar || !bookingDays) return 0;
    return bookingDays * selectedBookingCar.price_per_day;
  }, [selectedBookingCar, bookingDays]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / 8)), [total]);

  const loadCars = async () => {
    try {
      const result = await getCars({
        page,
        limit: 8,
        q: q || undefined,
        status: status === "all" ? undefined : status,
        category: category === "all" ? undefined : category,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      });
      setCars(result.items);
      setTotal(result.total);
      setError(null);
    } catch {
      setError(tr(lang, "Көліктер жүктелмеді", "Не удалось загрузить машины"));
    }
  };

  useEffect(() => { void loadCars(); }, [page, q, status, category, sortBy, sortOrder, minPrice, maxPrice]);

  const resetFilters = () => {
    setQ("");
    setStatus("all");
    setCategory("all");
    setSortBy("price_per_day");
    setSortOrder("asc");
    setMinPrice(0);
    setMaxPrice(100000);
    setPage(1);
  };

  const submitCreateCar = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await createCar({ brand, model, year, price_per_day: pricePerDay, status: "available", main_image_url: mainImageUrl || undefined, category: "comfort" });
      setBrand("");
      setModel("");
      setMainImageUrl("");
      void loadCars();
    } catch {
      setError(tr(lang, "Қосу қатесі", "Ошибка добавления"));
    }
  };

  const updateServiceSchedule = async (carId: number) => {
    const serviceDate = window.prompt(tr(lang, "Келесі сервис күні (YYYY-MM-DD)", "Следующая дата сервиса (YYYY-MM-DD)"));
    if (serviceDate === null) return;
    const serviceNote = window.prompt(tr(lang, "Сервис ескертпесі", "Комментарий сервиса")) || "";
    try {
      await updateCarService(carId, {
        next_service_date: serviceDate.trim() || null,
        service_note: serviceNote.trim() || null
      });
      await loadCars();
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Сервис жаңарту қатесі", "Ошибка обновления сервиса")));
    }
  };

  const submitBooking = async (event: FormEvent) => {
    event.preventDefault();
    if (!bookingCarId) return;
    setError(null);
    setBookingMessage(null);
    setWaitlistMessage(null);
    try {
      await createRental({
        car_id: bookingCarId,
        start_date: bookingStartDate,
        end_date: bookingEndDate
      });
      setBookingMessage(tr(lang, "Бронь сәтті жасалды", "Бронь успешно создана"));
      setBookingCarId(null);
      setBookingEndDate("");
      await loadCars();
      onBooked?.();
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Бронь жасау қатесі", "Ошибка создания брони")));
    }
  };

  const joinWaitlist = async (carId: number) => {
    const startDate = window.prompt(tr(lang, "Күтілетін басталу күні (YYYY-MM-DD)", "Желаемая дата начала (YYYY-MM-DD)"));
    if (!startDate) return;
    const endDate = window.prompt(tr(lang, "Күтілетін аяқталу күні (YYYY-MM-DD)", "Желаемая дата окончания (YYYY-MM-DD)"));
    if (!endDate) return;
    setError(null);
    setWaitlistMessage(null);
    try {
      await createWaitlistEntry({
        car_id: carId,
        start_date: startDate.trim(),
        end_date: endDate.trim(),
      });
      setWaitlistMessage(tr(lang, "Сіз күту тізіміне қосылдыңыз", "Вы добавлены в лист ожидания"));
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Күту тізіміне қосу қатесі", "Ошибка добавления в лист ожидания")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Автопарк", "Автопарк")}</h2>
      <StatsBar cars={cars} lang={lang} />
      <div className="section-head">
        <p className="panel-subtitle">{tr(lang, "Іздеу және фильтр", "Поиск и фильтр")}</p>
        <button className="soft mobile-only" onClick={() => setShowFilters((v) => !v)}>
          {showFilters ? tr(lang, "Фильтрді жасыру", "Скрыть фильтры") : tr(lang, "Фильтрді ашу", "Открыть фильтры")}
        </button>
      </div>
      <div className={`filters-grid ${showFilters ? "is-open" : ""}`}>
        <input placeholder={tr(lang, "Іздеу", "Поиск")} value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
          <option value="all">{tr(lang, "Барлық статус", "Все статусы")}</option><option value="available">{tr(lang, "Қолжетімді", "Доступно")}</option><option value="rented">{tr(lang, "Жалдауда", "В аренде")}</option><option value="service">{tr(lang, "Сервисте", "Сервис")}</option>
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value as CategoryFilter)}>
          <option value="all">{tr(lang, "Барлық санат", "Все категории")}</option><option value="econom">{tr(lang, "Эконом", "Эконом")}</option><option value="budget">{tr(lang, "Бюджет", "Бюджет")}</option><option value="comfort">{tr(lang, "Комфорт", "Комфорт")}</option><option value="lux">{tr(lang, "Люкс", "Люкс")}</option>
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortBy)}>
          <option value="price_per_day">{tr(lang, "Баға", "Цена")}</option><option value="year">{tr(lang, "Жыл", "Год")}</option><option value="brand">{tr(lang, "Бренд", "Бренд")}</option>
        </select>
        <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as SortOrder)}>
          <option value="asc">{tr(lang, "Өсу реті", "По возрастанию")}</option><option value="desc">{tr(lang, "Кему реті", "По убыванию")}</option>
        </select>
        <input type="number" placeholder={tr(lang, "Мин. баға", "Мин. цена")} value={minPrice} onChange={(e) => setMinPrice(Number(e.target.value || 0))} />
        <input type="number" placeholder={tr(lang, "Макс. баға", "Макс. цена")} value={maxPrice} onChange={(e) => setMaxPrice(Number(e.target.value || 0))} />
        <button onClick={() => void loadCars()}>{tr(lang, "Қолдану", "Применить")}</button>
        <button className="soft" onClick={resetFilters}>{tr(lang, "Тазалау", "Сбросить")}</button>
      </div>

      {adminMode && (
        <form className="admin-form" onSubmit={submitCreateCar}>
          <input placeholder={tr(lang, "Бренд", "Бренд")} value={brand} onChange={(e) => setBrand(e.target.value)} required />
          <input placeholder={tr(lang, "Модель", "Модель")} value={model} onChange={(e) => setModel(e.target.value)} required />
          <input type="number" placeholder={tr(lang, "Жыл", "Год")} value={year} onChange={(e) => setYear(Number(e.target.value))} required />
          <input type="number" placeholder={tr(lang, "Күндік баға", "Цена в день")} value={pricePerDay} onChange={(e) => setPricePerDay(Number(e.target.value))} required />
          <input placeholder={tr(lang, "Сурет URL", "URL фото")} value={mainImageUrl} onChange={(e) => setMainImageUrl(e.target.value)} />
          <button type="submit">{tr(lang, "Көлік қосу", "Добавить авто")}</button>
        </form>
      )}

      {error && <p className="error">{error}</p>}
      {bookingMessage && <p className="info-banner">{bookingMessage}</p>}
      {waitlistMessage && <p className="info-banner">{waitlistMessage}</p>}
      {!adminMode && bookingCarId && (
        <form className="booking-form" onSubmit={submitBooking}>
          <h3>{tr(lang, "Бронь жасау", "Создать бронь")}</h3>
          <input type="date" value={bookingStartDate} onChange={(e) => setBookingStartDate(e.target.value)} required />
          <input type="date" value={bookingEndDate} onChange={(e) => setBookingEndDate(e.target.value)} required />
          <p className="booking-preview">
            {tr(lang, "Алдын ала есеп", "Предварительный расчет")}:
            {" "}
            {bookingDays
              ? `${bookingDays} ${tr(lang, "күн", "дн.")} = ${formatMoney(bookingPreviewPrice)}`
              : tr(lang, "күнді таңдаңыз", "выберите даты")}
          </p>
          <button type="submit">{tr(lang, "Растау", "Подтвердить")}</button>
          <button type="button" className="soft" onClick={() => setBookingCarId(null)}>
            {tr(lang, "Бас тарту", "Отмена")}
          </button>
        </form>
      )}
      <div className="cars-grid">
        {cars.map((car) => (
          <article className="car-card" key={car.id}>
            <img src={car.main_image_url || car.photos[0]?.url || "https://images.unsplash.com/photo-1553440569-bcc63803a83d?auto=format&fit=crop&w=1200&q=80"} alt={`${car.brand} ${car.model}`} className="car-photo" />
            <h3>{car.brand} {car.model}</h3>
            <p>{car.year} | {car.category}</p>
            <span className={`pill ${car.status === "available" ? "status-available" : car.status === "rented" ? "status-rented" : "status-service"}`}>
              {car.status === "available" ? tr(lang, "Қолжетімді", "Доступно") : car.status === "rented" ? tr(lang, "Жалдауда", "В аренде") : car.status === "service" ? tr(lang, "Сервисте", "Сервис") : car.status}
            </span>
            <p>{formatMoney(car.price_per_day)} / {tr(lang, "күн", "день")}</p>
            {adminMode && (
              <p className="service-note">
                {tr(lang, "Келесі сервис", "Следующий сервис")}: {car.next_service_date || "-"}
              </p>
            )}
            {adminMode && <button onClick={() => void deleteCar(car.id).then(loadCars)}>{tr(lang, "Өшіру", "Удалить")}</button>}
            {adminMode && <button className="soft" onClick={() => void updateServiceSchedule(car.id)}>{tr(lang, "Сервис жоспары", "План сервиса")}</button>}
            {!adminMode && car.status === "available" && (
              <button onClick={() => setBookingCarId(car.id)}>
                {tr(lang, "Бронь жасау", "Забронировать")}
              </button>
            )}
            {!adminMode && car.status !== "available" && (
              <button className="soft" onClick={() => void joinWaitlist(car.id)}>
                {tr(lang, "Күту тізімі", "Лист ожидания")}
              </button>
            )}
          </article>
        ))}
      </div>
      {!cars.length && <p className="empty-note">{tr(lang, "Сүзгіге сай көлік табылмады", "Машины по фильтру не найдены")}</p>}
      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage((v) => v - 1)}>{tr(lang, "Артқа", "Назад")}</button>
        <span>{page}/{totalPages}</span>
        <button disabled={page >= totalPages} onClick={() => setPage((v) => v + 1)}>{tr(lang, "Келесі", "Далее")}</button>
      </div>
    </section>
  );
}

function DocumentsPanel({ lang }: { lang: Lang }) {
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [docType, setDocType] = useState("");
  const [docNumber, setDocNumber] = useState("");
  const [docFile, setDocFile] = useState<File | null>(null);

  const loadDocs = async () => setDocuments(await getMyDocuments());
  useEffect(() => { void loadDocs(); }, []);

  const submitDoc = async (event: FormEvent) => {
    event.preventDefault();
    if (!docFile) return;
    await uploadMyDocument({ document_type: docType, document_number: docNumber, file: docFile });
    setDocType("");
    setDocNumber("");
    setDocFile(null);
    await loadDocs();
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Құжаттар", "Документы")}</h2>
      <form className="admin-form" onSubmit={submitDoc}>
        <input placeholder={tr(lang, "Құжат түрі", "Тип документа")} value={docType} onChange={(e) => setDocType(e.target.value)} required />
        <input placeholder={tr(lang, "Құжат нөмірі", "Номер документа")} value={docNumber} onChange={(e) => setDocNumber(e.target.value)} required />
        <input type="file" onChange={(e) => setDocFile(e.target.files?.[0] ?? null)} required />
        <button type="submit">{tr(lang, "Жүктеу", "Загрузить")}</button>
      </form>
      {documents.map((doc) => (<div key={doc.id} className="doc-row"><span>{doc.document_type} #{doc.document_number}</span><span>{new Date(doc.uploaded_at).toLocaleString()}</span></div>))}
      {!documents.length && <p className="empty-note">{tr(lang, "Құжаттар әлі жүктелмеген", "Документы пока не загружены")}</p>}
    </section>
  );
}

function ClientRequestsPanel({ lang }: { lang: Lang }) {
  const [items, setItems] = useState<ClientRequest[]>([]);
  const [waitlist, setWaitlist] = useState<WaitlistEntry[]>([]);
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [chatText, setChatText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [requests, waitlistRows, chatRows] = await Promise.all([
        getMyClientRequests(),
        getMyWaitlist(),
        getMyChat(),
      ]);
      setItems(requests);
      setWaitlist(waitlistRows);
      setChat(chatRows);
      setError(null);
    } catch (err) {
      setError(apiErrorMessage(err, tr(lang, "Қолдау деректері жүктелмеді", "Данные поддержки не загрузились")));
    }
  };
  useEffect(() => { void load(); }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await createMyClientRequest({ subject, message });
    setSubject("");
    setMessage("");
    await load();
  };

  const submitChat = async (event: FormEvent) => {
    event.preventDefault();
    if (!chatText.trim()) return;
    try {
      await sendChatMessage({ message: chatText.trim() });
      setChatText("");
      await load();
    } catch (err) {
      setError(apiErrorMessage(err, tr(lang, "Чат хабарламасын жіберу қатесі", "Ошибка отправки чата")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Қолдау сұраныстары", "Запросы в поддержку")}</h2>
      {error && <p className="error">{error}</p>}
      <form className="form-stack" onSubmit={submit}>
        <input placeholder={tr(lang, "Тақырып", "Тема")} value={subject} onChange={(e) => setSubject(e.target.value)} required />
        <textarea className="textarea" placeholder={tr(lang, "Хабарлама", "Сообщение")} value={message} onChange={(e) => setMessage(e.target.value)} required />
        <button type="submit">{tr(lang, "Жіберу", "Отправить")}</button>
      </form>
      {items.map((row) => (<div key={row.id} className="doc-row support-row"><span>{row.subject}</span><span>{getRequestStatusLabel(row.status, lang)}</span><span>{new Date(row.created_at).toLocaleString()}</span></div>))}
      {!items.length && <p className="empty-note">{tr(lang, "Сұраныстар жоқ", "Запросов пока нет")}</p>}

      <h3>{tr(lang, "Күту тізімім", "Мой лист ожидания")}</h3>
      {waitlist.map((row) => (
        <div key={row.id} className="doc-row support-row">
          <span>{tr(lang, "Көлік ID", "Авто ID")}: {row.car_id}</span>
          <span>{row.start_date} - {row.end_date}</span>
          <span>{row.status}</span>
        </div>
      ))}
      {!waitlist.length && <p className="empty-note">{tr(lang, "Күту тізімі бос", "Лист ожидания пуст")}</p>}

      <h3>{tr(lang, "In-app чат (админмен)", "In-app чат (с админом)")}</h3>
      <div className="chat-box">
        {chat.map((row) => (
          <div key={row.id} className={`chat-row ${row.sender_role === "admin" ? "chat-admin" : "chat-user"}`}>
            <span>{row.sender_role === "admin" ? tr(lang, "Әкімші", "Админ") : tr(lang, "Сіз", "Вы")}:</span>
            <p>{row.message}</p>
          </div>
        ))}
      </div>
      <form className="chat-send" onSubmit={submitChat}>
        <input value={chatText} onChange={(e) => setChatText(e.target.value)} placeholder={tr(lang, "Хабарлама", "Сообщение")} />
        <button type="submit">{tr(lang, "Жіберу", "Отправить")}</button>
      </form>
    </section>
  );
}

function MyRentalsPanel({ lang }: { lang: Lang }) {
  const [rentals, setRentals] = useState<Rental[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "completed">("all");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getMyRentals({ page: 1, limit: 20 });
      setRentals(response.items);
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Броньдар жүктелмеді", "Не удалось загрузить брони")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const filteredRentals = rentals.filter((row) => {
    if (statusFilter === "all") return true;
    return row.status === statusFilter;
  });

  const onComplete = async (rentalId: number) => {
    setError(null);
    setMessage(null);
    try {
      const response = await completeRental(rentalId);
      setMessage(response.message);
      await load();
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Броньді аяқтау қатесі", "Ошибка завершения брони")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Менің броньдарым", "Мои брони")}</h2>
      <div className="filters-grid rental-filters">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as "all" | "active" | "completed")}
        >
          <option value="all">{tr(lang, "Барлығы", "Все")}</option>
          <option value="active">{tr(lang, "Белсенді", "Активные")}</option>
          <option value="completed">{tr(lang, "Аяқталған", "Завершенные")}</option>
        </select>
      </div>
      {message && <p className="info-banner">{message}</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p className="empty-note">{tr(lang, "Жүктелуде...", "Загрузка...")}</p>}
      {filteredRentals.map((row) => (
        <div key={row.id} className="doc-row rental-row">
          <span>#{row.id}</span>
          <span>{row.start_date} - {row.end_date}</span>
          <span>{formatMoney(row.total_price)}</span>
          <span>{row.status === "active" ? tr(lang, "Белсенді", "Активно") : row.status === "completed" ? tr(lang, "Аяқталды", "Завершено") : tr(lang, "Бас тартылды", "Отменено")}</span>
          <button className="soft" onClick={() => openReceiptAsPdf(row, lang)}>
            {tr(lang, "PDF чек", "PDF чек")}
          </button>
          {row.status === "active" && (
            <button onClick={() => void onComplete(row.id)}>
              {tr(lang, "Аяқтау", "Завершить")}
            </button>
          )}
        </div>
      ))}
      {!filteredRentals.length && <p className="empty-note">{tr(lang, "Фильтрге сай бронь жоқ", "Нет броней по фильтру")}</p>}
    </section>
  );
}
function AuditPanel({ lang }: { lang: Lang }) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [userId, setUserId] = useState("");
  const [action, setAction] = useState("");

  const loadLogs = async () => {
    const result = await getAuditLogs({ page: 1, limit: 20, user_id: userId ? Number(userId) : undefined, action: action || undefined });
    setLogs(result.items);
  };

  useEffect(() => { void loadLogs(); }, []);

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Аудит журналдары", "Журналы аудита")}</h2>
      <div className="filters-grid audit-filters">
        <input placeholder={tr(lang, "Пайдаланушы ID", "ID пользователя")} value={userId} onChange={(e) => setUserId(e.target.value)} />
        <input placeholder={tr(lang, "Әрекет", "Действие")} value={action} onChange={(e) => setAction(e.target.value)} />
        <button onClick={() => void loadLogs()}>{tr(lang, "Қолдану", "Применить")}</button>
      </div>
      {logs.map((log) => (<div key={log.id} className="doc-row support-row"><span>{log.action}</span><span>{log.user_id ?? "-"}</span><span>{new Date(log.created_at).toLocaleString()}</span></div>))}
      {!logs.length && <p className="empty-note">{tr(lang, "Аудит жазбасы табылмады", "Аудит-записи не найдены")}</p>}
    </section>
  );
}

function AdminOverviewPanel({ lang }: { lang: Lang }) {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [timeline, setTimeline] = useState<RentalTimelineItem[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [requests, setRequests] = useState<ClientRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [expenseTitle, setExpenseTitle] = useState("");
  const [expenseCategory, setExpenseCategory] = useState("operations");
  const [expenseAmount, setExpenseAmount] = useState(0);
  const [expenseDate, setExpenseDate] = useState(new Date().toISOString().slice(0, 10));
  const [expenseNote, setExpenseNote] = useState("");
  const [timelineUserId, setTimelineUserId] = useState("");
  const [timelineCarId, setTimelineCarId] = useState("");
  const [timelineStatus, setTimelineStatus] = useState<"all" | "active" | "completed" | "canceled">("all");
  const [requestFilter, setRequestFilter] = useState<"all" | RequestStatus>("all");

  const [requestStatus, setRequestStatus] = useState<Record<number, RequestStatus>>({});
  const [requestComment, setRequestComment] = useState<Record<number, string>>({});
  const [selectedRequestIds, setSelectedRequestIds] = useState<number[]>([]);
  const [bulkStatus, setBulkStatus] = useState<RequestStatus>("in_progress");
  const [bulkComment, setBulkComment] = useState("");
  const topCars = useMemo(() => {
    const grouped = new Map<string, { label: string; count: number; revenue: number }>();
    for (const row of timeline) {
      const key = `${row.car_id}`;
      const current = grouped.get(key) || {
        label: `${row.car_brand} ${row.car_model}`,
        count: 0,
        revenue: 0
      };
      current.count += 1;
      current.revenue += row.total_price;
      grouped.set(key, current);
    }
    return [...grouped.values()].sort((a, b) => b.count - a.count).slice(0, 5);
  }, [timeline]);
  const kpiUtilization = useMemo(() => {
    if (!overview || !overview.total_cars) return 0;
    return Math.round((overview.active_rentals / overview.total_cars) * 100);
  }, [overview]);
  const kpiOpenRequests = useMemo(() => requests.filter((row) => row.status === "open").length, [requests]);
  const kpiResolutionRate = useMemo(() => {
    if (!requests.length) return 0;
    const resolved = requests.filter((row) => row.status === "resolved").length;
    return Math.round((resolved / requests.length) * 100);
  }, [requests]);
  const staleOpenRequests = useMemo(() => {
    const now = Date.now();
    return requests.filter((row) => {
      if (row.status !== "open") return false;
      const created = new Date(row.created_at).getTime();
      return now - created > 3 * 24 * 60 * 60 * 1000;
    }).length;
  }, [requests]);
  const sevenDayTrend = useMemo(() => {
    const result: Array<{ day: string; count: number }> = [];
    const today = new Date();
    const grouped = new Map<string, number>();
    for (const row of timeline) {
      const day = row.start_date;
      grouped.set(day, (grouped.get(day) || 0) + 1);
    }
    for (let i = 6; i >= 0; i -= 1) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      result.push({ day: key.slice(5), count: grouped.get(key) || 0 });
    }
    return result;
  }, [timeline]);
  const trendMax = useMemo(() => Math.max(1, ...sevenDayTrend.map((row) => row.count)), [sevenDayTrend]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, timelineRes, expenseRes, requestRes] = await Promise.all([
        getAdminOverview(),
        getRentalTimeline({
          page: 1,
          limit: 20,
          user_id: timelineUserId ? Number(timelineUserId) : undefined,
          car_id: timelineCarId ? Number(timelineCarId) : undefined,
          status_filter: timelineStatus === "all" ? undefined : timelineStatus
        }),
        getExpenses({ page: 1, limit: 20 }),
        getClientRequests({
          page: 1,
          limit: 20,
          status_filter: requestFilter === "all" ? undefined : requestFilter
        })
      ]);
      setOverview(ov);
      setTimeline(timelineRes.items);
      setExpenses(expenseRes.items);
      setRequests(requestRes.items);
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Админ деректері жүктелмеді", "Не удалось загрузить данные админа")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [timelineUserId, timelineCarId, timelineStatus, requestFilter]);

  const submitExpense = async (event: FormEvent) => {
    event.preventDefault();
    await createExpense({ title: expenseTitle, amount: expenseAmount, category: expenseCategory, expense_date: expenseDate, note: expenseNote || undefined });
    setExpenseTitle("");
    setExpenseAmount(0);
    setExpenseNote("");
    await load();
  };

  const saveRequest = async (id: number) => {
    await updateClientRequest(id, { status: requestStatus[id], admin_comment: requestComment[id] });
    await load();
  };

  const toggleRequestSelection = (id: number) => {
    setSelectedRequestIds((prev) => (prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]));
  };

  const applyBulkUpdate = async () => {
    if (!selectedRequestIds.length) return;
    try {
      await Promise.all(
        selectedRequestIds.map((id) =>
          updateClientRequest(id, {
            status: bulkStatus,
            admin_comment: bulkComment || undefined
          })
        )
      );
      setSelectedRequestIds([]);
      setBulkComment("");
      await load();
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Топтық жаңарту қатесі", "Ошибка группового обновления")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Әкімші аналитикасы", "Аналитика администратора")}</h2>
      {overview && (
        <div className="stats-grid overview-grid">
          <article className="stat-card"><p>{tr(lang, "Жалпы клиент", "Всего клиентов")}</p><strong>{overview.total_users}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Жалпы көлік", "Всего авто")}</p><strong>{overview.total_cars}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Белсенді жалдау", "Активные аренды")}</p><strong>{overview.active_rentals}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Аяқталған жалдау", "Завершенные аренды")}</p><strong>{overview.completed_rentals}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Кіріс", "Доход")}</p><strong>{formatMoney(overview.monthly_revenue)}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Шығыс", "Расход")}</p><strong>{formatMoney(overview.monthly_expenses)}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Пайда / Минус", "Прибыль / Минус")}</p><strong>{formatMoney(overview.monthly_profit)}</strong></article>
          <article className="stat-card"><p>{tr(lang, "Орташа чек", "Средний чек")}</p><strong>{formatMoney(overview.avg_check)}</strong></article>
        </div>
      )}
      <h3>{tr(lang, "KPI Pro", "KPI Pro")}</h3>
      <div className="stats-grid kpi-grid">
        <article className="stat-card">
          <p>{tr(lang, "Автопарк жүктемесі", "Загрузка автопарка")}</p>
          <strong>{kpiUtilization}%</strong>
        </article>
        <article className="stat-card">
          <p>{tr(lang, "Ашық өтініштер", "Открытые обращения")}</p>
          <strong>{kpiOpenRequests}</strong>
        </article>
        <article className="stat-card">
          <p>{tr(lang, "Шешілу деңгейі", "Уровень решения")}</p>
          <strong>{kpiResolutionRate}%</strong>
        </article>
        <article className="stat-card">
          <p>{tr(lang, "Орт. кіріс/көлік", "Ср. доход/авто")}</p>
          <strong>{formatMoney(overview && overview.total_cars ? overview.monthly_revenue / overview.total_cars : 0)}</strong>
        </article>
      </div>

      <h3>{tr(lang, "7 күндік rental тренд", "7-дневный rental тренд")}</h3>
      <div className="trend-chart">
        {sevenDayTrend.map((row) => (
          <div key={row.day} className="trend-item">
            <div
              className="trend-bar"
              style={{ height: `${Math.max(8, Math.round((row.count / trendMax) * 78))}px` }}
              title={`${row.day}: ${row.count}`}
            />
            <span>{row.day}</span>
          </div>
        ))}
      </div>

      <div className="quick-actions">
        <button className="soft" onClick={() => document.getElementById("timeline-section")?.scrollIntoView({ behavior: "smooth" })}>
          {tr(lang, "Жалға алу тарихы", "История аренд")}
        </button>
        <button className="soft" onClick={() => document.getElementById("expenses-section")?.scrollIntoView({ behavior: "smooth" })}>
          {tr(lang, "Шығындар", "Расходы")}
        </button>
        <button className="soft" onClick={() => document.getElementById("requests-section")?.scrollIntoView({ behavior: "smooth" })}>
          {tr(lang, "Клиент өтініштері", "Обращения клиентов")}
        </button>
      </div>

      <h3>{tr(lang, "Top 5 көлік", "Top 5 авто")}</h3>
      <div className="top-cars-grid">
        {topCars.map((row) => (
          <article key={row.label} className="stat-card">
            <p>{row.label}</p>
            <strong>{row.count} {tr(lang, "рет", "раз")}</strong>
            <small>{tr(lang, "Түсім", "Выручка")}: {formatMoney(row.revenue)}</small>
          </article>
        ))}
      </div>
      {!topCars.length && <p className="empty-note">{tr(lang, "Top көлікке дерек жоқ", "Нет данных для топа авто")}</p>}

      {error && <p className="error">{error}</p>}
      {loading && <p className="empty-note">{tr(lang, "Жүктелуде...", "Загрузка...")}</p>}
      <h3 id="timeline-section">{tr(lang, "Кім, қашан, қандай көлік алды", "Кто, когда и какую машину арендовал")}</h3>
      <div className="filters-grid timeline-filters">
        <input
          placeholder={tr(lang, "Клиент ID", "ID клиента")}
          value={timelineUserId}
          onChange={(e) => setTimelineUserId(e.target.value)}
        />
        <input
          placeholder={tr(lang, "Көлік ID", "ID авто")}
          value={timelineCarId}
          onChange={(e) => setTimelineCarId(e.target.value)}
        />
        <select value={timelineStatus} onChange={(e) => setTimelineStatus(e.target.value as "all" | "active" | "completed" | "canceled")}>
          <option value="all">{tr(lang, "Барлық статус", "Все статусы")}</option>
          <option value="active">{tr(lang, "Белсенді", "Активно")}</option>
          <option value="completed">{tr(lang, "Аяқталды", "Завершено")}</option>
          <option value="canceled">{tr(lang, "Бас тартылды", "Отменено")}</option>
        </select>
      </div>
      {timeline.map((row) => (<div key={row.rental_id} className="doc-row timeline-row"><span>{row.user_full_name || row.user_email}</span><span>{row.car_brand} {row.car_model}</span><span>{row.start_date} - {row.end_date}</span><span>{formatMoney(row.total_price)}</span><span>{row.status === "active" ? "Белсенді" : row.status === "completed" ? "Аяқталды" : row.status === "canceled" ? "Бас тартылды" : row.status}</span></div>))}
      {!timeline.length && <p className="empty-note">{tr(lang, "Жалға алу тарихы жоқ", "История аренды пуста")}</p>}

      <h3 id="expenses-section">{tr(lang, "Шығындар", "Расходы")}</h3>
      <form className="admin-form" onSubmit={submitExpense}>
        <input placeholder={tr(lang, "Атауы", "Название")} value={expenseTitle} onChange={(e) => setExpenseTitle(e.target.value)} required />
        <input placeholder={tr(lang, "Санаты", "Категория")} value={expenseCategory} onChange={(e) => setExpenseCategory(e.target.value)} required />
        <input type="number" placeholder={tr(lang, "Сома", "Сумма")} value={expenseAmount} onChange={(e) => setExpenseAmount(Number(e.target.value || 0))} required />
        <input type="date" value={expenseDate} onChange={(e) => setExpenseDate(e.target.value)} required />
        <input placeholder={tr(lang, "Ескерту", "Комментарий")} value={expenseNote} onChange={(e) => setExpenseNote(e.target.value)} />
        <button type="submit">{tr(lang, "Шығын қосу", "Добавить расход")}</button>
      </form>
      {expenses.map((row) => (<div key={row.id} className="doc-row support-row"><span>{row.title}</span><span>{row.category}</span><span>{formatMoney(row.amount)}</span><span>{row.expense_date}</span><span>{row.note || "-"}</span></div>))}
      {!expenses.length && <p className="empty-note">{tr(lang, "Шығын жазбалары жоқ", "Записей расходов нет")}</p>}

      <h3 id="requests-section">{tr(lang, "Клиент өтініштері", "Обращения клиентов")}</h3>
      {staleOpenRequests > 0 && (
        <p className="warning-banner">
          {tr(lang, "Назар аударыңыз", "Внимание")}: {staleOpenRequests} {tr(lang, "ашық өтініш 3 күннен асты", "открытых обращений старше 3 дней")}
        </p>
      )}
      <div className="filters-grid request-filters">
        <select value={requestFilter} onChange={(e) => setRequestFilter(e.target.value as "all" | RequestStatus)}>
          <option value="all">{tr(lang, "Барлығы", "Все")}</option>
          <option value="open">{tr(lang, "Жаңа", "Новый")}</option>
          <option value="in_progress">{tr(lang, "Өңделуде", "В работе")}</option>
          <option value="resolved">{tr(lang, "Шешілді", "Решено")}</option>
          <option value="rejected">{tr(lang, "Қабылданбады", "Отклонено")}</option>
        </select>
      </div>
      <div className="request-bulk">
        <span>{tr(lang, "Таңдалды", "Выбрано")}: {selectedRequestIds.length}</span>
        <select value={bulkStatus} onChange={(e) => setBulkStatus(e.target.value as RequestStatus)}>
          <option value="open">{tr(lang, "Жаңа", "Новый")}</option>
          <option value="in_progress">{tr(lang, "Өңделуде", "В работе")}</option>
          <option value="resolved">{tr(lang, "Шешілді", "Решено")}</option>
          <option value="rejected">{tr(lang, "Қабылданбады", "Отклонено")}</option>
        </select>
        <input
          placeholder={tr(lang, "Топтық комментарий", "Групповой комментарий")}
          value={bulkComment}
          onChange={(e) => setBulkComment(e.target.value)}
        />
        <button onClick={() => void applyBulkUpdate()} disabled={!selectedRequestIds.length}>
          {tr(lang, "Таңдалғандарға қолдану", "Применить к выбранным")}
        </button>
        <button
          className="soft"
          onClick={() =>
            downloadCsv(
              "client_requests.csv",
              ["id", "user_id", "subject", "status", "created_at", "admin_comment"],
              requests.map((row) => [row.id, row.user_id, row.subject, row.status, row.created_at, row.admin_comment])
            )
          }
        >
          {tr(lang, "CSV экспорт", "Экспорт CSV")}
        </button>
      </div>
      {requests.map((row) => (
        <div key={row.id} className="request-card">
          <div className="request-head">
            <input
              type="checkbox"
              checked={selectedRequestIds.includes(row.id)}
              onChange={() => toggleRequestSelection(row.id)}
            />
            <p><b>{row.user_full_name || row.user_email}</b> - {row.subject}</p>
          </div>
          <p>{row.message}</p>
          <div className="request-controls">
            <select value={requestStatus[row.id] ?? row.status} onChange={(e) => setRequestStatus((prev) => ({ ...prev, [row.id]: e.target.value as RequestStatus }))}>
              <option value="open">{tr(lang, "Жаңа", "Новый")}</option><option value="in_progress">{tr(lang, "Өңделуде", "В работе")}</option><option value="resolved">{tr(lang, "Шешілді", "Решено")}</option><option value="rejected">{tr(lang, "Қабылданбады", "Отклонено")}</option>
            </select>
            <input value={requestComment[row.id] ?? row.admin_comment ?? ""} onChange={(e) => setRequestComment((prev) => ({ ...prev, [row.id]: e.target.value }))} placeholder={tr(lang, "Әкімші пікірі", "Комментарий админа")} />
            <button onClick={() => void saveRequest(row.id)}>{tr(lang, "Сақтау", "Сохранить")}</button>
          </div>
        </div>
      ))}
      {!requests.length && <p className="empty-note">{tr(lang, "Клиент өтініштері жоқ", "Нет обращений клиентов")}</p>}
    </section>
  );
}

function AdminTourRequestsPanel({ lang }: { lang: Lang }) {
  const [requests, setRequests] = useState<TourRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      setRequests(await listTourRequests());
    } catch (err) {
      setError(
        apiErrorMessage(
          err,
          tr(lang, "Firestore сұраныстары жүктелмеді", "Заявки Firestore не загрузились")
        )
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRequests();
  }, []);

  return (
    <section className="panel section-panel">
      <div className="section-head">
        <div>
          <h2>{tr(lang, "Tour сұраныстары", "Tour заявки")}</h2>
          <p className="panel-subtitle">
            {tr(
              lang,
              "Firestore ішіндегі tour package сұраныстары.",
              "Заявки на tour package из Firestore."
            )}
          </p>
        </div>
        <button className="soft" onClick={() => void loadRequests()}>
          {tr(lang, "Жаңарту", "Обновить")}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {loading && <p className="empty-note">{tr(lang, "Жүктелуде...", "Загрузка...")}</p>}
      {!loading && !requests.length && (
        <p className="empty-note">{tr(lang, "Сұраныс жоқ", "Заявок пока нет")}</p>
      )}
      {requests.map((row) => (
        <article key={row.id} className="request-card">
          <div className="doc-row">
            <strong>{row.packageTitle}</strong>
            <span>{formatMoney(row.price)}</span>
          </div>
          <p>{row.route}</p>
          <div className="pill-row">
            <span className="pill">{row.days} {tr(lang, "күн", "дня")}</span>
            <span className="pill">{row.status}</span>
            <span className="pill">{row.source}</span>
          </div>
          <p>{tr(lang, "Клиент", "Клиент")}: {row.userFullName || row.userEmail}</p>
          <p>Email: {row.userEmail}</p>
          {row.userPhone && <p>{tr(lang, "Телефон", "Телефон")}: {row.userPhone}</p>}
          <p>
            {tr(lang, "Жасалған уақыты", "Создано")}:{" "}
            {row.createdAt ? new Date(row.createdAt).toLocaleString() : "-"}
          </p>
        </article>
      ))}
    </section>
  );
}

function AdminUsersPanel({ me, lang }: { me: User; lang: Lang }) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAdminUsers();
      setUsers(result);
    } catch {
      setError(tr(lang, "Пайдаланушылар жүктелмеді", "Не удалось загрузить пользователей"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadUsers(); }, []);

  const visibleUsers = users.filter((user) => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return true;
    return (
      user.email.toLowerCase().includes(keyword) ||
      (user.full_name || "").toLowerCase().includes(keyword) ||
      String(user.id).includes(keyword)
    );
  });

  const onTransfer = async (userId: number) => {
    setMessage(null);
    setError(null);
    try {
      const response = await transferAdminRole(userId);
      setMessage(response.message);
      await loadUsers();
    } catch {
      setError(tr(lang, "Әкімші рөлін беру сәтсіз", "Не удалось передать роль администратора"));
    }
  };

  const toggleBlacklist = async (user: User) => {
    setMessage(null);
    setError(null);
    try {
      const nextState = !user.is_blacklisted;
      await updateUserBlacklist(user.id, {
        is_blacklisted: nextState,
        reason: nextState ? "Blocked by admin panel" : "Unblocked by admin panel"
      });
      await loadUsers();
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Blacklist жаңарту қатесі", "Ошибка обновления blacklist")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Пайдаланушыларды басқару", "Управление пользователями")}</h2>
      <div className="filters-grid users-filters">
        <input
          placeholder={tr(lang, "ID / email / аты бойынша іздеу", "Поиск по ID / email / имени")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button
          className="soft"
          onClick={() =>
            downloadCsv(
              "users.csv",
              ["id", "full_name", "email", "role", "is_verified", "created_at"],
              visibleUsers.map((u) => [u.id, u.full_name, u.email, u.role, u.is_verified ? "1" : "0", u.created_at])
            )
          }
        >
          {tr(lang, "CSV экспорт", "Экспорт CSV")}
        </button>
      </div>
      {message && <p className="info-banner">{message}</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p className="empty-note">{tr(lang, "Жүктелуде...", "Загрузка...")}</p>}
      {visibleUsers.map((user) => (
        <article key={user.id} className="request-card user-card">
          <p><b>#{user.id}</b> {user.full_name || "-"}</p>
          <p>{user.email}</p>
          <div className="pill-row">
            <span className="pill">{user.role === "admin" ? tr(lang, "Әкімші", "Администратор") : tr(lang, "Клиент", "Клиент")}</span>
            <span className={`pill ${user.is_verified ? "status-available" : "status-rented"}`}>
              {user.is_verified ? tr(lang, "Расталған", "Подтвержден") : tr(lang, "Расталмаған", "Не подтвержден")}
            </span>
            <span className={`pill ${user.is_blacklisted ? "status-rented" : "status-available"}`}>
              {user.is_blacklisted ? tr(lang, "Blacklist", "Blacklist") : tr(lang, "Белсенді", "Активен")}
            </span>
          </div>
          {user.id !== me.id && user.role !== "admin" && user.is_verified && (
            <button onClick={() => void onTransfer(user.id)}>
              {tr(lang, "Осы қолданушыға admin рөлін беру", "Передать admin роль этому пользователю")}
            </button>
          )}
          {user.id !== me.id && (
            <button className="soft" onClick={() => void toggleBlacklist(user)}>
              {user.is_blacklisted ? tr(lang, "Blacklist-тен шығару", "Снять blacklist") : tr(lang, "Blacklist-ке қосу", "Добавить в blacklist")}
            </button>
          )}
        </article>
      ))}
      {!visibleUsers.length && <p className="empty-note">{tr(lang, "Пайдаланушы табылмады", "Пользователи не найдены")}</p>}
    </section>
  );
}

function AdminRentalsPanel({ lang }: { lang: Lang }) {
  const [rentals, setRentals] = useState<Rental[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "completed" | "canceled">("all");

  const loadRentals = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getAllRentals({ page: 1, limit: 50, sort_order: "desc" });
      setRentals(response.items);
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Бронь тізімі жүктелмеді", "Не удалось загрузить список броней")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadRentals(); }, []);

  const filtered = rentals.filter((row) => (statusFilter === "all" ? true : row.status === statusFilter));

  const onComplete = async (rentalId: number) => {
    setError(null);
    setMessage(null);
    try {
      const response = await completeRental(rentalId);
      setMessage(response.message);
      await loadRentals();
    } catch (error) {
      setError(apiErrorMessage(error, tr(lang, "Броньді аяқтау қатесі", "Ошибка завершения брони")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Броньдарды басқару", "Управление бронированиями")}</h2>
      <div className="filters-grid rental-filters">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as "all" | "active" | "completed" | "canceled")}
        >
          <option value="all">{tr(lang, "Барлығы", "Все")}</option>
          <option value="active">{tr(lang, "Белсенді", "Активные")}</option>
          <option value="completed">{tr(lang, "Аяқталған", "Завершенные")}</option>
          <option value="canceled">{tr(lang, "Бас тартылған", "Отмененные")}</option>
        </select>
        <button
          className="soft"
          onClick={() =>
            downloadCsv(
              "rentals.csv",
              ["id", "user_id", "car_id", "start_date", "end_date", "total_price", "status"],
              filtered.map((r) => [r.id, r.user_id, r.car_id, r.start_date, r.end_date, r.total_price, r.status])
            )
          }
        >
          {tr(lang, "CSV экспорт", "Экспорт CSV")}
        </button>
      </div>
      {message && <p className="info-banner">{message}</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p className="empty-note">{tr(lang, "Жүктелуде...", "Загрузка...")}</p>}
      {filtered.map((row) => (
        <div key={row.id} className="doc-row rental-row admin-rental-row">
          <span>#{row.id}</span>
          <span>{tr(lang, "Клиент ID", "ID клиента")}: {row.user_id}</span>
          <span>{tr(lang, "Көлік ID", "ID авто")}: {row.car_id}</span>
          <span>{row.start_date} - {row.end_date}</span>
          <span>{formatMoney(row.total_price)}</span>
          <span>{row.status}</span>
          {row.status === "active" && (
            <button onClick={() => void onComplete(row.id)}>
              {tr(lang, "Аяқтау", "Завершить")}
            </button>
          )}
        </div>
      ))}
      {!filtered.length && <p className="empty-note">{tr(lang, "Бронь табылмады", "Брони не найдены")}</p>}
    </section>
  );
}

function AdminChatPanel({ lang }: { lang: Lang }) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadUsers = async () => {
    try {
      const rows = await getAdminChatUsers();
      setUsers(rows);
      if (!selectedUserId && rows.length) setSelectedUserId(rows[0].id);
    } catch (err) {
      setError(apiErrorMessage(err, tr(lang, "Чат қолданушылары жүктелмеді", "Пользователи чата не загрузились")));
    }
  };

  const loadMessages = async (userId: number) => {
    try {
      const rows = await getAdminUserChat(userId);
      setMessages(rows);
    } catch (err) {
      setError(apiErrorMessage(err, tr(lang, "Чат жүктелмеді", "Чат не загрузился")));
    }
  };

  useEffect(() => { void loadUsers(); }, []);
  useEffect(() => {
    if (selectedUserId) void loadMessages(selectedUserId);
  }, [selectedUserId]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedUserId || !text.trim()) return;
    try {
      await sendChatMessage({ user_id: selectedUserId, message: text.trim() });
      setText("");
      await loadMessages(selectedUserId);
      await loadUsers();
    } catch (err) {
      setError(apiErrorMessage(err, tr(lang, "Хабарлама жіберу қатесі", "Ошибка отправки сообщения")));
    }
  };

  return (
    <section className="panel section-panel">
      <h2>{tr(lang, "Клиент чаттары", "Чаты клиентов")}</h2>
      {error && <p className="error">{error}</p>}
      <div className="filters-grid users-filters">
        <select value={selectedUserId ?? ""} onChange={(e) => setSelectedUserId(Number(e.target.value) || null)}>
          <option value="">{tr(lang, "Клиент таңдаңыз", "Выберите клиента")}</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              #{u.id} {u.full_name || u.email}
            </option>
          ))}
        </select>
      </div>
      <div className="chat-box">
        {messages.map((row) => (
          <div key={row.id} className={`chat-row ${row.sender_role === "admin" ? "chat-admin" : "chat-user"}`}>
            <span>{row.sender_role === "admin" ? tr(lang, "Әкімші", "Админ") : tr(lang, "Клиент", "Клиент")}:</span>
            <p>{row.message}</p>
          </div>
        ))}
      </div>
      {selectedUserId && (
        <form className="chat-send" onSubmit={submit}>
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder={tr(lang, "Хабарлама", "Сообщение")} />
          <button type="submit">{tr(lang, "Жіберу", "Отправить")}</button>
        </form>
      )}
    </section>
  );
}

function Header({ user, onLogout, lang, setLang }: { user: User | null; onLogout: () => void; lang: Lang; setLang: (v: Lang) => void }) {
  const roleLabel = user?.role === "admin" ? tr(lang, "Әкімші", "Администратор") : tr(lang, "Клиент", "Клиент");
  return (
    <header className="hero">
      <div className="hero-overlay" />
      <div className="hero-content">
        <div>
          <h1>AutoRent Pro</h1>
          <p>{tr(lang, "Автокөлікті жалға беру және басқару жүйесі", "Система аренды и управления автомобилями")}</p>
        </div>
        <div className="hero-controls">
          <div className="lang-switch">
            <button className={lang === "kz" ? "active" : ""} onClick={() => setLang("kz")}>KZ</button>
            <button className={lang === "ru" ? "active" : ""} onClick={() => setLang("ru")}>RU</button>
          </div>
          {user && (
            <div className="user-chip">
              <span>{user.email}</span>
              <b>{roleLabel}</b>
              {user.role === "user" && (
                <small>{tr(lang, "Бонус ұпайы", "Бонусные баллы")}: {user.loyalty_points || 0}</small>
              )}
            </div>
          )}
          {user && <button onClick={onLogout}>{tr(lang, "Шығу", "Выйти")}</button>}
        </div>
      </div>
    </header>
  );
}

function AdminWorkspace({ me, lang }: { me: User; lang: Lang }) {
  const [view, setView] = useState<AdminView>("ops");
  return (
    <>
      <div className="workspace-switch">
        <button className={view === "ops" ? "active" : ""} onClick={() => setView("ops")}>{tr(lang, "Аналитика", "Аналитика")}</button>
        <button className={view === "fleet" ? "active" : ""} onClick={() => setView("fleet")}>{tr(lang, "Автопарк", "Автопарк")}</button>
        <button className={view === "rentals" ? "active" : ""} onClick={() => setView("rentals")}>{tr(lang, "Броньдар", "Брони")}</button>
        <button className={view === "tourRequests" ? "active" : ""} onClick={() => setView("tourRequests")}>{tr(lang, "Tour заявки", "Tour заявки")}</button>
        <button className={view === "chat" ? "active" : ""} onClick={() => setView("chat")}>{tr(lang, "Чат", "Чат")}</button>
        <button className={view === "audit" ? "active" : ""} onClick={() => setView("audit")}>{tr(lang, "Аудит", "Аудит")}</button>
        <button className={view === "users" ? "active" : ""} onClick={() => setView("users")}>{tr(lang, "Қолданушылар", "Пользователи")}</button>
      </div>
      {view === "ops" && <AdminOverviewPanel lang={lang} />}
      {view === "fleet" && <CarsGrid adminMode lang={lang} />}
      {view === "rentals" && <AdminRentalsPanel lang={lang} />}
      {view === "tourRequests" && <AdminTourRequestsPanel lang={lang} />}
      {view === "chat" && <AdminChatPanel lang={lang} />}
      {view === "audit" && <AuditPanel lang={lang} />}
      {view === "users" && <AdminUsersPanel me={me} lang={lang} />}
    </>
  );
}

function ClientWorkspace({ lang, user }: { lang: Lang; user: User }) {
  const [view, setView] = useState<ClientView>("fleet");
  return (
    <>
      <div className="workspace-switch">
        <button className={view === "fleet" ? "active" : ""} onClick={() => setView("fleet")}>{tr(lang, "Автопарк", "Автопарк")}</button>
        <button className={view === "tours" ? "active" : ""} onClick={() => setView("tours")}>{tr(lang, "Тур пакеттер", "Тур-пакеты")}</button>
        <button className={view === "rentals" ? "active" : ""} onClick={() => setView("rentals")}>{tr(lang, "Менің броньдарым", "Мои брони")}</button>
        <button className={view === "docs" ? "active" : ""} onClick={() => setView("docs")}>{tr(lang, "Құжаттар", "Документы")}</button>
        <button className={view === "support" ? "active" : ""} onClick={() => setView("support")}>{tr(lang, "Қолдау", "Поддержка")}</button>
      </div>
      {view === "fleet" && <CarsGrid adminMode={false} lang={lang} onBooked={() => setView("rentals")} />}
      {view === "tours" && <TourPackagesPanel lang={lang} user={user} />}
      {view === "rentals" && <MyRentalsPanel lang={lang} />}
      {view === "docs" && <DocumentsPanel lang={lang} />}
      {view === "support" && <ClientRequestsPanel lang={lang} />}
    </>
  );
}
export default function App() {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [lang, setLang] = useState<Lang>(() => (localStorage.getItem(LANG_KEY) as Lang) || "kz");
  const [me, setMe] = useState<User | null>(null);
  const [loadingMe, setLoadingMe] = useState(false);

  useEffect(() => {
    localStorage.setItem(LANG_KEY, lang);
  }, [lang]);

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  useEffect(() => {
    const resolveMe = async () => {
      if (!token) {
        setMe(null);
        return;
      }
      setLoadingMe(true);
      try {
        const user = await getMe();
        setMe(user);
        navigate(user.role === "admin" ? "/admin" : "/client", { replace: true });
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setMe(null);
      } finally {
        setLoadingMe(false);
      }
    };
    void resolveMe();
  }, [token, navigate]);

  const onLogin = async (email: string, password: string) => {
    const result = await login(email, password);
    localStorage.setItem(TOKEN_KEY, result.access_token);
    setToken(result.access_token);
  };

  const onLogout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setMe(null);
    navigate("/", { replace: true });
  };

  return (
    <div className="page">
      <Header user={me} onLogout={onLogout} lang={lang} setLang={setLang} />
      {loadingMe ? (
        <section className="panel section-panel"><p>{tr(lang, "Профиль жүктелуде...", "Профиль загружается...")}</p></section>
      ) : (
        <Routes>
          <Route path="/" element={me ? <Navigate to={me.role === "admin" ? "/admin" : "/client"} replace /> : <LoginView onLogin={onLogin} lang={lang} />} />
          <Route path="/client" element={me?.role === "user" ? <ClientWorkspace lang={lang} user={me} /> : <Navigate to="/" replace />} />
          <Route path="/admin" element={me?.role === "admin" ? <AdminWorkspace me={me} lang={lang} /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </div>
  );
}
