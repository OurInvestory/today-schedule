/**
 * 회원가입 페이지
 */

import React, { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import './Auth.css';

const Signup = () => {
  const navigate = useNavigate();
  const { signup, login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError('');
  };

  // 비밀번호 유효성 검사 (실시간)
  const passwordValidation = useMemo(() => {
    const { password, passwordConfirm } = formData;
    const validations = {
      minLength: password.length >= 8,
      hasNumber: /\d/.test(password),
      hasLetter: /[a-zA-Z]/.test(password),
      passwordMatch: password === passwordConfirm && passwordConfirm.length > 0,
    };
    
    const isValid = validations.minLength && validations.hasNumber && validations.hasLetter && validations.passwordMatch;
    
    return { ...validations, isValid };
  }, [formData.password, formData.passwordConfirm]);

  // 비밀번호 힌트 메시지
  const getPasswordHint = () => {
    const { password, passwordConfirm } = formData;
    
    if (password.length === 0) return null;
    
    if (!passwordValidation.minLength) {
      return { type: 'error', message: '비밀번호는 8자 이상이어야 합니다.' };
    }
    if (!passwordValidation.hasLetter) {
      return { type: 'error', message: '영문자를 포함해야 합니다.' };
    }
    if (!passwordValidation.hasNumber) {
      return { type: 'error', message: '숫자를 포함해야 합니다.' };
    }
    
    return { type: 'success', message: '사용 가능한 비밀번호입니다.' };
  };

  // 비밀번호 확인 힌트 메시지
  const getPasswordConfirmHint = () => {
    const { passwordConfirm } = formData;
    
    if (passwordConfirm.length === 0) return null;
    
    if (!passwordValidation.passwordMatch) {
      return { type: 'error', message: '비밀번호가 일치하지 않습니다.' };
    }
    
    return { type: 'success', message: '비밀번호가 일치합니다.' };
  };

  const passwordHint = getPasswordHint();
  const passwordConfirmHint = getPasswordConfirmHint();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!passwordValidation.isValid) {
      if (!passwordValidation.minLength) {
        setError('비밀번호는 8자 이상이어야 합니다.');
      } else if (!passwordValidation.hasLetter || !passwordValidation.hasNumber) {
        setError('비밀번호는 영문자와 숫자를 포함해야 합니다.');
      } else if (!passwordValidation.passwordMatch) {
        setError('비밀번호가 일치하지 않습니다.');
      }
      return;
    }

    setLoading(true);

    try {
      const response = await signup(
        formData.email,
        formData.password,
        formData.passwordConfirm
      );
      
      if (response.status === 201) {
        // 회원가입 성공 후 자동 로그인
        const loginResponse = await login(formData.email, formData.password);
        if (loginResponse.status === 200) {
          navigate('/');
        } else {
          // 자동 로그인 실패 시 로그인 페이지로
          navigate('/login');
        }
      } else {
        setError(response.message || '회원가입에 실패했습니다.');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || '회원가입 중 오류가 발생했습니다.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <div className="auth-logo">
            <div className="auth-logo-icon">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
            </div>
            <h1 className="auth-title">오늘의 일정</h1>
          </div>
          <p className="auth-subtitle">AI 학업 스케줄 도우미</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <h2 className="auth-form-title">회원가입</h2>
          
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

          <div className="auth-input-wrapper">
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
            {passwordHint && (
              <p className={`auth-hint auth-hint--${passwordHint.type}`}>
                {passwordHint.message}
              </p>
            )}
          </div>

          <div className="auth-input-wrapper">
            <Input
              type="password"
              name="passwordConfirm"
              label="비밀번호 확인"
              placeholder="비밀번호를 다시 입력하세요"
              value={formData.passwordConfirm}
              onChange={handleChange}
              required
              fullWidth
            />
            {passwordConfirmHint && (
              <p className={`auth-hint auth-hint--${passwordConfirmHint.type}`}>
                {passwordConfirmHint.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            fullWidth
            loading={loading}
            disabled={loading}
          >
            회원가입
          </Button>
        </form>

        <div className="auth-footer">
          <p>
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="auth-link">
              로그인
            </Link>
          </p>
          <Link to="/" className="auth-back-link">
            홈으로 돌아가기
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Signup;
