interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  return (
    <header
      style={{ height: 'var(--header-height)' }}
      className="sticky top-0 z-10 flex items-center justify-between px-6 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] shrink-0"
    >
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
          Рабочее пространство мастера
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div className="text-right hidden sm:block">
          <div className="text-sm font-semibold text-[var(--text-main)]">
            Мастер кухни
          </div>
          <div className="text-xs text-[var(--text-muted)]">
            user@foodcalc.ru
          </div>
        </div>
        <div className="w-9 h-9 rounded-full bg-[var(--accent-soft)] text-[var(--accent-text)] border border-[var(--accent-primary)]/20 flex items-center justify-center text-sm font-bold">
          М
        </div>
      </div>
    </header>
  );
}
