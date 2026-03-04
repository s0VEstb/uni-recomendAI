import { Outlet, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import styles from './Layout.module.css'

export default function Layout() {
  const { isAuthenticated, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo}>uni recomendAI</Link>
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
              <Link to="/profile" className={styles.navLink}>Профиль</Link>
              <Link to="/survey" className={styles.navLink}>Опрос</Link>
              <Link to="/results" className={styles.navLink}>Результаты</Link>
              <Link to="/chat" className={styles.navLink}>Чат</Link>
              <button type="button" onClick={logout} className={styles.logout}>
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={styles.navLink}>Вход</Link>
              <Link to="/register" className={styles.navLink}>Регистрация</Link>
            </>
          )}
        </nav>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
