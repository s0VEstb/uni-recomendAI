import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listTags, submitSurvey, type Tag, type SurveyPayload, type Language } from '../api/client'
import styles from './Survey.module.css'

const LANGUAGES: { value: Language; label: string }[] = [
  { value: 'russian', label: 'Русский' },
  { value: 'kyrgyz', label: 'Кыргызский' },
  { value: 'english', label: 'English' },
  { value: 'turkish', label: 'Türkçe' },
]

const RESULTS_KEY = 'uni_survey_results'

export default function Survey() {
  const navigate = useNavigate()
  const [interests, setInterests] = useState<Tag[]>([])
  const [strengths, setStrengths] = useState<Tag[]>([])
  const [subjects, setSubjects] = useState<Tag[]>([])
  const [loadingTags, setLoadingTags] = useState(true)
  const [loadingSubmit, setLoadingSubmit] = useState(false)
  const [error, setError] = useState('')

  const [ortScore, setOrtScore] = useState('')
  const [budgetMax, setBudgetMax] = useState('')
  const [city, setCity] = useState('')
  const [language, setLanguage] = useState<Language | ''>('')
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])

  useEffect(() => {
    async function load() {
      try {
        const [i, s, sub] = await Promise.all([
          listTags('interest'),
          listTags('strength'),
          listTags('subject'),
        ])
        setInterests(i)
        setStrengths(s)
        setSubjects(sub)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Не удалось загрузить теги')
      } finally {
        setLoadingTags(false)
      }
    }
    load()
  }, [])

  function toggleTag(id: number) {
    setSelectedTagIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    const ort = parseInt(ortScore, 10)
    if (Number.isNaN(ort) || ort < 0 || ort > 300) {
      setError('Укажите балл ОРТ от 0 до 300')
      return
    }
    setLoadingSubmit(true)
    try {
      const payload: SurveyPayload = {
        ort_score: ort,
        budget_max: budgetMax ? parseInt(budgetMax, 10) || null : null,
        city: city.trim() || null,
        language: language || null,
        answers: {},
        tag_ids: selectedTagIds,
      }
      const result = await submitSurvey(payload)
      localStorage.setItem(RESULTS_KEY, JSON.stringify(result))
      navigate('/results', { state: result })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки')
    } finally {
      setLoadingSubmit(false)
    }
  }

  if (loadingTags) {
    return <p className={styles.loading}>Загрузка опроса…</p>
  }

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>Опрос для подбора вуза</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        {error && <p className={styles.error}>{error}</p>}

        <section className={styles.section}>
          <h2>Балл ОРТ и условия</h2>
          <label>
            Балл ОРТ (0–300)
            <input
              type="number"
              min={0}
              max={300}
              value={ortScore}
              onChange={(e) => setOrtScore(e.target.value)}
              required
              className={styles.input}
            />
          </label>
          <label>
            Макс. бюджет (сом)
            <input
              type="number"
              min={0}
              value={budgetMax}
              onChange={(e) => setBudgetMax(e.target.value)}
              placeholder="Не указан"
              className={styles.input}
            />
          </label>
          <label>
            Город
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Бишкек"
              className={styles.input}
            />
          </label>
          <label>
            Язык обучения
            <select
              value={language}
              onChange={(e) => setLanguage((e.target.value as Language) || '')}
              className={styles.input}
            >
              <option value="">— выбрать —</option>
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className={styles.section}>
          <h2>Интересы</h2>
          <div className={styles.tags}>
            {interests.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleTag(t.id)}
                className={selectedTagIds.includes(t.id) ? styles.tagActive : styles.tag}
              >
                {t.title}
              </button>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2>Сильные стороны</h2>
          <div className={styles.tags}>
            {strengths.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleTag(t.id)}
                className={selectedTagIds.includes(t.id) ? styles.tagActive : styles.tag}
              >
                {t.title}
              </button>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2>Предметы</h2>
          <div className={styles.tags}>
            {subjects.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleTag(t.id)}
                className={selectedTagIds.includes(t.id) ? styles.tagActive : styles.tag}
              >
                {t.title}
              </button>
            ))}
          </div>
        </section>

        <button type="submit" disabled={loadingSubmit} className={styles.submit}>
          {loadingSubmit ? 'Отправка…' : 'Получить рекомендации'}
        </button>
      </form>
    </div>
  )
}

export { RESULTS_KEY }
