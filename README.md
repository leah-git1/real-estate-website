# 🏡 Real Estate Website — Full Stack Platform

A full-stack real estate brokerage platform with AI-powered voice search, a conversational chatbot assistant, **AI property valuation with image analysis**, property listings, cart, favorites, orders, and an admin dashboard.

---

## 📸 Project Screenshots

> Place your screenshots in a `/docs/screenshots/` folder and update the paths below.

| Home Page | Property Listings | Property Details |
|:---------:|:-----------------:|:----------------:|
| ![Home](/assets/home.png) | ![Listings](/assets/products.png) | ![Details](/assets/dashboard.png) |

| AI Smart Agent | Property Valuation (AI) | Add Product |
|:--------------:|:-----------------------:|:-----------:|
| ![Chat](/assets/chat.png) | ![Valuation](/assets/value.png) | ![Add](/assets/add.png) |

---

## 🗂️ Project Structure

```
real-estate-website/
│
├── frontend/                  # Angular 21 — Client Application
│   └── src/app/
│       ├── component/         # All UI components
│       │   ├── ai-guide-component/       # Smart Agent guide page
│       │   ├── valuation-component/      # AI property valuation wizard
│       │   ├── valuation-btn/            # Persistent side-tab shortcut
│       │   ├── chat/                     # GPT-4o chat (floating)
│       │   ├── chatbot-component/        # Simple rule-based chatbot
│       │   ├── voice-search/             # Mic button + Web Speech API
│       │   ├── home-component/
│       │   ├── product-list-component/
│       │   ├── product-details-component/
│       │   ├── add-product-component/
│       │   ├── edit-product-component/
│       │   ├── auth/
│       │   ├── cart-component/
│       │   ├── cart-sidebar/
│       │   ├── checkout-component/
│       │   ├── favorites-component/
│       │   ├── favorites-sidebar/
│       │   ├── user-profile-component/
│       │   ├── admin-dashboard-component/
│       │   ├── contact-component/
│       │   ├── blog-component/
│       │   └── order-success-component/
│       ├── services/          # HTTP & business logic services
│       │   ├── valuation.service.ts      # Valuation API calls
│       │   ├── voice-search.service.ts   # Voice search API calls
│       │   ├── chat_service.ts           # GPT-4o chat API calls
│       │   ├── chat-state.service.ts     # Chat open/prefill state
│       │   ├── product-service.ts
│       │   ├── user-service.ts
│       │   ├── order-service.ts
│       │   ├── cart-service.ts
│       │   ├── favorites-service.ts
│       │   └── ...
│       ├── models/            # TypeScript interfaces & models
│       ├── guards/            # Route guards (admin)
│       └── app.routes.ts      # Application routing
│
├── backend/                   # .NET 8 C# — Web API
│   ├── WebApiShop/            # Main API project
│   │   └── Controllers/
│   │       ├── ProductController.cs
│   │       ├── ChatController.cs
│   │       ├── VoiceSearchController.cs
│   │       ├── ValuationController.cs    # Property valuation proxy
│   │       ├── UsersController.cs
│   │       ├── OrderController.cs
│   │       └── ...
│   ├── Services/              # Business logic layer
│   ├── Repository/            # Data access layer (EF Core)
│   ├── Entities/              # Database entity models
│   ├── DTOs/                  # Data Transfer Objects
│   ├── AI_SERVICE/            # C# AI service class library
│   └── TestProject/           # Integration & unit tests
│
└── ai_service/                # Python — FastAPI AI Microservice
    ├── chat_service.py        # All AI endpoints (chat, voice, valuation)
    ├── test_chat_service.py   # Pytest test suite
    ├── requirements.txt       # Python dependencies
    └── .env                   # API keys (not committed)
```

