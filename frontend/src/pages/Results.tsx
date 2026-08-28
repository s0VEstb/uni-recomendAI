import { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { getLatestSurvey, type SurveySubmitResult } from '../api/client'
import styles from './Results.module.css'

// ── Skeleton Loading ─────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <li className={styles.card}>
      <div className={styles.cardContent}>
        <div className={`${styles.photoWrap}`}>
          <div className={`${styles.photo} ${styles.skeleton}`} />
        </div>
        <div className={styles.uniInfo} style={{ flex: 1 }}>
          <div className={`${styles.skeleton}`} style={{ height: '1.2rem', width: '60%', marginBottom: '0.5rem', borderRadius: 8 }} />
          <div className={`${styles.skeleton}`} style={{ height: '0.85rem', width: '40%', marginBottom: '0.75rem', borderRadius: 8 }} />
          <div className={`${styles.skeleton}`} style={{ height: '0.85rem', width: '80%', borderRadius: 8 }} />
        </div>
      </div>
    </li>
  )
}

// ── Score Bar ────────────────────────────────────────────────────────
function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'var(--score-high)' : pct >= 45 ? 'var(--score-mid)' : 'var(--score-low)'

  return (
    <div className={styles.scoreBarWrap} title={`Совпадение: ${pct}%`}>
      <div className={styles.scoreBarBg}>
        <div
          className={styles.scoreBarFill}
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className={styles.scoreBarLabel} style={{ color }}>{pct}%</span>
    </div>
  )
}

// ── Score Breakdown ──────────────────────────────────────────────────
function ScoreBreakdown({ breakdown }: { breakdown?: Record<string, number> }) {
  if (!breakdown) return null
  const items = [
    { key: 'ort', label: 'ОРТ', max: 0.35 },
    { key: 'tags', label: 'Интересы', max: 0.35 },
    { key: 'budget', label: 'Бюджет', max: 0.15 },
    { key: 'city', label: 'Город', max: 0.10 },
    { key: 'extra', label: 'Доп.', max: 0.05 },
  ]
  return (
    <div className={styles.breakdown}>
      {items.map(({ key, label, max }) => {
        const val = breakdown[key] ?? 0
        const pct = max > 0 ? Math.round((val / max) * 100) : 0
        return (
          <div key={key} className={styles.breakdownItem}>
            <span className={styles.breakdownLabel}>{label}</span>
            <div className={styles.breakdownBar}>
              <div
                className={styles.breakdownFill}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className={styles.breakdownPct}>{pct}%</span>
          </div>
        )
      })}
    </div>
  )
}

export default function Results() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as SurveySubmitResult | null
  const [data, setData] = useState<SurveySubmitResult | null>(state)
  const [loading, setLoading] = useState(!state)
  const [selectedPrograms, setSelectedPrograms] = useState<number[]>([])
  const [expandedBreakdowns, setExpandedBreakdowns] = useState<Set<number>>(new Set())

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

  const toggleBreakdown = (programId: number) => {
    setExpandedBreakdowns(prev => {
      const next = new Set(prev)
      next.has(programId) ? next.delete(programId) : next.add(programId)
      return next
    })
  }

  const reasonIcon = (code: string): string => {
    const icons: Record<string, string> = {
      budget_ok: '💰',
      budget_great: '🤑',
      budget_tight: '⚠️',
      budget_too_low: '⛔',
      fee_unknown: '❓',
      tag_match: '🎯',
      ort_ok: '✅',
      ort_strong: '🚀',
      ort_marginal: '⚡',
      ort_not_required: '📋',
      ort_unknown_or_not_required: '📋',
      city_match: '📍',
      dorm_needed: '🏠',
      relocation_ok: '✈️',
    }
    return icons[code] ?? '•'
  }

  if (loading) {
    return (
      <div className={styles.wrap}>
        <div className={`${styles.titleSkeleton} ${styles.skeleton}`} />
        <ul className={styles.list}>
          {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
        </ul>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={styles.wrap}>
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon}>🎓</span>
          <p className={styles.empty}>Пока нет результатов.</p>
          <p className={styles.emptyHint}>Пройдите опрос, и мы подберём университеты специально для вас.</p>
          <Link to="/survey" className={styles.startBtn}>Пройти опрос →</Link>
        </div>
      </div>
    )
  }

  const { message, universities_top } = data

  return (
    <div className={styles.wrap}>
      <div className={styles.headerRow}>
        <h1 className={styles.title}>Рекомендованные вузы</h1>
        <span className={styles.countBadge}>{universities_top.length} вузов</span>
      </div>
      {message && <p className={styles.message}>{message}</p>}

      {selectedPrograms.length >= 2 && (
        <div className={styles.compareBar}>
          <span>Выбрано программ: <strong>{selectedPrograms.length}</strong></span>
          <button
            className={styles.compareBtn}
            onClick={() => navigate('/compare', { state: { programIds: selectedPrograms } })}
          >
            Сравнить выбранные →
          </button>
        </div>
      )}

      <ul className={styles.list}>
        {universities_top.map((item, idx) => (
          <li
            key={item.university.id}
            className={styles.card}
            style={{ animationDelay: `${idx * 0.07}s` }}
          >
            <div className={styles.cardContent}>
              <div className={styles.photoWrap}>
                <img
                  src={item.university.photo_url || `https://picsum.photos/seed/${item.university.id}/160/120`}
                  alt={item.university.name}
                  className={styles.photo}
                  loading="lazy"
                />
                {/* Ранг */}
                {idx < 3 && (
                  <span className={styles.rankBadge}>
                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'}
                  </span>
                )}
              </div>
              <div className={styles.uniInfo}>
                <div className={styles.uniHeader}>
                  <h2 className={styles.uniName}>{item.university.name}</h2>
                </div>
                <div className={styles.uniMeta}>
                  {item.university.city && (
                    <span className={styles.metaChip}>📍 {item.university.city}</span>
                  )}
                  <span className={styles.metaChip}>📚 {item.programs_count} программ</span>
                </div>

                {/* Score bar */}
                <ScoreBar score={item.score} />

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
                        <button
                          type="button"
                          className={styles.breakdownToggle}
                          onClick={() => toggleBreakdown(pr.program.id)}
                          title="Детали скора"
                        >
                          {expandedBreakdowns.has(pr.program.id) ? '▲' : '▼'}
                        </button>
                      </div>

                      {/* Reasons */}
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

                      {/* Score breakdown (toggle) */}
                      {expandedBreakdowns.has(pr.program.id) && (
                        <ScoreBreakdown breakdown={(pr as any).score_breakdown} />
                      )}
                    </div>
                  ))}
                </div>

                <div className={styles.cardActions}>
                  <button
                    type="button"
                    className={styles.chatButton}
                    onClick={() => navigate('/chat', { state: { universityId: item.university.id, universityName: item.university.name } })}
                  >
                    💬 Спросить ИИ об этом вузе
                  </button>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <div className={styles.actions}>
        <button type="button" onClick={() => navigate('/survey')} className={styles.button}>
          ← Изменить параметры
        </button>
      </div>
    </div>
  )
}