import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Landing.module.css'

export default function Landing() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const handleStart = () => {
    if (isAuthenticated) {
      navigate('/survey')
    } else {
      navigate('/register')
    }
  }

  return (
    <section className={styles.hero}>
      <div className={styles.heroContent}>
        <span className={styles.eyebrow}>Университетский навигатор с ИИ</span>
        <h1 className={styles.title}>
          Не можете определиться с <span className={styles.highlight}>университетом</span>?
        </h1>
        <p className={styles.subtitle}>
          Uni Recomend анализирует ваши интересы, сильные стороны и бюджет, чтобы за несколько минут
          предложить программы и университеты, которые действительно вам подходят.
        </p>
        <div className={styles.actions}>
          <button type="button" onClick={handleStart} className={styles.primaryBtn}>
            Начать подбор
          </button>
          <Link to="/chat">
            <button type="button" className={styles.secondaryBtn}>
              Задать вопрос ИИ-боту
            </button>
          </Link>
        </div>
        <div className={styles.heroMeta}>
          <div className={styles.metaItem}>
            <strong>1-2 минуты</strong>
            чтобы пройти опрос и получить результаты
          </div>
          <div className={styles.metaItem}>
            <strong>Прозрачные критерии</strong>
            объясняем, почему советуем именно эти программы
          </div>
          <div className={styles.metaItem}>
            <strong>Бесплатно</strong>
            сервис доступен без скрытых платежей
          </div>
        </div>
      </div>

      <aside className={styles.card}>
        <h2 className={styles.cardTitle}>Как это работает</h2>
        <ul className={styles.steps}>
          <li>
            <span className={styles.stepBadge}>1</span>
            Отвечаете на вопросы об интересах, планах и возможностях.
          </li>
          <li>
            <span className={styles.stepBadge}>2</span>
            Алгоритм сопоставляет ваши ответы с программами университетов.
          </li>
          <li>
            <span className={styles.stepBadge}>3</span>
            Получаете список подходящих направлений с пояснениями и ссылками.
          </li>
        </ul>
        <p className={styles.tagline}>
          Уже есть аккаунт? <Link to="/login">Войдите</Link>, чтобы продолжить с последнего результата.
        </p>
        <div className={styles.trusted}>
          <span className={styles.pill}>Подходит выпускникам 9–11 классов</span>
          <span className={styles.pill}>Фокус на университетах Кыргызстана</span>
        </div>
      </aside>
    </section>
  )
}

