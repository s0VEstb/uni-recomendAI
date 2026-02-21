import { useLocation, useNavigate, Link } from 'react-router-dom'
import type { SurveySubmitResult } from '../api/client'
import { RESULTS_KEY } from './Survey'
import styles from './Results.module.css'

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as SurveySubmitResult | null
  const stored = (() => {
    try {
      const raw = localStorage.getItem(RESULTS_KEY)
      return raw ? (JSON.parse(raw) as SurveySubmitResult) : null
    } catch {
      return null
    }
  })()

  const data = state ?? stored

  if (!data) {
    return (
      <div className={styles.wrap}>
        <p className={styles.empty}>Пока нет результатов. Пройдите опрос.</p>
        <Link to="/survey" className={styles.link}>Перейти к опросу</Link>
      </div>
    )
  }

  const { message, universities_top } = data

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>Рекомендованные вузы</h1>
      {message && <p className={styles.message}>{message}</p>}

      <ul className={styles.list}>
        {universities_top.map((item) => (
          <li key={item.university.id} className={styles.card}>
            <h2 className={styles.uniName}>{item.university.name}</h2>
            <p className={styles.meta}>
              Совпадение: {Math.round(item.score * 100)}% · программ: {item.programs_count}
            </p>
            <div className={styles.programs}>
              {item.programs.map((pr) => (
                <div key={pr.program.id} className={styles.programCard}>
                  <span className={styles.programName}>{pr.program.name}</span>
                  <span className={styles.programScore}>{Math.round(pr.score * 100)}%</span>
                </div>
              ))}
            </div>
          </li>
        ))}
      </ul>

      <div className={styles.actions}>
        <button type="button" onClick={() => navigate('/survey')} className={styles.button}>
          Пройти опрос заново
        </button>
      </div>
    </div>
  )
}