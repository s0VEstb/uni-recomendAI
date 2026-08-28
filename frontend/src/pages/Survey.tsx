import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listTags, submitSurvey, getLatestSurvey, type Tag, type SurveyPayload, type Language, type City } from '../api/client'
import styles from './Survey.module.css'

const LANGUAGES: { value: Language; label: string }[] = [
  { value: 'russian', label: 'Русский' },
  { value: 'kyrgyz', label: 'Кыргызский' },
  { value: 'english', label: 'English' },
  { value: 'turkish', label: 'Türkçe' },
]

const CITIES: { value: City; label: string }[] = [
  { value: 'bishkek', label: 'Бишкек' },
  { value: 'osh', label: 'Ош' },
  { value: 'jalal_abad', label: 'Джалал-Абад' },
  { value: 'karakol', label: 'Каракол' },
  { value: 'tokmok', label: 'Токмок' },
  { value: 'naryn', label: 'Нарын' },
  { value: 'batken', label: 'Баткен' },
  { value: 'talas', label: 'Талас' },
  { value: 'uzgen', label: 'Узген' },
  { value: 'kara_balta', label: 'Кара-Балта' },
  { value: 'balykchy', label: 'Балыкчы' },
  { value: 'bazar_korgon', label: 'Базар-Коргон' },
  { value: 'kyzyl_kiya', label: 'Кызыл-Кия' },
  { value: 'tash_kumyr', label: 'Таш-Кумыр' },
  { value: 'kant', label: 'Кант' },
  { value: 'isfana', label: 'Исфана' },
  { value: 'mailuu_suu', label: 'Майлуу-Суу' },
  { value: 'kara_suu', label: 'Кара-Суу' },
  { value: 'other', label: 'Другой город' },
]

const STEPS = ['Основные данные', 'Интересы', 'Сильные стороны', 'Предметы']

