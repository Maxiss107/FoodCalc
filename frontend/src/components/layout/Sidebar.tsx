import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { ConfirmModal } from '../ui/ConfirmModal';
import { authApi } from '../../services/authApi';

interface NavItem {
  to: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/recipes', label: 'Рецепты' },
  { to: '/ingredients', label: 'Ингредиенты' },
  { to: '/purchases', label: 'Закупки' },
  { to: '/orders', label: 'Заказы' },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

function FoodCalcLogo({ className = 'w-9 h-9' }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      fill="none"
      stroke="currentColor"
      strokeWidth="3.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M18 28C12.8 28 9 24.4 9 19.6C9 15.6 11.8 12.3 15.8 11.5C17.6 7.4 22.1 4.5 27.5 4.5C29.4 4.5 31.2 4.9 32.8 5.6C34.4 4.9 36.2 4.5 38.1 4.5C43.5 4.5 48 7.4 49.8 11.5C53.8 12.3 56.6 15.6 56.6 19.6C56.6 24.4 52.8 28 47.6 28H18Z" />
      <path d="M11 33V39.5C11 41.8 12.8 43.5 15 43.5C17.2 43.5 19 41.8 19 39.5V33" />
      <line x1="15" y1="33" x2="15" y2="39.5" />
      <line x1="15" y1="43.5" x2="15" y2="55" />
      <path d="M23 28H48V50C48 53.3 45.3 56 42 56H24C21.2 56 19 53.8 19 51V45" />
      <rect x="27" y="34" width="6" height="6" rx="1" />
      <rect x="37" y="34" width="6" height="6" rx="1" />
      <rect x="27" y="44" width="6" height="6" rx="1" />
      <rect x="37" y="44" width="6" height="6" rx="1" />
    </svg>
  );
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

  const handleConfirmLogout = () => {
    authApi.logout();
    setIsLogoutModalOpen(false);
    onClose?.();
    navigate('/login');
  };

  return (
    <>
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
        {/* Логотип FoodCalc */}
        <div
          style={{ height: 'var(--header-height)' }}
          className="flex items-center justify-between px-6 border-b border-[var(--border-subtle)] shrink-0"
        >
          <div className="flex items-center gap-2.5">
            <FoodCalcLogo className="w-9 h-9 text-[var(--accent-primary)] shrink-0" />
            <span className="text-xl font-bold tracking-tight text-[var(--text-main)]">
              Food<span className="text-[var(--accent-primary)]">Calc</span>
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="lg:hidden text-sm text-[var(--text-muted)] hover:text-[var(--text-main)] cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Навигация по 4 разделам */}
        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-[15px] font-medium transition-colors ${
                  isActive
                    ? 'bg-[var(--accent-soft)] text-[var(--accent-text)] font-semibold'
                    : 'text-[var(--text-muted)] hover:bg-gray-100 hover:text-[var(--text-main)]'
                }`
              }
            >
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Кнопка вызова модалки выхода */}
        <div className="p-4 border-t border-[var(--border-subtle)]">
          <button
            type="button"
            onClick={() => setIsLogoutModalOpen(true)}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-sm font-medium text-[var(--text-muted)] hover:bg-red-50 hover:text-red-600 transition-colors cursor-pointer"
          >
            <svg
              className="w-4 h-4 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span>Выйти из аккаунта</span>
          </button>
        </div>
      </aside>

      {/* Модальное окно подтверждения выхода по макету 07_Modal_Windows 2 */}
      <ConfirmModal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={handleConfirmLogout}
        variant="confirm"
        title="Выйти из аккаунта?"
        description="Вы действительно хотите завершить текущий сеанс?"
        confirmText="Выйти"
        cancelText="Остаться"
      />
    </>
  );
}
