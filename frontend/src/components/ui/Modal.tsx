import { useEffect, type ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg';
  showCloseButton?: boolean;
}

const WIDTH_CLASSES = {
  sm: 'max-w-[380px]',
  md: 'max-w-md',
  lg: 'max-w-lg',
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = 'md',
  showCloseButton = true,
}: ModalProps) {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Затемнение фона */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-[#1E293B]/35 backdrop-blur-[2px] transition-opacity"
      />

      {/* Карточка модального окна */}
      <div
        className={`relative z-10 w-full ${WIDTH_CLASSES[maxWidth]} bg-white rounded-[28px] shadow-[0_20px_50px_rgba(15,23,42,0.12)] border border-gray-100 p-7 sm:p-8`}
      >
        {title && (
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-xl font-bold text-[#1E293B] font-['Lora']">
              {title}
            </h3>
            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors cursor-pointer"
                aria-label="Закрыть"
              >
                ✕
              </button>
            )}
          </div>
        )}

        {!title && showCloseButton && (
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors cursor-pointer"
            aria-label="Закрыть"
          >
            ✕
          </button>
        )}

        <div>{children}</div>
      </div>
    </div>
  );
}
