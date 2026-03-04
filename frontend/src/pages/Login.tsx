import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { auth as authApi } from '../api/client'
import styles from './Auth.module.css'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setInfo('')
    setLoading(true)
    try {
      const { access_token } = await authApi.login(email, password)
      login(access_token)
      navigate('/survey')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.iconWrap}>🔑</div>
        <h1 className={styles.title}>Вход</h1>
        <p className={styles.subtitle}>Продолжите работу с опросом и рекомендациями.</p>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && <p className={styles.error}>{error}</p>}
          {info && !error && <p className={styles.success}>{info}</p>}
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className={styles.input}
              placeholder="you@example.com"
            />
          </label>
          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className={styles.input}
              placeholder="••••••••"
            />
          </label>
          <button type="submit" disabled={loading} className={styles.button}>
            {loading ? 'Вход…' : 'Войти →'}
          </button>
        </form>
        <div className={styles.footer}>
          <p>
            Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
          </p>
          <button
            type="button"
            className={styles.buttonSecondary}
            onClick={async () => {
              if (!email) {
                setError('Укажите email, чтобы получить ссылку для сброса пароля')
                return
              }
              setError('')
              setInfo('')
              try {
                await authApi.forgotPassword(email)
                setInfo('Если такой аккаунт существует, мы отправили письмо со ссылкой для сброса пароля.')
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Не удалось отправить письмо')
              }
            }}
          >
            Забыли пароль?
          </button>
        </div>
      </div>
    </div>
  )
}