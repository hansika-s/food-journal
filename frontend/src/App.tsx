import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AccountBar } from './components/AccountBar'
import { Logo } from './components/Logo'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { SignupPage } from './pages/SignupPage'

// "/" is the home page, "/login" is the login page. Any other address goes home.
// The header sits above every page: the logo on the left, the account on the right.
function App() {
  return (
    <BrowserRouter>
      <header className="mb-6 flex items-start justify-between gap-4">
        <Logo />
        <AccountBar />
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
