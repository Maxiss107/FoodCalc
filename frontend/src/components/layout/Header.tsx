import { Link } from 'react-router-dom';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  return (
    <header
      style={{ height: 'var(--header-height)' }}
      className="sticky top-0 z-10 flex items-center justify-between px-6 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] shrink-0"
    >
      {/* Левая часть: кнопка меню для мобильных + место под хлебные крошки или поиск */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="lg:hidden px-2.5 py-1.5 rounded-lg border border-[var(--border-subtle)] text-sm text-[var(--text-main)] hover:bg-gray-50"
          aria-label="Открыть меню"
        >
          ☰
        </button>

        <span className="text-sm text-[var(--text-muted)] hidden sm:inline">
          Управление себестоимостью
        </span>
      </div>

      {/* Правая часть: профиль и выход */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[var(--accent-soft)] text-[var(--accent-text)] flex items-center justify-center text-sm font-semibold">
            П
          </div>
          <span className="text-sm font-medium text-[var(--text-main)]">
            Пользователь
          </span>
        </div>

        <Link
          to="/login"
          className="text-sm text-[var(--text-muted)] hover:text-red-600 transition-colors"
        >
          Выйти
        </Link>
      </div>
    </header>
  );
}
