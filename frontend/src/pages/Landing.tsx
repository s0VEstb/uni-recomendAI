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
    <div className={styles.landing}>
      {/* ═══════════ ANIMATED BACKGROUND ═══════════ */}
      <div className={styles.meshBg} aria-hidden="true">
        <div className={styles.orb1} />
        <div className={styles.orb2} />
        <div className={styles.orb3} />
      </div>

      {/* ═══════════ HERO ═══════════ */}
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <span className={styles.eyebrow}>
            <span className={styles.eyebrowDot} />
            Университетский навигатор с ИИ
          </span>

          <h1 className={styles.title}>
            Не можете определиться{' '}
            <br className={styles.brDesktop} />с{' '}
            <span className={styles.highlight}>университетом</span>?
          </h1>

          <p className={styles.subtitle}>
            Uni&nbsp;Recomend анализирует ваши интересы, сильные стороны и&nbsp;бюджет,
            чтобы за&nbsp;несколько минут предложить программы и&nbsp;университеты,
            которые действительно вам подходят.
          </p>

          <div className={styles.actions}>
            <button type="button" onClick={handleStart} className={styles.primaryBtn}>
              Начать подбор
              <span className={styles.btnArrow}>→</span>
            </button>
            <Link to="/chat" className={styles.secondaryBtn}>
              Задать вопрос ИИ&#8209;боту
            </Link>
          </div>

          <div className={styles.heroMeta}>
            <div className={styles.metaCard}>
              <span className={styles.metaIcon}>⚡</span>
              <div>
                <strong>1–2 минуты</strong>
                <span>чтобы пройти опрос</span>
              </div>
            </div>
            <div className={styles.metaCard}>
              <span className={styles.metaIcon}>🔍</span>
              <div>
                <strong>Прозрачные критерии</strong>
                <span>объясняем, почему советуем</span>
              </div>
            </div>
            <div className={styles.metaCard}>
              <span className={styles.metaIcon}>💎</span>
              <div>
                <strong>Бесплатно</strong>
                <span>без скрытых платежей</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════ HOW IT WORKS ═══════════ */}
      <section className={styles.howSection}>
        <h2 className={styles.sectionTitle}>Как это работает</h2>
        <p className={styles.sectionSubtitle}>Три простых шага до списка подходящих программ</p>

        <div className={styles.stepsRow}>
          <div className={styles.stepCard}>
            <span className={styles.stepBadge}>1</span>
            <span className={styles.stepIcon}>📝</span>
            <h3 className={styles.stepTitle}>Расскажите о себе</h3>
            <p className={styles.stepDesc}>
              Отвечаете на вопросы об интересах, планах и возможностях.
            </p>
          </div>

          <div className={styles.stepConnector} aria-hidden="true">
            <span />
          </div>

          <div className={styles.stepCard}>
            <span className={styles.stepBadge}>2</span>
            <span className={styles.stepIcon}>⚙️</span>
            <h3 className={styles.stepTitle}>Алгоритм подбирает</h3>
            <p className={styles.stepDesc}>
              Сопоставляем ваши ответы с программами университетов.
            </p>
          </div>

          <div className={styles.stepConnector} aria-hidden="true">
            <span />
          </div>

          <div className={styles.stepCard}>
            <span className={styles.stepBadge}>3</span>
            <span className={styles.stepIcon}>🎓</span>
            <h3 className={styles.stepTitle}>Получите результат</h3>
            <p className={styles.stepDesc}>
              Список подходящих направлений с пояснениями и ссылками.
            </p>
          </div>
        </div>
      </section>

      {/* ═══════════ TRUST / SOCIAL PROOF ═══════════ */}
      <section className={styles.trustSection}>
        <div className={styles.trustGrid}>
          <div className={styles.trustStat}>
            <span className={styles.trustNumber}>10+</span>
            <span className={styles.trustLabel}>университетов</span>
          </div>
          <div className={styles.trustStat}>
            <span className={styles.trustNumber}>40+</span>
            <span className={styles.trustLabel}>программ в базе</span>
          </div>
          <div className={styles.trustStat}>
            <span className={styles.trustNumber}>7</span>
            <span className={styles.trustLabel}>критериев оценки</span>
          </div>
        </div>

        <div className={styles.pillRow}>
          <span className={styles.pill}>🎒 Подходит выпускникам 9–11 классов</span>
          <span className={styles.pill}>🇰🇬 Фокус на университетах Кыргызстана</span>
          <span className={styles.pill}>🤖 ИИ‑чат для вопросов</span>
          <span className={styles.pill}>📊 Сравнение программ</span>
        </div>
      </section>

      {/* ═══════════ FINAL CTA ═══════════ */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaCard}>
          <h2 className={styles.ctaTitle}>Готовы найти свой университет?</h2>
          <p className={styles.ctaSubtitle}>
            Опрос займёт пару минут — и вы получите персональные рекомендации с объяснениями.
          </p>
          <button type="button" onClick={handleStart} className={styles.ctaBtn}>
            Начать подбор →
          </button>
          <p className={styles.ctaLogin}>
            Уже есть аккаунт?{' '}
            <Link to="/login">Войдите</Link>, чтобы продолжить с последнего результата.
          </p>
        </div>
      </section>

      {/* ═══════════ FOOTER ═══════════ */}
      <footer className={styles.footer}>
        <span className={styles.footerBrand}>uni&nbsp;recomendAI</span>
        <span className={styles.footerCopy}>© 2026</span>
        <Link to="/chat" className={styles.footerLink}>ИИ‑бот</Link>
      </footer>
    </div>
  )
}
