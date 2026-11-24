import { Link } from 'react-router-dom';
import { LoginForm } from '../components/LoginForm';

function FoodCalcLogo({ className = 'w-11 h-11' }: { className?: string }) {
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
      {/* Пышный поварской колпак (3 округлые секции) */}
      <path d="M18 28C12.8 28 9 24.4 9 19.6C9 15.6 11.8 12.3 15.8 11.5C17.6 7.4 22.1 4.5 27.5 4.5C29.4 4.5 31.2 4.9 32.8 5.6C34.4 4.9 36.2 4.5 38.1 4.5C43.5 4.5 48 7.4 49.8 11.5C53.8 12.3 56.6 15.6 56.6 19.6C56.6 24.4 52.8 28 47.6 28H18Z" />

      {/* Вилка слева (выступает за край блока) */}
      <path d="M11 33V39.5C11 41.8 12.8 43.5 15 43.5C17.2 43.5 19 41.8 19 39.5V33" />
      <line x1="15" y1="33" x2="15" y2="39.5" />
      <line x1="15" y1="43.5" x2="15" y2="55" />

      {/* Правая часть (корпус калькулятора с 4 квадратными кнопками) */}
      <path d="M23 28H48V50C48 53.3 45.3 56 42 56H24C21.2 56 19 53.8 19 51V45" />
      <rect x="27" y="34" width="6" height="6" rx="1" />
      <rect x="37" y="34" width="6" height="6" rx="1" />
      <rect x="27" y="44" width="6" height="6" rx="1" />
      <rect x="37" y="44" width="6" height="6" rx="1" />
    </svg>
  );
}

export function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#DCE3EC] p-4 sm:p-6">
      {/* Главная белая карточка */}
      <div className="w-full max-w-[1020px] bg-white rounded-[28px] shadow-xl p-3 sm:p-4 grid grid-cols-1 lg:grid-cols-12">
        {/* Левый оранжевый блок — 1 в 1 по эталону */}
        <div className="hidden lg:flex lg:col-span-5 flex-col justify-between rounded-[22px] bg-[#F59544] p-9 text-white relative overflow-hidden min-h-[610px]">
          {/* Светлый круглый блик в правом верхнем углу */}
          <div className="w-44 h-44 rounded-full bg-white/15 absolute -top-8 -right-10 pointer-events-none" />

          {/* Верхний логотип и заголовки */}
          <div className="relative z-10">
            <div className="flex items-center gap-3.5">
              <FoodCalcLogo className="w-12 h-12 text-white shrink-0" />
              <span className="text-[28px] font-bold tracking-tight">FoodCalc</span>
            </div>

            <h2 className="mt-12 text-[34px] font-bold leading-[1.18] font-['Lora']">
              Готовить проще,
              <br />с FoodCalc.
            </h2>
            <p className="mt-4 text-[14px] text-white/90 leading-relaxed max-w-[300px]">
              Войдите в FoodCalc — ваши рецепты,
              <br />
              расчёты и любимые блюда всегда рядом.
            </p>
          </div>

          {/* Центральная эмблема в кольцах */}
          <div className="flex justify-center items-center my-4 relative z-10">
            <div className="w-44 h-44 rounded-full bg-white/12 flex items-center justify-center">
              <div className="w-32 h-32 rounded-full border border-white/50 flex items-center justify-center">
                <FoodCalcLogo className="w-16 h-16 text-white" />
              </div>
            </div>
          </div>

          {/* Нижняя строка */}
          <div className="relative z-10 text-[11px] font-semibold tracking-wide uppercase text-white/95">
            FOODCALC - ВАША КУХНЯ В ОДНОМ МЕСТЕ
          </div>

          {/* Декоративные тонкие дуги на фоне */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none opacity-20"
            viewBox="0 0 400 610"
            fill="none"
          >
            <path
              d="M-30 355 C 110 285, 250 425, 430 335"
              stroke="white"
              strokeWidth="1.8"
            />
            <circle cx="95" cy="545" r="165" stroke="white" strokeWidth="1.5" />
          </svg>
        </div>

        {/* Правая часть с формой входа */}
        <div className="lg:col-span-7 flex flex-col justify-center px-6 py-10 sm:px-14">
          <div className="w-full max-w-md mx-auto">
            <h1 className="text-3xl font-bold text-[#1E293B]">
              С возвращением!
            </h1>
            <p className="text-sm text-gray-500 mt-2 mb-8">
              Войдите, чтобы продолжить готовить с удовольствием
            </p>

            <LoginForm />

            <p className="text-center text-sm text-gray-500 mt-7">
              Впервые в FoodCalc?{' '}
              <Link
                to="/register"
                className="font-semibold text-[#EC7E27] hover:underline ml-1"
              >
                Создать аккаунт
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
