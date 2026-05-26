# 🏡 Real Estate Website — Full Stack Platform

A full-stack real estate brokerage platform with AI-powered voice search, a conversational chatbot assistant, property listings, cart, favorites, orders, and an admin dashboard.

---

## 📸 Project Screenshots

> Place your screenshots in a `/docs/screenshots/` folder and update the paths below.

| Home Page | Property Listings | Property Details |
|:---------:|:-----------------:|:----------------:|
| ![Home](docs/screenshots/home.png) | ![Listings](docs/screenshots/listings.png) | ![Details](docs/screenshots/details.png) |

| AI Chat Assistant | Voice Search | Admin Dashboard |
|:-----------------:|:------------:|:---------------:|
| ![Chat](docs/screenshots/chat.png) | ![Voice](docs/screenshots/voice.png) | ![Admin](docs/screenshots/admin.png) |

---

## 🗂️ Project Structure

```
real-estate-website/
│
├── frontend/                  # Angular 21 — Client Application
│   └── src/app/
│       ├── component/         # All UI components
│       ├── services/          # HTTP & business logic services
│       ├── models/            # TypeScript interfaces & models
│       ├── guards/            # Route guards (admin)
│       └── app.routes.ts      # Application routing
│
├── backend/                   # .NET 8 C# — Web API
│   ├── WebApiShop/            # Main API project (controllers, middleware)
│   ├── Services/              # Business logic layer
│   ├── Repository/            # Data access layer (EF Core)
│   ├── Entities/              # Database entity models
│   ├── DTOs/                  # Data Transfer Objects
│   ├── AI_SERVICE/            # C# AI service class library
│   └── TestProject/           # Integration & unit tests
│
└── ai_service/                # Python — FastAPI AI Microservice
    ├── chat_service.py        # Chat + Voice Search endpoints
    └── .env                   # API keys (not committed)
```

