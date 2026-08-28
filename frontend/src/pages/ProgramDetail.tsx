import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProgramDetail, type ProgramDetail as ProgramDetailType } from '../api/client'
import styles from './ProgramDetail.module.css'

const LANGUAGE_LABELS: Record<string, string> = {
  russian: 'Русский',
  kyrgyz: 'Кыргызский',
  english: 'English',
  turkish: 'Türkçe',
}

const STUDY_FORM_LABELS: Record<string, string> = {
  full_time: 'Очная',
  part_time: 'Заочная / вечерняя',
}

export default function ProgramDetail() {
  const { universityId, programId } = useParams<{ universityId: string; programId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<ProgramDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const uid = universityId ? parseInt(universityId, 10) : NaN
    const pid = programId ? parseInt(programId, 10) : NaN
    if (Number.isNaN(uid) || Number.isNaN(pid)) {
      setError('Неверный адрес')
      setLoading(false)
      return
    }
    getProgramDetail(uid, pid)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Ошибка загрузки'))
      .finally(() => setLoading(false))
  }, [universityId, programId])

  if (loading) {
    return (
      <div className={styles.wrap}>
        <p className={styles.loading}>Загрузка…</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className={styles.wrap}>
        <p className={styles.error}>{error || 'Программа не найдена'}</p>
        <button type="button" className={styles.backButton} onClick={() => navigate(-1)}>
          ← Назад
        </button>
      </div>
    )
  }

  const { university, fees, admissions, tags } = data

  return (
    <div className={styles.wrap}>
      <button type="button" className={styles.backButton} onClick={() => navigate(-1)}>
        ← Назад к результатам
      </button>

      <div className={styles.header}>
        <div className={styles.uniPhotoWrap}>
          <img
            src={university.photo_url || `https://picsum.photos/seed/${university.id}/200/150`}
            alt={university.name}
            className={styles.uniPhoto}
          />
        </div>
        <div className={styles.headerText}>
          <h1 className={styles.programName}>{data.name}</h1>
          <p className={styles.uniName}>{university.name}</p>
          <p className={styles.meta}>
            <span className={styles.metaBadge}>📍 {university.city}</span>
            <span className={styles.metaBadge}>🌐 {LANGUAGE_LABELS[data.language] ?? data.language}</span>
            <span className={styles.metaBadge}>📋 {STUDY_FORM_LABELS[data.study_form] ?? data.study_form}</span>
            <span className={styles.metaBadge}>⏱ {data.duration_years} лет</span>
          </p>
          {data.official_url && (
            <a href={data.official_url} target="_blank" rel="noopener noreferrer" className={styles.officialLink}>
              Официальная страница программы →
            </a>
          )}
        </div>
      </div>

      {fees.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Стоимость</h2>
          <ul className={styles.feeList}>
            {fees.map((f) => (
              <li key={f.id} className={styles.feeCard}>
                <span className={styles.feeName}>{f.name}</span>
                <span className={styles.feeYear}>{f.year} г.</span>
                <span className={styles.feeAmount}>{f.contract_fee.toLocaleString('ru-KG')} {f.currency}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {admissions.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Поступление</h2>
          <ul className={styles.admList}>
            {admissions.map((a) => (
              <li key={a.id} className={styles.admCard}>
                <div className={styles.admYear}>Год: {a.year}</div>
                {a.ort_min_score != null && (
                  <div className={styles.admOrt}>Минимальный балл ОРТ: <strong>{a.ort_min_score}</strong></div>
                )}
                {a.requirements && Object.keys(a.requirements).length > 0 && (
                  <div className={styles.admReq}>
                    <span className={styles.label}>Требования:</span>
                    <pre className={styles.jsonBlock}>{JSON.stringify(a.requirements, null, 2)}</pre>
                  </div>
                )}
                {a.deadlines && Object.keys(a.deadlines).length > 0 && (
                  <div className={styles.admDead}>
                    <span className={styles.label}>Дедлайны:</span>
                    <pre className={styles.jsonBlock}>{JSON.stringify(a.deadlines, null, 2)}</pre>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {tags.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Направления / теги</h2>
          <div className={styles.tags}>
            {tags.map((t) => (
              <span key={t.id} className={styles.tag}>{t.title}</span>
            ))}
          </div>
        </section>
      )}

      <div className={styles.actions}>
        <button type="button" className={styles.backButton} onClick={() => navigate('/chat', { state: { universityId: university.id, universityName: university.name } })}>
          Чат с ИИ по вузу
        </button>
      </div>
    </div>
  )
}
