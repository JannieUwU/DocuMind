# Frontend - Vue3 RAG Application

Modern web interface for the RAG hybrid search application.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at http://localhost:5173

### Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📦 Dependencies

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Build tool
- **Element Plus** - UI component library
- **Tailwind CSS** - CSS framework
- **Pinia** - State management
- **Axios** - HTTP client
- **Vue Router** - Official router

## 🔧 Configuration

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── assets/        # Static assets
│   ├── components/    # Vue components
│   ├── composables/   # Composition API hooks
│   ├── router/        # Route configuration
│   ├── stores/        # Pinia stores
│   ├── utils/         # Utility functions
│   ├── views/         # Page components
│   ├── App.vue        # Root component
│   └── main.js        # Entry point
├── public/            # Public static files
└── package.json       # Dependencies
```

## 🧪 Testing

```bash
npm run test
```

## 📝 Code Style

```bash
# Run linter
npm run lint

# Format code
npm run format
```

## 🌐 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

---

**Part of Vue3 RAG Hybrid Search Application**