---

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (Angular 21)                     │
│                                                                 │
│   ┌──────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│   │  Property    │   │   AI Chatbot    │   │ Voice Search  │  │
│   │  Listings    │   │   (Maggie 🏡)   │   │  🎤 Button    │  │
│   └──────┬───────┘   └────────┬────────┘   └───────┬───────┘  │
│          │                    │                     │           │
│          │         Web Speech API (he-IL)           │           │
└──────────┼────────────────────┼─────────────────────┼───────────┘
           │                    │                     │
           │         HTTP (localhost:44305)            │
           ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   .NET 8 Web API (C#)                           │
│                                                                 │
│   ProductController   ChatController   VoiceSearchController    │
│   UsersController     OrderController  POST /api/search/voice   │
│                                                                 │
│              Entity Framework Core → SQL Server                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    HTTP (localhost:8001)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Python FastAPI AI Microservice                   │
│                                                                 │
│    POST /chat              POST /parse-search                   │
│    (Maggie chatbot)        (Voice search extractor)             │
│                                                                 │
│              OpenAI GPT-4o / GPT-4o-mini                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🏠 Property Management
- Browse properties with filters: city, price range, rooms, beds, transaction type
- Property detail pages with image gallery
- Add / Edit / Delete listings (authenticated owners)
- Featured properties on the home page

### 🔍 Voice Search *(New Feature)*
- Click the 🎤 microphone button and speak your search in **Hebrew or English**
- Browser converts speech to text using the native **Web Speech API**
- Text is sent to the .NET API → forwarded to the Python AI service
- **GPT-4o-mini** extracts structured filters: city, rooms, max price, balcony, parking
- Results are filtered and returned instantly

### 🤖 AI Chat Assistant (Maggie 🏡)
- Conversational assistant powered by **GPT-4o**
- Knows the full property catalog in real time
- Responds in the same language the user writes in (Hebrew / English)
- Provides clickable property links, owner contact info, and smart recommendations

### 🛒 Cart & Orders
- Add properties to cart, proceed to checkout
- Full order history for users and admins

### ❤️ Favorites
- Save and manage favorite properties

### 👤 User Accounts
- Register / Login
- Profile management
- Password change with strength validation (zxcvbn)

### 🔐 Admin Dashboard
- Manage all properties, users, orders, and inquiries
- Protected by `adminGuard` route guard + server-side middleware

### 📧 Email Notifications
- Automated emails via MailKit / Gmail SMTP on inquiry and order events

---

## 🎤 Voice Search — Deep Dive

### How It Works

```
User speaks Hebrew:
"אני מחפש דירה ב-4 חדרים עם חניה בתל אביב עד 2.5 מיליון"
         │
         ▼
  webkitSpeechRecognition (he-IL)
  converts speech → text string
         │
         ▼
  Angular VoiceSearchService
  POST https://localhost:44305/api/search/voice
  { "transcript": "אני מחפש דירה..." }
         │
         ▼
  .NET VoiceSearchController
  forwards to Python ai_service
  POST http://localhost:8001/parse-search
         │
         ▼
  Python FastAPI + GPT-4o-mini
  extracts structured JSON:
  {
    "city":        "Tel Aviv",
    "rooms":       4,
    "max_price":   2500000,
    "has_balcony": null,
    "has_parking": true
  }
         │
         ▼
  .NET LINQ filter on Properties table
         │
         ▼
  { filters: {...}, results: [...] }
  returned to Angular → displayed to user
```

### Extracted JSON Structure

```json
{
  "city":        "Tel Aviv",
  "rooms":       4,
  "max_price":   2500000,
  "has_balcony": null,
  "has_parking": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `city` | `string \| null` | City name in English |
| `rooms` | `integer \| null` | Number of rooms |
| `max_price` | `number \| null` | Maximum price in ILS |
| `has_balcony` | `boolean \| null` | `true` = wanted, `false` = excluded, `null` = not mentioned |
| `has_parking` | `boolean \| null` | `true` = wanted, `false` = excluded, `null` = not mentioned |

### Files Added / Modified

| File | Change |
|------|--------|
| `frontend/src/app/services/voice-search.service.ts` | New — Web Speech API + HTTP service |
| `frontend/src/app/component/voice-search/voice-search.component.ts` | New — Mic button component |
| `backend/WebApiShop/Controllers/VoiceSearchController.cs` | New — `POST /api/search/voice` |
| `backend/WebApiShop/Program.cs` | Added named `HttpClient` for ai_service |
| `backend/WebApiShop/appsettings.json` | Added `AiService:BaseUrl` |
| `ai_service/chat_service.py` | Added `POST /parse-search` endpoint |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Angular | 21 | SPA Framework |
| PrimeNG | 21 | UI Component Library |
| PrimeFlex | 4 | CSS Utility Layout |
| RxJS | 7.8 | Reactive programming |
| TypeScript | 5.9 | Type safety |
| Web Speech API | Native | Voice-to-text |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| .NET | 8.0 | Web API framework |
| Entity Framework Core | 8 | ORM / SQL Server |
| AutoMapper | 12 | DTO mapping |
| NLog | 6 | Structured logging |
| MailKit | 4 | Email sending |
| zxcvbn-core | 7 | Password strength |

### AI Service
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | latest | API framework |
| OpenAI SDK | latest | GPT-4o / GPT-4o-mini |
| python-dotenv | latest | Environment config |

### Database
| Technology | Purpose |
|------------|---------|
| SQL Server | Primary database |
| EF Core Power Tools | Schema scaffolding |

---

## 🚀 Getting Started

### Prerequisites

- Node.js 20+ and npm 11+
- .NET 8 SDK
- Python 3.11+
- SQL Server (local or remote)
- OpenAI API Key

---

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd real-estate-website
```

---

### 2. AI Service Setup (Python)

```bash
cd ai_service
pip install fastapi uvicorn openai python-dotenv
```

Create the `.env` file:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
STORE_NAME=Your Store Name
STORE_DESCRIPTION=Your store description here.
```

Start the service:

```bash
uvicorn chat_service:app --port 8001 --reload
```

> The AI service will be available at `http://localhost:8001`
> Swagger docs at `http://localhost:8001/docs`

---

### 3. Backend Setup (.NET)

Update `backend/WebApiShop/appsettings.json` with your SQL Server connection:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=YOUR_SERVER; Database=RealEstateDB_; Trusted_Connection=True; TrustServerCertificate=True;"
  },
  "AiService": {
    "BaseUrl": "http://localhost:8001"
  },
  "EmailSettings": {
    "SmtpServer": "smtp.gmail.com",
    "SmtpPort": "587",
    "SenderEmail": "your-email@gmail.com",
    "SenderPassword": "your-app-password",
    "RecipientEmail": "your-email@gmail.com"
  }
}
```

Run the API:

```bash
cd backend/WebApiShop
dotnet restore
dotnet run
```

> API available at `https://localhost:44305`
> Swagger UI at `https://localhost:44305/swagger`

