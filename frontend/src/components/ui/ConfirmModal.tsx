import { Modal } from './Modal';

export type DialogVariant = 'confirm' | 'danger' | 'success' | 'info' | 'error';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  variant?: DialogVariant;
  title: string;
  description: string;
  confirmText: string;
  cancelText?: string;
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  variant = 'confirm',
  title,
  description,
  confirmText,
  cancelText,
}: ConfirmModalProps) {
  const isBlueBadge = variant === 'success' || variant === 'info';

  const renderIcon = () => {
    switch (variant) {
      case 'danger':
        return (
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        );
      case 'success':
        return (
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        );
      case 'info':
        return <span className="text-xl font-bold leading-none">i</span>;
      case 'error':
        return <span className="text-xl font-bold leading-none">!</span>;
      case 'confirm':
      default:
        return <span className="text-xl font-bold leading-none">?</span>;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="sm"
      showCloseButton={false}
    >
      <div className="flex flex-col items-center text-center pt-1">
        {/* Круглый бейдж с иконкой сверху */}
        <div
          className={`w-14 h-14 rounded-full flex items-center justify-center mb-5 ${
            isBlueBadge
              ? 'bg-[#EAF3FB] text-[#5B9BD5]'
              : 'bg-[#FFF3E6] text-[#F28C38]'
          }`}
        >
          {renderIcon()}
        </div>

        {/* Заголовок и описание */}
        <h3 className="text-[22px] font-bold text-[#1E293B] leading-snug">
          {title}
        </h3>
        <p className="text-sm text-gray-500 mt-2.5 leading-relaxed max-w-[270px]">
          {description}
        </p>

        {/* Вертикальный стек кнопок на всю ширину */}
        <div className="w-full mt-7 space-y-2.5">
          <button
            type="button"
            onClick={onConfirm}
            className="w-full h-11 rounded-xl bg-gradient-to-r from-[#F69B4B] to-[#EC7E27] hover:from-[#ef8d39] hover:to-[#df711b] text-white font-semibold text-sm shadow-sm shadow-orange-500/20 transition-all cursor-pointer"
          >
            {confirmText}
          </button>

          {cancelText && (
            <button
              type="button"
              onClick={onClose}
              className="w-full h-11 rounded-xl bg-[#EEF4FA] hover:bg-[#e2ecf6] text-[#5C7089] font-semibold text-sm transition-colors cursor-pointer"
            >
              {cancelText}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