export default function Survey() {
  const navigate = useNavigate()
  const [interests, setInterests] = useState<Tag[]>([])
  const [strengths, setStrengths] = useState<Tag[]>([])
  const [subjects, setSubjects] = useState<Tag[]>([])
  const [careers, setCareers] = useState<Tag[]>([])
  const [loadingTags, setLoadingTags] = useState(true)
  const [loadingSubmit, setLoadingSubmit] = useState(false)
  const [loadingLatest, setLoadingLatest] = useState(true)
  const [error, setError] = useState('')
  const [activeStep, setActiveStep] = useState(0)

  const [ortScore, setOrtScore] = useState('')
  const [budgetMax, setBudgetMax] = useState('')
  const [city, setCity] = useState<City | ''>('')
  const [language, setLanguage] = useState<Language | ''>('')
  const [notes, setNotes] = useState('')
  const [needsDorm, setNeedsDorm] = useState(false)
  const [willingToRelocate, setWillingToRelocate] = useState(false)
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])

  useEffect(() => {
    async function load() {
      try {
        const [i, s, sub, c] = await Promise.all([
          listTags('interest'),
          listTags('strength'),
          listTags('subject'),
          listTags('career'),
        ])
        setInterests(i)
        setStrengths(s)
        setSubjects(sub)
        setCareers(c)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Не удалось загрузить теги')
      } finally {
        setLoadingTags(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    async function loadLatest() {
      setLoadingLatest(true)
      try {
        const result = await getLatestSurvey()
        const s = result.submission
        setOrtScore(String(s.ort_score))
        setBudgetMax(s.budget_max != null ? String(s.budget_max) : '')
        setCity((s.city as City) || '')
        setLanguage((s.language as Language) || '')
        setNotes(s.notes || '')
        setNeedsDorm(s.needs_dorm ?? false)
        setWillingToRelocate(s.willing_to_relocate ?? false)
        setSelectedTagIds(result.submission.tag_ids || [])
      } catch {
        // 404 or error — leave form empty
      } finally {
        setLoadingLatest(false)
      }
    }
    loadLatest()
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
    if (Number.isNaN(ort) || ort < 0 || ort > 245) {
      setError('Укажите балл ОРТ от 0 до 245')
      return
    }
    setLoadingSubmit(true)
    try {
      const payload: SurveyPayload = {
        ort_score: ort,
        budget_max: budgetMax ? parseInt(budgetMax, 10) || null : null,
        city: city || null,
        language: language || null,
        notes: notes.trim() || null,
        needs_dorm: needsDorm,
        willing_to_relocate: willingToRelocate,
        answers: {},
        tag_ids: selectedTagIds,
      }
      const result = await submitSurvey(payload)
      navigate('/results', { state: result })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки')
    } finally {
      setLoadingSubmit(false)
    }
  }

  const countSelected = (tags: Tag[]) => tags.filter(t => selectedTagIds.includes(t.id)).length

  if (loadingTags || loadingLatest) {
    return (
      <div className={styles.wrap}>
        <div className={styles.loadingWrap}>
          <div className={styles.spinner} />
          <p className={styles.loading}>Загружаем опрос…</p>
        </div>
      </div>
    )
  }

  const STEPS_LABELS = ['Основные данные', 'Интересы', 'Сильные стороны', 'Предметы', 'Карьера']

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>
        Опрос для <span className={styles.titleGrad}>подбора вуза</span>
      </h1>

      {/* Stepper */}
      <div className={styles.stepper}>
        {STEPS_LABELS.map((s, i) => (
          <div key={s} className={styles.step}>
            <span className={`${styles.stepNum} ${activeStep === i ? styles.stepNumActive : ''}`}>{i + 1}</span>
            <span className={`${styles.stepLabel} ${activeStep === i ? styles.stepLabelActive : ''}`}>{s}</span>
            {i < STEPS_LABELS.length - 1 && <div className={styles.stepLine} />}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        {error && <p className={styles.error}>{error}</p>}

        {/* Section 1: Basic Data */}
        <section className={styles.section} onMouseEnter={() => setActiveStep(0)}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionBadge}>1</span>
            <h2>Основные данные</h2>
          </div>
          <div className={styles.fieldsGrid}>
            <label>
              Балл ОРТ (0–245)
              <input
                type="number"
                min={0}
                max={245}
                value={ortScore}
                onChange={(e) => setOrtScore(e.target.value)}
                required
                className={styles.input}
                placeholder="например, 130"
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
              <select
                value={city}
                onChange={(e) => setCity((e.target.value as City) || '')}
                className={styles.input}
              >
                <option value="">— выбрать —</option>
                {CITIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
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
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </label>
            <label style={{ gridColumn: '1 / -1' }}>
              Примечания
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Например: Хочу IT, интересует медицина…"
                className={styles.input}
              />
            </label>
          </div>
          <div className={styles.checkboxGroup}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={needsDorm}
                onChange={(e) => setNeedsDorm(e.target.checked)}
                className={styles.checkbox}
              />
              🏠 Нужна общага
            </label>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={willingToRelocate}
                onChange={(e) => setWillingToRelocate(e.target.checked)}
                className={styles.checkbox}
              />
              🚀 Готов к переезду
            </label>
          </div>
        </section>

        {/* Section 2: Interests */}
        <section className={styles.section} onMouseEnter={() => setActiveStep(1)}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionBadge} style={{ background: 'linear-gradient(135deg, #58a6ff, #3b82f6)' }}>2</span>
            <h2>Интересы</h2>
            {countSelected(interests) > 0 && (
              <span className={styles.tagCount}>✓ {countSelected(interests)}</span>
            )}
          </div>
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

        {/* Section 3: Strengths */}
        <section className={styles.section} onMouseEnter={() => setActiveStep(2)}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionBadge} style={{ background: 'linear-gradient(135deg, #a371f7, #8b5cf6)' }}>3</span>
            <h2>Сильные стороны</h2>
            {countSelected(strengths) > 0 && (
              <span className={styles.tagCount}>✓ {countSelected(strengths)}</span>
            )}
          </div>
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

        {/* Section 4: Subjects */}
        <section className={styles.section} onMouseEnter={() => setActiveStep(3)}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionBadge} style={{ background: 'linear-gradient(135deg, #f0a832, #f59e0b)' }}>4</span>
            <h2>Предметы</h2>
            {countSelected(subjects) > 0 && (
              <span className={styles.tagCount}>✓ {countSelected(subjects)}</span>
            )}
          </div>
          <p className={styles.sectionHint}>Какие предметы вам даются лучше всего?</p>
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

        {/* Section 5: Career */}
        {careers.length > 0 && (
          <section className={styles.section} onMouseEnter={() => setActiveStep(4)}>
            <div className={styles.sectionHeader}>
              <span className={styles.sectionBadge} style={{ background: 'linear-gradient(135deg, #3fb950, #22c55e)' }}>5</span>
              <h2>Карьера</h2>
              {countSelected(careers) > 0 && (
                <span className={styles.tagCount}>✓ {countSelected(careers)}</span>
              )}
            </div>
            <p className={styles.sectionHint}>Кем вы хотите работать в будущем?</p>
            <div className={styles.tags}>
              {careers.map((t) => (
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
        )}

        <div className={styles.submitRow}>
          <div className={styles.selectedSummary}>
            {selectedTagIds.length > 0 && (
              <span className={styles.selectedCount}>
                🎯 Выбрано интересов: <strong>{selectedTagIds.length}</strong>
              </span>
            )}
          </div>
          <button type="submit" disabled={loadingSubmit} className={styles.submit}>
            {loadingSubmit ? 'Отправка…' : 'Получить рекомендации →'}
          </button>
        </div>

      </form>
    </div>
  )
}
