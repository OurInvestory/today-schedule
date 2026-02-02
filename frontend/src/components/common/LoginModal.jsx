/**
 * 로그인 모달 컴포넌트
 * 비로그인 사용자가 기능을 사용하려 할 때 표시
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Button from './Button';
import Input from './Input';
import '../../../src/pages/Auth.css';

const LoginModal = () => {
  const navigate = useNavigate();
  const { showLoginModal, closeLoginModal, login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!showLoginModal) {
    return null;
  }

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await login(formData.email, formData.password);
      if (response.success) {
        setFormData({ email: '', password: '' });
        closeLoginModal();
      } else {
        setError(response.message || '로그인에 실패했습니다.');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || '로그인 중 오류가 발생했습니다.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoToSignup = () => {
    closeLoginModal();
    navigate('/signup');
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      closeLoginModal();
    }
  };

  return (
    <div className="login-modal-overlay" onClick={handleOverlayClick}>
      <div className="login-modal">
        <button className="login-modal__close" onClick={closeLoginModal}>
          ×
        </button>
        
        <div className="login-modal__header">
          <h2 className="login-modal__title">로그인이 필요합니다</h2>
          <p className="login-modal__subtitle">이 기능을 사용하려면 로그인해주세요</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}

          <Input
            type="email"
            name="email"
            label="이메일"
            placeholder="이메일을 입력하세요"
            value={formData.email}
            onChange={handleChange}
            required
            fullWidth
          />

          <Input
            type="password"
            name="password"
            label="비밀번호"
            placeholder="비밀번호를 입력하세요"
            value={formData.password}
            onChange={handleChange}
            required
            fullWidth
          />

          <Button
            type="submit"
            variant="primary"
            fullWidth
            loading={loading}
            disabled={loading}
          >
            로그인
          </Button>
        </form>

        <div className="auth-footer">
          <p>
            계정이 없으신가요?{' '}
            <button 
              type="button" 
              className="auth-link" 
              onClick={handleGoToSignup}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              회원가입
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginModal;
