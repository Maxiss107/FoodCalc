import { NavLink } from 'react-router-dom';

export interface NavItem {
  to: string;
  label: string;
  // Задел под будущие иконки от дизайнера
  icon?: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/catalog', label: 'Каталог и склад' },
  { to: '/orders', label: 'Доска заказов' },
  { to: '/purchases', label: 'Закупки' },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  return (
    <>
      {/* Затемнение фона на мобильных устройствах */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
        />
      )}

      <aside
        style={{ width: 'var(--sidebar-width)' }}
        className={`fixed inset-y-0 left-0 z-30 flex flex-col bg-[var(--bg-surface)] border-r border-[var(--border-subtle)] transition-transform duration-200 lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Логотип / название сервиса */}
        <div
          style={{ height: 'var(--header-height)' }}
          className="flex items-center justify-between px-6 border-b border-[var(--border-subtle)] shrink-0"
        >
          <span className="text-2xl font-bold tracking-tight text-[var(--text-main)] font-['Lora']">
            FoodCalc
          </span>

          <button
            onClick={onClose}
            className="lg:hidden text-sm text-[var(--text-muted)] hover:text-[var(--text-main)]"
          >
            ✕
          </button>
        </div>

        {/* Навигация */}
        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-xl text-[15px] font-medium transition-colors ${
                  isActive
                    ? 'bg-[var(--accent-soft)] text-[var(--accent-text)] font-semibold'
                    : 'text-[var(--text-muted)] hover:bg-gray-100 hover:text-[var(--text-main)]'
                }`
              }
            >
              {item.icon && <span className="shrink-0">{item.icon}</span>}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Нижний слот под будущие виджеты дизайнера (например, переключатель темы Dark/Light) */}
        <div className="p-4 border-t border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
          Учёт и калькуляция
        </div>
      </aside>
    </>
  );
}