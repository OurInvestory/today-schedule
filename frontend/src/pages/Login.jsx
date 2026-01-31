/**
 * 로그인 페이지
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import './Auth.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await login(formData.email, formData.password);
      if (response.status === 200) {
        navigate('/');
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

  // 테스트 계정으로 빠른 로그인
  const handleDemoLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const response = await login('demo@five-today.com', 'demo1234');
      if (response.status === 200) {
        navigate('/');
      } else {
        setError(response.message || '데모 로그인에 실패했습니다.');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || '데모 로그인 중 오류가 발생했습니다.';
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
          <h2 className="auth-form-title">로그인</h2>
          
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

          <div className="auth-divider">
            <span>또는</span>
          </div>

          <Button
            type="button"
            variant="secondary"
            fullWidth
            onClick={handleDemoLogin}
            disabled={loading}
          >
            🎯 데모 계정으로 시작하기
          </Button>
        </form>

        <div className="auth-footer">
          <p>
            계정이 없으신가요?{' '}
            <Link to="/signup" className="auth-link">
              회원가입
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

export default Login;
