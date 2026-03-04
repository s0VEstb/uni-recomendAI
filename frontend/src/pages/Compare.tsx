import { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { comparePrograms, type ProgramDetail } from '../api/client'
import styles from './Compare.module.css'

const LANG_MAP: Record<string, string> = {
    ru: 'Русский', russian: 'Русский',
    kg: 'Кыргызский', kyrgyz: 'Кыргызский',
    en: 'Английский', english: 'Английский',
    tr: 'Турецкий', turkish: 'Турецкий',
}

const FORM_MAP: Record<string, string> = {
    full_time: 'Очная',
    part_time: 'Заочная',
}

export default function Compare() {
    const location = useLocation()
    const navigate = useNavigate()
    const state = location.state as { programIds: number[] } | null
    const [programs, setPrograms] = useState<ProgramDetail[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const ids = state?.programIds
        if (!ids || ids.length < 2) {
            setError('Для сравнения выберите минимум 2 программы на странице результатов.')
            setLoading(false)
            return
        }
        comparePrograms(ids)
            .then((res) => setPrograms(res.programs))
            .catch((e) => setError(String(e)))
            .finally(() => setLoading(false))
    }, [])

    if (loading) {
        return <div className={styles.wrap}><p className={styles.loading}>Загрузка сравнения…</p></div>
    }

    if (error) {
        return (
            <div className={styles.wrap}>
                <p className={styles.error}>{error}</p>
                <button className={styles.backBtn} onClick={() => navigate(-1)}>← Назад</button>
            </div>
        )
    }

    return (
        <div className={styles.wrap}>
            <div className={styles.header}>
                <h1 className={styles.title}>Сравнение программ</h1>
                <button className={styles.backBtn} onClick={() => navigate(-1)}>← К результатам</button>
            </div>

            <div className={styles.tableWrap}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th className={styles.rowLabel}>Критерий</th>
                            {programs.map((p) => (
                                <th key={p.id} className={styles.colHead}>
                                    <Link
                                        to={`/universities/${p.university.id}/programs/${p.id}`}
                                        className={styles.progLink}
                                    >
                                        {p.name}
                                    </Link>
                                    <span className={styles.uniSubtitle}>{p.university.name}</span>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td className={styles.rowLabel}>Город</td>
                            {programs.map((p) => <td key={p.id}>{p.university.city}</td>)}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Язык</td>
                            {programs.map((p) => <td key={p.id}>{LANG_MAP[p.language] ?? p.language}</td>)}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Форма</td>
                            {programs.map((p) => <td key={p.id}>{FORM_MAP[p.study_form] ?? p.study_form}</td>)}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Срок (лет)</td>
                            {programs.map((p) => <td key={p.id}>{p.duration_years}</td>)}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Стоимость (2026)</td>
                            {programs.map((p) => {
                                const fee = p.fees.find((f) => f.year === 2026) ?? p.fees[0]
                                return (
                                    <td key={p.id}>
                                        {fee ? `${fee.contract_fee.toLocaleString()} ${fee.currency}` : '—'}
                                    </td>
                                )
                            })}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Мин. ОРТ (2026)</td>
                            {programs.map((p) => {
                                const adm = p.admissions.find((a) => a.year === 2026) ?? p.admissions[0]
                                return <td key={p.id}>{adm?.ort_min_score != null ? adm.ort_min_score : '—'}</td>
                            })}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Теги</td>
                            {programs.map((p) => (
                                <td key={p.id}>
                                    {p.tags.length > 0
                                        ? p.tags.map((t) => <span key={t.id} className={styles.tag}>{t.title}</span>)
                                        : '—'}
                                </td>
                            ))}
                        </tr>
                        <tr>
                            <td className={styles.rowLabel}>Сайт</td>
                            {programs.map((p) => (
                                <td key={p.id}>
                                    {p.official_url
                                        ? <a href={p.official_url} target="_blank" rel="noopener noreferrer" className={styles.extLink}>Открыть ↗</a>
                                        : '—'}
                                </td>
                            ))}
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    )
}
