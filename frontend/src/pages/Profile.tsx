import { Link } from 'react-router-dom'
import styles from './Profile.module.css'

export default function Profile() {
  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>Профиль</h1>
      <div className={styles.actions}>
        <Link to="/survey" className={styles.link}>Редактировать опрос</Link>
        <Link to="/results" className={styles.link}>Мои результаты</Link>
      </div>
    </div>
  )
}
