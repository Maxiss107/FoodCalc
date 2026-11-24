import { useState, type SyntheticEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError } from '../../../services/api';
import { ConfirmModal } from '../../../components/ui/ConfirmModal';
import { authApi } from '../../../services/authApi';

export function LoginForm() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      await authApi.login({ email, password }, rememberMe);
      navigate('/ingredients');
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('Не удалось связаться с сервером. Проверьте подключение к сети.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Поле: Электронная почта */}
        <div>
          <label className="block text-sm font-semibold text-[#1E293B] mb-2">
            Электронная почта
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-4 flex items-center text-gray-400 pointer-events-none">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <rect x="2" y="4" width="20" height="16" rx="3" />
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
              </svg>
            </span>
            <input
              type="email"
              required
              disabled={isLoading}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full h-12 pl-12 pr-4 rounded-xl border border-gray-200 bg-[#F8FAFC] text-[#1E293B] placeholder:text-gray-400 focus:bg-white focus:outline-none focus:border-[#F28C38] focus:ring-2 focus:ring-[#F28C38]/20 transition disabled:opacity-60"
            />
          </div>
        </div>

        {/* Поле: Пароль */}
        <div>
          <label className="block text-sm font-semibold text-[#1E293B] mb-2">
            Пароль
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-4 flex items-center text-gray-400 pointer-events-none">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <rect x="3" y="11" width="18" height="11" rx="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </span>
            <input
              type={showPassword ? 'text' : 'password'}
              required
              disabled={isLoading}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••"
              className="w-full h-12 pl-12 pr-12 rounded-xl border border-gray-200 bg-[#F8FAFC] text-[#1E293B] placeholder:text-gray-400 focus:bg-white focus:outline-none focus:border-[#F28C38] focus:ring-2 focus:ring-[#F28C38]/20 transition disabled:opacity-60"
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute inset-y-0 right-4 flex items-center text-gray-400 hover:text-gray-600 cursor-pointer"
              aria-label="Показать или скрыть пароль"
            >
              {showPassword ? (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Чекбокс "Запомнить меня" */}
        <div className="flex items-center pt-0.5">
          <label className="inline-flex items-center gap-2.5 cursor-pointer select-none">
            <input
              type="checkbox"
              disabled={isLoading}
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 accent-[#F28C38] cursor-pointer"
            />
            <span className="text-sm text-gray-500">Запомнить меня</span>
          </label>
        </div>

        {/* Кнопка входа */}
        <button
          type="submit"
          disabled={isLoading}
          className="relative w-full h-12 rounded-xl bg-gradient-to-r from-[#F69B4B] to-[#EC7E27] hover:from-[#ef8d39] hover:to-[#df711b] disabled:opacity-60 text-white font-semibold text-base shadow-md shadow-orange-500/20 flex items-center justify-center transition-all cursor-pointer"
        >
          <span>{isLoading ? 'Входим...' : 'Войти в аккаунт'}</span>
          {!isLoading && <span className="absolute right-5 text-lg leading-none">→</span>}
        </button>
      </form>

      {/* Модальное окно ошибки по макету 07_Modal_Windows 2 */}
      <ConfirmModal
        isOpen={Boolean(errorMessage)}
        onClose={() => setErrorMessage(null)}
        onConfirm={() => setErrorMessage(null)}
        variant="error"
        title="Не удалось войти"
        description={errorMessage || ''}
        confirmText="Понятно"
      />
    </>
  );
}
