import { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { getLatestSurvey, type SurveySubmitResult } from '../api/client'
import styles from './Results.module.css'

const MEDALS = ['🥇', '🥈', '🥉']

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as SurveySubmitResult | null
  const [data, setData] = useState<SurveySubmitResult | null>(state)
  const [loading, setLoading] = useState(!state)

  useEffect(() => {
    if (state) {
      setData(state)
      setLoading(false)
      return
    }
    async function load() {
      try {
        const result = await getLatestSurvey()
        setData(result)
      } catch {
        setData(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [state])

  if (loading) {
    return <div className={styles.wrap}><div className={styles.loading}>Загрузка результатов…</div></div>
  }

  if (!data) {
    return (
      <div className={styles.wrap}>
        <p className={styles.empty}>Пока нет результатов. Пройдите опрос.</p>
        <Link to="/survey" className={styles.link}>Перейти к опросу →</Link>
      </div>
    )
  }

  const { message, universities_top } = data

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>Рекомендованные вузы</h1>
      {message && <p className={styles.message}>{message}</p>}

      <ul className={styles.list}>
        {universities_top.map((item, idx) => {
          const scorePct = Math.round(item.score * 100)
          const rank = idx + 1
          return (
            <li key={item.university.id} className={styles.card} data-rank={rank <= 3 ? rank : undefined}>
              <div className={styles.cardContent}>
                <div className={styles.photoWrap}>
                  <img
                    src={item.university.photo_url || `https://picsum.photos/seed/${item.university.id}/140/105`}
                    alt={item.university.name}
                    className={styles.photo}
                  />
                </div>
                <div className={styles.uniInfo}>
                  <div className={styles.uniHeader}>
                    {idx < 3 && <span className={styles.medal}>{MEDALS[idx]}</span>}
                    <h2 className={styles.uniName}>{item.university.name}</h2>
                  </div>

                  {/* Score bar */}
                  <div className={styles.scoreWrap}>
                    <div className={styles.scoreLabel}>
                      <span>Совпадение с профилем</span>
                      <span className={styles.scoreValue}>{scorePct}%</span>
                    </div>
                    <div className={styles.scoreBar}>
                      <div
                        className={styles.scoreBarFill}
                        style={{ width: `${scorePct}%` }}
                      />
                    </div>
                  </div>

                  <p className={styles.programsMeta}>
                    {item.programs_count} {item.programs_count === 1 ? 'программа' : item.programs_count < 5 ? 'программы' : 'программ'}
                  </p>

                  <div className={styles.programs}>
                    {item.programs.map((pr) => (
                      <Link
                        key={pr.program.id}
                        to={`/universities/${item.university.id}/programs/${pr.program.id}`}
                        className={styles.programCard}
                      >
                        <span className={styles.programName}>{pr.program.name}</span>
                        <span className={styles.programScore}>{Math.round(pr.score * 100)}%</span>
                      </Link>
                    ))}
                  </div>

                  <button
                    type="button"
                    className={styles.chatButton}
                    onClick={() => navigate('/chat', { state: { universityId: item.university.id, universityName: item.university.name } })}
                  >
                    💬 Чат с ИИ
                  </button>
                </div>
              </div>
            </li>
          )
        })}
      </ul>

      <div className={styles.actions}>
        <button type="button" onClick={() => navigate('/survey')} className={styles.button}>
          ← Пройти опрос заново
        </button>
      </div>
    </div>
  )
}