import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Navigation from './components/layout/Navigation';
import Home from './pages/Home';
import TaskDetail from './pages/TaskDetail';
import Archive from './pages/Archive';
import './App.css';

function App() {
  const user = null; // TODO: 실제 사용자 정보

  const handleNotificationClick = () => {
    console.log('Notification clicked');
  };

  return (
    <BrowserRouter>
      <div className="app">
        <Header user={user} onNotificationClick={handleNotificationClick} />
        <div className="app__layout">
          <Navigation />
          <div className="app__content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/task/:id" element={<TaskDetail />} />
              <Route path="/archive" element={<Archive />} />
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;