---

### 4. Frontend Setup (Angular)

```bash
cd frontend
npm install
ng serve
```

> App available at `http://localhost:4200`

---

### 5. Run All Three Services

Open three terminals:

```bash
# Terminal 1 — Python AI Service
cd ai_service && uvicorn chat_service:app --port 8001 --reload

# Terminal 2 — .NET Backend
cd backend/WebApiShop && dotnet run

# Terminal 3 — Angular Frontend
cd frontend && ng serve
```

---

## 📡 API Endpoints

### Properties
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/product` | Get all properties (with filters) |
| `GET` | `/api/product/:id` | Get property by ID |
| `POST` | `/api/product` | Create new property |
| `PUT` | `/api/product/:id` | Update property |
| `DELETE` | `/api/product/:id` | Delete property |
| `GET` | `/api/product/search` | Text search |
| `GET` | `/api/product/featured` | Featured listings |

### Voice Search *(New)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search/voice` | Parse Hebrew voice transcript → filtered results |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to Maggie AI assistant |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/register` | Register new user |
| `POST` | `/api/users/login` | Login |
| `GET` | `/api/users/:id` | Get user profile |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/order` | Create order |
| `GET` | `/api/order/user/:id` | Get user orders |

### Python AI Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Maggie chatbot |
| `POST` | `/parse-search` | Voice search parameter extraction |

---

## 🗄️ Database Schema

```
Users ──────────────────────────────────────────────┐
  UserId, FullName, Email, Password, Phone,          │
  Address, IsAdmin                                   │
                                                     │
Products ───────────────────────────────────────────►┤ OwnerId FK
  ProductId, Title, Description, Price, City,        │
  Rooms, Beds, ImageUrl, CategoryId, OwnerId,        │
  IsAvailable, TransactionType, CreatedDate          │
       │                                             │
       ├──► ProductImages                            │
       │      ImageId, ProductId, AdditionalImageUrl │
       │                                             │
       ├──► OrderItems ──► Orders ──────────────────►┤ UserId FK
       │      OrderItemId, OrderId, ProductId,       │
       │      PriceAtPurchase, StartDate, EndDate    │
       │                                             │
       └──► PropertyInquiries ────────────────────► Users
              InquiryId, ProductId, UserId, OwnerId,
              Name, Phone, Email, Status, CreatedAt

Categories
  CategoryId, CategoryName, Description

AdminInquiries ─────────────────────────────────────► Users
  InquiryId, UserId, Name, Email, Phone,
  Subject, Message, Status, CreatedAt

Ratings (HTTP request log)
  RatingId, Method, Path, Host, UserAgent,
  Referer, RecordDate
```

---

## 🔒 Security

- Admin routes protected by `adminGuard` (Angular) + `AdminAuthorizationMiddleware` (.NET)
- Passwords hashed with bcrypt-style validation via `zxcvbn-core`
- CORS configured to allow only `http://localhost:4200`
- `.env` file is git-ignored — never commit API keys
- Email credentials should use Gmail App Passwords, not your main password

---

## 🧪 Running Tests

```bash
# .NET tests
cd backend
dotnet test

# Angular tests
cd frontend
ng test
```

Test projects cover:
- `CategoriesUnitTest` / `CategoriesIntegrationTest`
- `ProductUnitTest` / `ProductIntegrationTest`
- `OrdersUnitTest` / `OrderIntegrationTest`
- `UserUnitTest` / `UserIntegrationTest`

---

## 📁 Angular Routes

| Path | Component | Protected |
|------|-----------|-----------|
| `/` | HomeComponent | No |
| `/products` | ProductListComponent | No |
| `/product-details/:id` | ProductDetailsComponent | No |
| `/auth` | AuthComponent | No |
| `/cart` | CartComponent | No |
| `/favorites` | FavoritesComponent | No |
| `/checkout` | CheckoutComponent | No |
| `/profile` | UserProfileComponent | No |
| `/add-product` | AddProductComponent | No |
| `/edit-product/:id` | EditProductComponent | No |
| `/ai-guide` | AiGuideComponent | No |
| `/blog` | BlogComponent | No |
| `/contact` | ContactComponent | No |
| `/admin` | AdminDashboardComponent | ✅ Admin only |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feat/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is for educational and portfolio purposes.
