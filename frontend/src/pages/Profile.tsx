import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Profile.module.css'

export default function Profile() {
  const { logout } = useAuth()

  return (
    <div className={styles.wrap}>
      {/* Hero */}
      <div className={styles.hero}>
        <div className={styles.avatar}>🎓</div>
        <h1 className={styles.title}>Профиль</h1>
        <p className={styles.subtitle}>Управляйте своим аккаунтом и результатами</p>
      </div>

      {/* Quick links */}
      <div className={styles.card}>
        <p className={styles.cardTitle}>Быстрый доступ</p>
        <div className={styles.links}>
          <Link to="/survey" className={styles.navCard}>
            <span className={styles.navIcon}>📝</span>
            <span className={styles.navLabel}>Пройти / изменить опрос</span>
            <span className={styles.navArrow}>→</span>
          </Link>
          <Link to="/results" className={styles.navCard}>
            <span className={styles.navIcon}>🎯</span>
            <span className={styles.navLabel}>Мои рекомендации</span>
            <span className={styles.navArrow}>→</span>
          </Link>
          <Link to="/chat" className={styles.navCard}>
            <span className={styles.navIcon}>💬</span>
            <span className={styles.navLabel}>История чатов с ИИ</span>
            <span className={styles.navArrow}>→</span>
          </Link>
        </div>
      </div>

      {/* Account */}
      <div className={styles.card}>
        <p className={styles.cardTitle}>Аккаунт</p>
        <div className={styles.links}>
          <button
            type="button"
            onClick={logout}
            className={styles.navCard}
            style={{ textAlign: 'left', fontFamily: 'inherit' }}
          >
            <span className={styles.navIcon}>🚪</span>
            <span className={styles.navLabel}>Выйти из аккаунта</span>
          </button>
        </div>
      </div>
    </div>
  )
}
