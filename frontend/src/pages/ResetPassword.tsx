import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { auth as authApi } from '../api/client'
import styles from './Auth.module.css'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [token, setToken] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const t = searchParams.get('token')
    setToken(t)
    if (!t) {
      setError('Ссылка для сброса некорректна или устарела.')
    }
  }, [searchParams])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token) return
    setError('')
    setSuccess('')
    if (!password || password.length < 6) {
      setError('Пароль должен быть не короче 6 символов.')
      return
    }
    if (password !== confirm) {
      setError('Пароли не совпадают.')
      return
    }
    setLoading(true)
    try {
      await authApi.resetPassword(token, password)
      setSuccess('Пароль успешно изменён. Сейчас вы будете перенаправлены на страницу входа.')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.iconWrap}>🔒</div>
        <h1 className={styles.title}>Новый пароль</h1>
        <p className={styles.subtitle}>Придумайте надёжный пароль для входа в Uni Recomend.</p>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && <p className={styles.error}>{error}</p>}
          {success && !error && <p className={styles.success}>{success}</p>}
          <label>
            Новый пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className={styles.input}
              placeholder="Минимум 6 символов"
            />
          </label>
          <label>
            Повторите пароль
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              className={styles.input}
              placeholder="Повторите пароль"
            />
          </label>
          <button type="submit" disabled={loading || !token} className={styles.button}>
            {loading ? 'Сохраняем…' : 'Сохранить новый пароль →'}
          </button>
        </form>
      </div>
    </div>
  )
}
