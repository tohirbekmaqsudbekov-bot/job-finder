import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import type { CredentialResponse } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import './login.css';
import { motion } from 'framer-motion';

interface LoginProps {
  onLogin: (user: { name: string; email: string; picture?: string }) => void;
}

interface GoogleUserInfo {
  name: string;
  email: string;
  picture: string;
  sub: string;
}

export default function Login({ onLogin }: LoginProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const validateEmail = (emailStr: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailStr);
  };

  // Email login va Ro'yxatdan o'tish mantig'i
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!email || !password) {
      setError('Email va parolni kiriting!');
      return;
    }
    if (!validateEmail(email)) {
      setError("Email manzili noto'g'ri kiritildi!");
      return;
    }
    if (password.length < 6) {
      setError("Parol kamida 6 ta belgi bo'lishi kerak!");
      return;
    }

    const users = JSON.parse(localStorage.getItem('registered_users') || '[]');

    if (isRegister) {
      if (!name.trim()) {
        setError('Ismingizni kiriting!');
        return;
      }

      const isEmailTaken = users.some((u: any) => u.email.toLowerCase() === email.toLowerCase());
      if (isEmailTaken) {
        setError('Bu email allaqachon ro\'yxatdan o\'tgan!');
        return;
      }

      const newUser = { name, email: email.toLowerCase(), password };
      users.push(newUser);
      localStorage.setItem('registered_users', JSON.stringify(users));

      setSuccess("Muvaffaqiyatli ro'yxatdan o'tdingiz! Kirilmoqda...");

      setTimeout(() => {
        onLogin({
          name: newUser.name,
          email: newUser.email
        });
      }, 1200);

    } else {
      const foundUser = users.find((u: any) => u.email.toLowerCase() === email.toLowerCase());

      if (!foundUser) {
        setError('Bunday email ro\'yxatdan o\'tmagan! Avval ro\'yxatdan o\'ting.');
        return;
      }

      if (foundUser.password !== password) {
        setError('Kiritilgan parol noto\'g\'ri!');
        return;
      }

      onLogin({
        name: foundUser.name,
        email: foundUser.email
      });
    }
  };

  // Google login
  const handleGoogleSuccess = (credentialResponse: CredentialResponse) => {
    try {
      if (credentialResponse.credential) {
        const decoded: GoogleUserInfo = jwtDecode(credentialResponse.credential);
        console.log("Google ma'lumot:", decoded);

        const users = JSON.parse(localStorage.getItem('registered_users') || '[]');
        const isExist = users.some((u: any) => u.email.toLowerCase() === decoded.email.toLowerCase());

        if (!isExist) {
          users.push({
            name: decoded.name,
            email: decoded.email.toLowerCase(),
            password: 'google_oauth_secret_pass'
          });
          localStorage.setItem('registered_users', JSON.stringify(users));
        }

        onLogin({
          name: decoded.name,
          email: decoded.email,
          picture: decoded.picture
        });
      }
    } catch (err) {
      console.error("Google xato:", err);
      setError("Google bilan kirishda xato yuz berdi");
    }
  };

  const handleGoogleError = () => {
    setError("Google bilan kirish muvaffaqiyatsiz yakunlandi");
  };

  return (
    <div className="login-container" style={{ position: 'relative', overflow: 'hidden', backgroundColor: '#1E223D' }}>

      {/* =======================================================================
          RANGLARI DOIMIY RAVISHDA SILLIQ O'ZGARIB TURADIGAN NEON FOYDA ANIMATSIYASI
          ======================================================================= */}
      <style>{`
        @keyframes float-orb-1 {
          0% { transform: translate(0px, 0px) scale(1); }
          50% { transform: translate(60px, -80px) scale(1.2); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        @keyframes float-orb-2 {
          0% { transform: translate(0px, 0px) scale(1.1); }
          50% { transform: translate(-80px, 50px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1.1); }
        }
        @keyframes float-orb-3 {
          0% { transform: translate(0px, 0px) scale(1); }
          50% { transform: translate(40px, 60px) scale(1.15); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        /* Ranglarni spektr bo'ylab silliq aylantirish animatsiyasi */
        @keyframes color-cycle {
          0% { filter: blur(140px) hue-rotate(0deg); }
          100% { filter: blur(140px) hue-rotate(360deg); }
        }
        .bg-glow-orb {
          position: absolute;
          border-radius: 50%;
          opacity: 0.70; /* Yorqinligini bir oz ko'tardik */
          pointer-events: none;
          z-index: 1;
          /* Rang aylanish animatsiyasi shu yerda ulanadi */
          animation-name: color-cycle;
          animation-duration: 15s;
          animation-iteration-count: infinite;
          animation-timing-function: linear;
        }
        .login-box {
          position: relative;
          z-index: 5;
          backdrop-filter: blur(14px) !important;
          background: rgba(30, 32, 57, 0.82) !important;
          border: 1px solid rgba(255, 255, 255, 0.08) !important;
          box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6) !important;
        }
      `}</style>

      {/* Ranglari va joylashuvi doimiy aylanib o'zgaradigan neon sharlar */}
      <div className="bg-glow-orb" style={{
        width: '550px',
        height: '550px',
        backgroundColor: '#F54F1B',
        top: '-15%',
        left: '5%',
        animation: 'color-cycle 18s infinite linear, float-orb-1 22s infinite ease-in-out'
      }} />
      <div className="bg-glow-orb" style={{
        width: '650px',
        height: '650px',
        backgroundColor: '#1E223D',
        bottom: '-20%',
        right: '5%',
        animation: 'color-cycle 18s infinite linear, float-orb-2 26s infinite ease-in-out'
      }} />
      <div className="bg-glow-orb" style={{
        width: '450px',
        height: '450px',
        backgroundColor: '#F54F1B',
        top: '20%',
        right: '25%',
        animation: 'color-cycle 18s infinite linear, float-orb-3 20s infinite ease-in-out'
      }} />

      {/* =======================================================================
          ANIMATSIYALI LOGIN CARD
          ======================================================================= */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="login-box"
      >
        <div className="login-logo">
          <i className="fas fa-robot"></i>
        </div>

        <h1 className="login-title">
          {isRegister ? "Ro'yxatdan o'tish" : 'Xush kelibsiz!'}
        </h1>
        <p className="login-subtitle">
          {isRegister ? "Job Finder AI ga qo'shiling" : "Davom etish uchun tizimga kiring"}
        </p>

        {/* GOOGLE LOGIN TUGMASI */}
        <div className="google-login-wrapper">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            theme="filled_black"
            size="large"
            text={isRegister ? "signup_with" : "signin_with"}
            shape="rectangular"
            width="360"
          />
        </div>

        <div className="divider">
          <span>yoki email bilan</span>
        </div>

        {/* Xatolik va muvaffaqiyat xabarlari */}
        {error && (
          <div className="error-message" style={{ marginBottom: '15px' }}>
            <i className="fas fa-exclamation-circle"></i>
            {error}
          </div>
        )}
        {success && (
          <div className="success-message" style={{ color: '#F54F1B', display: 'flex', gap: '8px', alignItems: 'center', fontSize: '14px', marginBottom: '15px' }}>
            <i className="fas fa-check-circle"></i>
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          {isRegister && (
            <div className="input-group">
              <label>Ism</label>
              <div className="input-wrapper-login">
                <i className="fas fa-user input-icon"></i>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ismingiz"
                />
              </div>
            </div>
          )}

          <div className="input-group">
            <label>Email</label>
            <div className="input-wrapper-login">
              <i className="fas fa-envelope input-icon"></i>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@mail.com"
              />
            </div>
          </div>

          <div className="input-group">
            <label>Parol</label>
            <div className="input-wrapper-login">
              <i className="fas fa-lock input-icon"></i>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
              <button
                type="button"
                className="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                <i className={`fas fa-${showPassword ? 'eye-slash' : 'eye'}`}></i>
              </button>
            </div>
          </div>

          <button type="submit" className="submit-btn">
            {isRegister ? "Ro'yxatdan o'tish" : 'Kirish'}
          </button>
        </form>

        <div className="switch-mode">
          {isRegister ? "Hisobingiz bormi?" : "Hisobingiz yo'qmi?"}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
              setSuccess('');
            }}
          >
            {isRegister ? 'Kirish' : "Ro'yxatdan o'tish"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}