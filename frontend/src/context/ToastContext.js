import { createContext } from 'react';

// Toast Context - 별도 파일로 분리하여 Fast Refresh 호환
export const ToastContext = createContext(null);

export default ToastContext;
