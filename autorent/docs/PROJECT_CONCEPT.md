# AutoRent - Автосалонда автомобильдерді жалға беруді есепке алу жүйесі

## Жобаның мақсаты

Автосалонда автомобильдерді жалға беру процесін толық автоматтандыратын web-жүйе жасау:

- Клиент автокөлікті онлайн таңдайды
- Жалдау мерзімін белгілейді
- Әкімші көліктерді, клиенттерді және жалға беру тарихын басқарады
- Жүйе табысты, қолжетімді көліктерді және статистиканы есептейді

## Негізгі пайдаланушылар

### Клиент (`User`)

- Тіркелу / Кіру / Шығу
- Автокөліктер тізімін көру
- Іздеу және сүзгілеу
- Көлікті жалға алу
- Өз жалдау тарихын көру

### Әкімші (`Admin`)

- Автокөлік қосу / өзгерту / өшіру
- Бағаларды орнату
- Клиенттерді көру
- Жалдау тапсырыстарын бекіту
- Кіріс пен статистиканы көру
- Админ-панель

## Ұсынылатын технологиялар

### Frontend

- React
- React Router
- Axios
- Tailwind CSS немесе MUI
- Адаптивті дизайн (mobile + desktop)

### Backend

- Node.js + Express
- RESTful API
- JWT Authentication

### Database

- PostgreSQL
- ORM: Prisma немесе Sequelize

### DevOps

- Docker + docker-compose
- GitHub Actions (CI/CD)
- Render / Heroku / AWS
- Prometheus + Grafana
- k6 (load testing)

## Архитектура

```text
[ React Frontend ]
        |
        | REST API
        |
[ Node.js Backend ]
        |
[ PostgreSQL Database ]
```

## Дерекқор құрылымы (негізгі)

### User

- `id`
- `full_name`
- `email`
- `password_hash`
- `role` (`USER` / `ADMIN`)

### Car

- `id`
- `brand`
- `model`
- `year`
- `price_per_day`
- `status` (`available` / `rented` / `service`)
- `image_url`

### Rental

- `id`
- `user_id`
- `car_id`
- `start_date`
- `end_date`
- `total_price`
- `status` (`active` / `finished` / `canceled`)

### Payment (қосымша)

- `id`
- `rental_id`
- `amount`
- `payment_date`
- `payment_method`

## Қауіпсіздік

- Құпиясөздерді `bcrypt` арқылы хэштеу
- JWT токендер
- Input sanitization
- SQL Injection / XSS / CSRF қорғанысы
- Role-based access control

## Функционал талаптарға сәйкестік

| Талап | AutoRent-та іске асуы |
|---|---|
| Аутентификация | JWT login/register |
| Рөлдер | User / Admin |
| CRUD | Cars, Rentals |
| REST API | `/api/auth`, `/api/cars`, `/api/rentals` |
| Іздеу | `brand`, `model` |
| Сүзгілеу | `price`, `status` |
| Сұрыптау | `price`, `year` |
| Пагинация | `page`, `limit` |
| Логирование | Winston |
| Тестілеу | Jest + Supertest |
| Docker | backend + db |
| CI/CD | GitHub Actions |
| Мониторинг | Prometheus |
| Load test | k6 |
