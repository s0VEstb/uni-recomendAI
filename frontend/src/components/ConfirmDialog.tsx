import { useEffect } from 'react'
import styles from './ConfirmDialog.module.css'

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  danger = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  // Закрытие по Escape
  useEffect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, onCancel])

  if (!isOpen) return null

  return (
    <div className={styles.overlay} onClick={onCancel} role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
        <div className={styles.iconWrap}>
          <span className={styles.icon}>{danger ? '🗑' : '⚠️'}</span>
        </div>
        <h2 id="dialog-title" className={styles.title}>{title}</h2>
        <p className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelBtn}
            onClick={onCancel}
            autoFocus
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`${styles.confirmBtn} ${danger ? styles.confirmDanger : ''}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
