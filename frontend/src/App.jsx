import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Navigation from './components/layout/Navigation';
import Home from './pages/Home';
import TaskDetail from './pages/TaskDetail';
import Archive from './pages/Archive';
import Notifications from './pages/Notifications';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          {/* 헤더가 있는 레이아웃 */}
          <Route
            path="/"
            element={
              <>
                <Header hasNotification={true} />
                <div className="app__layout">
                  <Navigation />
                  <div className="app__content">
                    <Home />
                  </div>
                </div>
              </>
            }
          />
          <Route
            path="/task/:id"
            element={
              <>
                <Header hasNotification={true} />
                <div className="app__layout">
                  <Navigation />
                  <div className="app__content">
                    <TaskDetail />
                  </div>
                </div>
              </>
            }
          />
          <Route
            path="/archive"
            element={
              <>
                <Header hasNotification={true} />
                <div className="app__layout">
                  <Navigation />
                  <div className="app__content">
                    <Archive />
                  </div>
                </div>
              </>
            }
          />
          
          {/* 독립 페이지 (헤더/네비게이션 없음) */}
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;