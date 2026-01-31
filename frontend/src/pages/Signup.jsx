/**
 * 회원가입 페이지
 */

import React, { useState } from 'react';
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

  const validateForm = () => {
    if (formData.password.length < 6) {
      setError('비밀번호는 6자 이상이어야 합니다.');
      return false;
    }
    if (formData.password !== formData.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
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
            <span className="auth-logo-icon">📅</span>
            <h1 className="auth-title">5늘의 일정</h1>
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

          <Input
            type="password"
            name="password"
            label="비밀번호"
            placeholder="비밀번호를 입력하세요 (6자 이상)"
            value={formData.password}
            onChange={handleChange}
            required
            fullWidth
            helper="비밀번호는 6자 이상이어야 합니다."
          />

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
            ← 홈으로 돌아가기
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Signup;
