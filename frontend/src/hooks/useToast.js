import { useContext } from 'react';
import { ToastContext } from '../context/ToastContext';

// useToast hook - 별도 파일로 분리하여 Fast Refresh 호환
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export default useToast;