---

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BROWSER (Angular 21)                           │
│                                                                         │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Property    │  │  Smart Agent    │  │  Voice   │  │ Valuation  │  │
│  │  Listings    │  │  Chat 🤖        │  │  Search  │  │ Wizard 🏠  │  │
│  └──────┬───────┘  └────────┬────────┘  └────┬─────┘  └─────┬──────┘  │
│         │                   │                │               │         │
│         │          Web Speech API (he-IL)    │               │         │
└─────────┼───────────────────┼────────────────┼───────────────┼─────────┘
          │                   │                │               │
          │         HTTP (localhost:44305)                      │
          ▼                   ▼                ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       .NET 8 Web API (C#)                               │
│                                                                         │
│  ProductController  ChatController  VoiceSearchController               │
│  UsersController    OrderController ValuationController                 │
│                                                                         │
│               Entity Framework Core → SQL Server                       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                     HTTP (localhost:8001)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Python FastAPI AI Microservice                         │
│                                                                         │
│   POST /chat              POST /parse-search                            │
│   (Smart Agent)           (Voice search extractor)                      │
│                                                                         │
│   POST /analyze-property-multipart                                      │
│   (Property valuation — GPT-4o Vision + image upload)                  │
│                                                                         │
│               OpenAI GPT-4o / GPT-4o-mini                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🏠 Property Management
- Browse properties with filters: city, price range, rooms, beds, transaction type
- Property detail pages with image gallery
- Add / Edit / Delete listings (authenticated owners)
- Featured properties on the home page

### 🔍 Voice Search
- Click the 🎤 microphone button and speak your search in **Hebrew or English**
- Browser converts speech to text using the native **Web Speech API**
- Text is sent to the .NET API → forwarded to the Python AI service
- **GPT-4o-mini** extracts structured filters: city, rooms, max price, balcony, parking
- Results are filtered and returned instantly

### 🤖 Smart Agent (AI Chat)
- Conversational assistant powered by **GPT-4o**
- Knows the full property catalog in real time
- Responds in the same language the user writes in (Hebrew / English)
- Provides clickable property links, owner contact info, and smart recommendations
- Voice input supported directly inside the chat

### 🏠 AI Property Valuation *(Feature)*
- 3-step wizard: property details → image upload → results
- **Live camera capture** — open the camera, record a clip or take snapshots; frames are extracted in real time and displayed as thumbnails immediately
- **File upload** — drag & drop or select JPEG/PNG images
- **GPT-4o Vision** analyzes images and returns:
  - Estimated market value in ILS
  - Price range (min / max)
  - Confidence level (0–1)
  - Room-by-room breakdown: kitchen, lighting, renovations, flooring
  - Overall impression
- Guest users see a blurred teaser; registered users get the full report
- A persistent ✨ side tab on the right edge of the screen provides quick access

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

### 📢 Ad Popup
- A periodic promotional popup appears every ~25 seconds (then every 90 s) advertising the Smart Agent and Valuation pages

---

## 🏠 AI Property Valuation — Deep Dive

### How It Works

```
User opens Valuation page (/valuation)
         │
         ▼
  Step 1 — Fill property details
  (address, city, rooms, sqm)
         │
         ▼
  Step 2 — Add images (optional)
  ┌────────────────────────────────────────┐
  │  Option A: Live Camera                  │
  │  → Click "פתח מצלמה"                   │
  │  → Press "הקלט" — frames captured      │
  │    every 2 s from live video feed      │
  │    and shown as thumbnails instantly   │
  │  → Press "עצור" to finish              │
  │  Option B: Drag & Drop / File Picker   │
  │  → Select up to 4 JPEG / PNG files     │
  └────────────────────────────────────────┘
         │
         ▼
  Angular ValuationService
  POST https://localhost:44305/api/valuation/analyze
  multipart/form-data: { address, city, rooms, sqm, images[] }
         │
         ▼
  .NET ValuationController
  forwards to Python ai_service
  POST http://localhost:8001/analyze-property-multipart
         │
         ▼
  Python FastAPI + GPT-4o Vision
  returns structured JSON:
  {
    "valuation":   3500000,
    "confidence":  0.82,
    "price_range": { "min": 3220000, "max": 3780000 },
    "details": {
      "kitchen":     "...",
      "lighting":    "...",
      "renovations": "...",
      "flooring":    "...",
      "overall":     "..."
    }
  }
         │
         ▼
  Step 3 — Results displayed
  (guest: blurred teaser | registered: full report)
```

### Valuation Response Structure

| Field | Type | Description |
|-------|------|-------------|
| `valuation` | `number` | Estimated market value in ILS |
| `confidence` | `number` (0–1) | Model confidence in the estimate |
| `price_range.min` | `number` | Lower bound (valuation × 0.92) |
| `price_range.max` | `number` | Upper bound (valuation × 1.08) |
| `details.kitchen` | `string` | Kitchen quality assessment |
| `details.lighting` | `string` | Lighting quality |
| `details.renovations` | `string` | Renovation level |
| `details.flooring` | `string` | Flooring type and condition |
| `details.overall` | `string` | One-sentence overall impression |

### Files Added / Modified

| File | Change |
|------|--------|
| `frontend/src/app/component/valuation-component/` | New — 3-step wizard UI |
| `frontend/src/app/component/valuation-btn/` | New — persistent side tab |
| `frontend/src/app/services/valuation.service.ts` | New — HTTP calls to backend |
| `backend/WebApiShop/Controllers/ValuationController.cs` | New — proxy to Python |
| `ai_service/chat_service.py` | Added `/analyze-property` and `/analyze-property-multipart` endpoints |

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
| FastAPI | ≥0.111 | API framework |
| OpenAI SDK | ≥1.30 | GPT-4o / GPT-4o-mini / Vision |
| python-dotenv | latest | Environment config |
| python-multipart | ≥0.0.9 | File upload support |
| pytest | ≥8.2 | Test runner |
| httpx | ≥0.27 | TestClient transport |

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
pip install -r requirements.txt
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

### Voice Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search/voice` | Parse Hebrew voice transcript → filtered results |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to Smart Agent AI |

### Property Valuation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/valuation/analyze` | Upload images + property data → AI valuation report |

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
| `POST` | `/chat` | Smart Agent chatbot |
| `POST` | `/parse-search` | Voice search parameter extraction |
| `POST` | `/analyze-property` | Valuation via base64 images (JSON) |
| `POST` | `/analyze-property-multipart` | Valuation via file upload (multipart) |

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
- Valuation images are processed in memory only — never persisted to disk

---

## 🧪 Running Tests

```bash
# .NET tests
cd backend
dotnet test

# Angular tests
cd frontend
ng test

# Python AI service tests
cd ai_service
pytest test_chat_service.py -v
```

### Python Test Coverage

| Test Class | Endpoint | Cases |
|------------|----------|-------|
| `TestChat` | `POST /chat` | Basic reply, product catalog injection, history, empty message |
| `TestParseSearch` | `POST /parse-search` | Full params, partial params, all-null, empty/whitespace 400, invalid JSON 500, parking excluded |
| `TestAnalyzeProperty` | `POST /analyze-property` | No images, base64 image, cap at 4, missing fields 400, invalid JSON 500 |
| `TestAnalyzePropertyMultipart` | `POST /analyze-property-multipart` | No images, JPEG upload, cap at 4, unsupported type 400, missing fields 422, invalid JSON 500 |

### .NET Test Coverage

| Test Class | Description |
|------------|-------------|
| `CategoriesUnitTest` | Category service unit tests |
| `CategoriesIntegrationTest` | Category API integration tests |
| `ProductUnitTest` | Product service unit tests |
| `ProductIntegrationTest` | Product API integration tests |
| `OrdersUnitTest` | Order service unit tests |
| `OrderIntegrationTest` | Order API integration tests |
| `UserUnitTest` | User service unit tests |
| `UserIntegrationTest` | User API integration tests |

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
| `/valuation` | ValuationComponent | No |
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
