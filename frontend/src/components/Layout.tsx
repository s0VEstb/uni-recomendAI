import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import ConfirmDialog from './ConfirmDialog'
import styles from './Layout.module.css'

export default function Layout() {
  const { isAuthenticated, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const [logoutOpen, setLogoutOpen] = useState(false)

  // Helper: проверяем активный маршрут
  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/')

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo}>
          <span className={styles.logoIcon}>🎓</span>
          uni recomendAI
        </Link>
        <nav className={styles.nav}>
          <button
            type="button"
            onClick={toggleTheme}
            className={styles.themeToggle}
            title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            aria-label={theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          {isAuthenticated ? (
            <>
              <Link
                to="/survey"
                className={`${styles.navLink} ${isActive('/survey') ? styles.navLinkActive : ''}`}
              >
                Опрос
              </Link>
              <Link
                to="/results"
                className={`${styles.navLink} ${isActive('/results') ? styles.navLinkActive : ''}`}
              >
                Результаты
              </Link>
              <Link
                to="/chat"
                className={`${styles.navLink} ${isActive('/chat') ? styles.navLinkActive : ''}`}
              >
                ИИ-чат
              </Link>
              <Link
                to="/profile"
                className={`${styles.navLink} ${isActive('/profile') ? styles.navLinkActive : ''}`}
              >
                Профиль
              </Link>
              <button type="button" onClick={() => setLogoutOpen(true)} className={styles.logout}>
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className={`${styles.navLink} ${isActive('/login') ? styles.navLinkActive : ''}`}
              >
                Вход
              </Link>
              <Link to="/register" className={styles.registerBtn}>
                Регистрация
              </Link>
            </>
          )}
        </nav>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>

      {/* ── Диалог выхода из аккаунта ── */}
      <ConfirmDialog
        isOpen={logoutOpen}
        title="Выйти из аккаунта?"
        message="Вы будете перенаправлены на страницу входа."
        confirmLabel="Выйти"
        cancelLabel="Остаться"
        onConfirm={() => { setLogoutOpen(false); logout() }}
        onCancel={() => setLogoutOpen(false)}
      />
    </div>
  )
}
