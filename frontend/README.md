# MedMatch AI Frontend

A React-based frontend for MedMatch AI - an AI-powered clinical trial matching platform for cancer patients.

## 🚀 Tech Stack

- **React 18+** with TypeScript
- **Vite** for blazing fast development
- **TailwindCSS** for styling
- **React Router v6** for navigation
- **TanStack Query** for API state management
- **Supabase** for authentication and database
- **React Hook Form + Zod** for form validation
- **Lucide React** for icons

## 📋 Prerequisites

- Node.js 18+ and npm
- Supabase account and project
- Backend API running on port 8000

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

### 3. Set Up Supabase Tables

Run these SQL commands in your Supabase SQL Editor:

```sql
-- User Profiles Table
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('patient', 'caregiver', 'healthcare_provider')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search History Table
CREATE TABLE search_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  patient_data JSONB NOT NULL,
  search_results JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Saved Trials Table
CREATE TABLE saved_trials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  trial_id TEXT NOT NULL,
  trial_data JSONB NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, trial_id)
);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_trials ENABLE ROW LEVEL SECURITY;

-- Policies for user_profiles
CREATE POLICY "Users can view own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON user_profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Policies for search_history
CREATE POLICY "Users can view own history" ON search_history
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own history" ON search_history
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policies for saved_trials
CREATE POLICY "Users can view own saved trials" ON saved_trials
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own saved trials" ON saved_trials
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved trials" ON saved_trials
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can update own saved trials" ON saved_trials
  FOR UPDATE USING (auth.uid() = user_id);
```

### 4. Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## 🏗️ Project Structure

```
frontend/src/
├── components/
│   ├── auth/           # Authentication components
│   ├── forms/          # Patient input forms
│   ├── trials/         # Trial display components
│   ├── layout/         # Header, Footer
│   └── ui/             # Reusable UI components
├── pages/              # Route pages
├── services/           # API and Supabase services
├── hooks/              # Custom React hooks
├── types/              # TypeScript types
└── utils/              # Utility functions
```

## 🔑 Key Features

### Authentication
- Email/password signup and login
- Google OAuth integration
- Password reset functionality
- Protected routes

### Trial Matching
- **Natural Language Input**: Describe patient condition in plain English
- **Structured Form**: Detailed medical form for precise matching
- AI-powered trial matching with match scores
- Location-based distance calculation

### Trial Management
- Save trials for later review
- Add notes to saved trials
- View search history
- Sort and filter results

### UI/UX
- Fully responsive design
- WCAG 2.1 AA accessibility compliant
- Gentle loading states
- Clear error messages
- Medical term tooltips

## 🎨 Design System

### Colors
- **Primary Blue**: `#4A90E2` - Main CTA and interactive elements
- **Primary Teal**: `#3AAFA9` - Secondary accents
- **Secondary Green**: `#88D498` - Success states and high match scores
- **Gray Scale**: Custom gray palette for text and borders

### Typography
- Font Family: Inter, Source Sans Pro, system-ui

## 📱 Pages

1. **Landing** (`/`) - Marketing page with features and CTA
2. **Login** (`/login`) - User authentication
3. **Signup** (`/signup`) - New user registration
4. **Dashboard** (`/dashboard`) - User home with quick actions
5. **Trial Search** (`/search`) - Input patient data to find trials
6. **Results** (`/results`) - Display matching trials
7. **Saved Trials** (`/saved`) - View bookmarked trials

## 🔐 Security Notes

- All sensitive data stored in Supabase with Row Level Security
- Environment variables for API keys
- HTTPS required in production
- Authentication tokens handled securely
- CORS configured on backend

## 🚢 Build for Production

```bash
npm run build
```

Output will be in the `dist/` folder.

## 🧪 Testing

```bash
# Run linting
npm run lint

# Type checking
npm run type-check
```

## 📝 Environment Setup Checklist

- [ ] Node.js 18+ installed
- [ ] Supabase project created
- [ ] Environment variables configured
- [ ] Supabase tables created with RLS policies
- [ ] Backend API running
- [ ] Dependencies installed
- [ ] Development server running

## 🆘 Troubleshooting

### Common Issues

**Issue**: Supabase connection error
- Check environment variables are correct
- Verify Supabase URL and anon key

**Issue**: API connection failed
- Ensure backend is running on port 8000
- Check CORS configuration

**Issue**: Build errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`

## 📄 License

This project is part of MedMatch AI - a healthcare application for clinical trial matching.

---

Built with ❤️ for cancer patients and their families
