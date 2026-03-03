import { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { getLatestSurvey, type SurveySubmitResult } from '../api/client'
import styles from './Results.module.css'

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as SurveySubmitResult | null
  const [data, setData] = useState<SurveySubmitResult | null>(state)
  const [loading, setLoading] = useState(!state)
  const [selectedPrograms, setSelectedPrograms] = useState<number[]>([])

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

  const toggleProgram = (programId: number) => {
    setSelectedPrograms(prev =>
      prev.includes(programId)
        ? prev.filter(id => id !== programId)
        : prev.length < 5 ? [...prev, programId] : prev
    )
  }

  const reasonIcon = (code: string): string => {
    const icons: Record<string, string> = {
      budget_ok: '💰',
      budget_too_low: '⚠️',
      fee_unknown: '❓',
      tag_match: '🎯',
      ort_ok: '✅',
      ort_unknown_or_not_required: '📋',
      city_match: '📍',
    }
    return icons[code] ?? '•'
  }

  if (loading) {
    return <div className={styles.wrap}><p className={styles.loading}>Загрузка…</p></div>
  }

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

      {selectedPrograms.length >= 2 && (
        <div className={styles.compareBar}>
          <span>Выбрано программ: {selectedPrograms.length}</span>
          <button
            className={styles.compareBtn}
            onClick={() => navigate('/compare', { state: { programIds: selectedPrograms } })}
          >
            Сравнить выбранные
          </button>
        </div>
      )}

      <ul className={styles.list}>
        {universities_top.map((item) => (
          <li key={item.university.id} className={styles.card}>
            <div className={styles.cardContent}>
              <div className={styles.photoWrap}>
                <img
                  src={item.university.photo_url || `https://picsum.photos/seed/${item.university.id}/160/120`}
                  alt={item.university.name}
                  className={styles.photo}
                />
              </div>
              <div className={styles.uniInfo}>
                <h2 className={styles.uniName}>{item.university.name}</h2>
                <p className={styles.meta}>
                  Совпадение: {Math.round(item.score * 100)}% · программ: {item.programs_count}
                </p>
                <div className={styles.programs}>
                  {item.programs.map((pr) => (
                    <div key={pr.program.id} className={styles.programRow}>
                      <div className={styles.programTop}>
                        <input
                          type="checkbox"
                          id={`prog-${pr.program.id}`}
                          checked={selectedPrograms.includes(pr.program.id)}
                          onChange={() => toggleProgram(pr.program.id)}
                          className={styles.programCheck}
                          title="Добавить к сравнению"
                        />
                        <Link
                          to={`/universities/${item.university.id}/programs/${pr.program.id}`}
                          className={styles.programCard}
                        >
                          <span className={styles.programName}>{pr.program.name}</span>
                          <span className={styles.programScore}>{Math.round(pr.score * 100)}%</span>
                        </Link>
                      </div>
                      {pr.reasons && pr.reasons.length > 0 && (
                        <ul className={styles.reasons}>
                          {pr.reasons.map((r) => (
                            <li key={r.code} className={styles.reason}>
                              <span className={styles.reasonIcon}>{reasonIcon(r.code)}</span>
                              <span className={styles.reasonMsg}>{r.message}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  className={styles.chatButton}
                  onClick={() => navigate('/chat', { state: { universityId: item.university.id, universityName: item.university.name } })}
                >
                  Начать чат с ИИ
                </button>
              </div>
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