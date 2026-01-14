import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTimetable } from '../hooks/useTimetable';
import { getLectureColor, getLectureTextColor } from '../services/lectureService';
import { formatDate } from '../utils/dateUtils';
import Modal from '../components/common/Modal';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import Loading from '../components/common/Loading';
import './Timetable.css';

// 요일 라벨
const DAY_LABELS = {
  0: '일',
  1: '월',
  2: '화',
  3: '수',
  4: '목',
  5: '금',
  6: '토',
};

const Timetable = () => {
  const navigate = useNavigate();
  const {
    lectures,
    loading,
    error,
    year,
    weekNumber,
    displayDays,
    minHour,
    maxHour,
    addLecture,
    editLecture,
    removeLecture,
    goToPreviousWeek,
    goToNextWeek,
    goToToday,
    getLecturesForDay,
    getDateForDay,
  } = useTimetable();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedLecture, setSelectedLecture] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    start_time: '09:00',
    end_time: '10:30',
    start_day: '',
    end_day: '',
    week: [],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 시간 배열 생성 (minHour부터 maxHour까지)
  const hours = [];
  for (let h = minHour; h < maxHour; h++) {
    hours.push(h);
  }

  // 폼 초기화
  const resetForm = () => {
    const today = new Date();
    const threeMonthsLater = new Date();
    threeMonthsLater.setMonth(threeMonthsLater.getMonth() + 3);
    
    setFormData({
      title: '',
      start_time: '09:00',
      end_time: '10:30',
      start_day: formatDate(today, 'YYYY-MM-DD'),
      end_day: formatDate(threeMonthsLater, 'YYYY-MM-DD'),
      week: [],
    });
  };

  // 강의 추가 모달 열기
  const handleOpenAddModal = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  // 강의 편집 모달 열기
  const handleOpenEditModal = (lecture) => {
    setSelectedLecture(lecture);
    setFormData({
      title: lecture.title || '',
      start_time: lecture.start_time?.slice(0, 5) || '09:00',
      end_time: lecture.end_time?.slice(0, 5) || '10:30',
      start_day: lecture.start_day || '',
      end_day: lecture.end_day || '',
      week: lecture.week || [],
    });
    setIsEditModalOpen(true);
  };

  // 요일 토글
  const handleDayToggle = (day) => {
    setFormData(prev => ({
      ...prev,
      week: prev.week.includes(day)
        ? prev.week.filter(d => d !== day)
        : [...prev.week, day].sort((a, b) => a - b),
    }));
  };

  // 강의 추가 처리
  const handleAddLecture = async () => {
    if (!formData.title.trim()) {
      alert('강의명을 입력해주세요.');
      return;
    }
    if (formData.week.length === 0) {
      alert('요일을 선택해주세요.');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await addLecture({
        ...formData,
        start_time: formData.start_time + ':00',
        end_time: formData.end_time + ':00',
      });
      setIsAddModalOpen(false);
      resetForm();
    } catch (err) {
      alert(err.message || '강의 추가에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 강의 수정 처리
  const handleEditLecture = async () => {
    if (!formData.title.trim()) {
      alert('강의명을 입력해주세요.');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await editLecture(selectedLecture.id, {
        ...formData,
        start_time: formData.start_time + ':00',
        end_time: formData.end_time + ':00',
      });
      setIsEditModalOpen(false);
      setSelectedLecture(null);
    } catch (err) {
      alert(err.message || '강의 수정에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 강의 삭제 처리
  const handleDeleteLecture = async () => {
    if (!window.confirm('이 강의를 삭제하시겠습니까?')) return;
    
    setIsSubmitting(true);
    try {
      await removeLecture(selectedLecture.id);
      setIsEditModalOpen(false);
      setSelectedLecture(null);
    } catch (err) {
      alert(err.message || '강의 삭제에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 특정 시간대의 강의 찾기
  const getLectureAtTime = (dayOfWeek, hour) => {
    const dayLectures = getLecturesForDay(dayOfWeek);
    return dayLectures.filter(lecture => {
      const startHour = parseInt(lecture.start_time?.split(':')[0], 10);
      const endHour = parseInt(lecture.end_time?.split(':')[0], 10);
      const endMinute = parseInt(lecture.end_time?.split(':')[1], 10);
      const effectiveEndHour = endMinute > 0 ? endHour : endHour - 1;
      return hour >= startHour && hour <= effectiveEndHour;
    });
  };

  // 강의 셀 높이 계산 (시간 단위)
  const getLectureDuration = (lecture) => {
    const startHour = parseInt(lecture.start_time?.split(':')[0], 10);
    const startMinute = parseInt(lecture.start_time?.split(':')[1], 10);
    const endHour = parseInt(lecture.end_time?.split(':')[0], 10);
    const endMinute = parseInt(lecture.end_time?.split(':')[1], 10);
    
    return (endHour * 60 + endMinute - startHour * 60 - startMinute) / 60;
  };

  // 강의가 해당 시간의 시작인지 확인
  const isLectureStart = (lecture, hour) => {
    const startHour = parseInt(lecture.start_time?.split(':')[0], 10);
    return startHour === hour;
  };

  // 뒤로가기
  const handleBack = () => {
    navigate('/');
  };

  if (loading && lectures.length === 0) {
    return (
      <div className="timetable timetable--loading">
        <Loading text="시간표를 불러오는 중..." />
      </div>
    );
  }

  return (
    <div className="timetable">
      {/* 헤더 */}
      <div className="timetable__header">
        <button className="timetable__back-btn" onClick={handleBack}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        
        <div className="timetable__title-section">
          <div className="timetable__nav">
            <button className="timetable__nav-btn" onClick={goToPreviousWeek}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
            <h1 className="timetable__title">{year}년 {weekNumber}주</h1>
            <button className="timetable__nav-btn" onClick={goToNextWeek}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
          </div>
          <button className="timetable__today-btn" onClick={goToToday}>
            오늘
          </button>
        </div>

        <button className="timetable__add-btn" onClick={handleOpenAddModal}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="timetable__error">
          {error}
        </div>
      )}

      {/* 시간표 그리드 */}
      <div className="timetable__grid-container">
        <div className="timetable__grid">
          {/* 헤더 행 (요일) */}
          <div className="timetable__row timetable__row--header">
            <div className="timetable__cell timetable__cell--time"></div>
            {displayDays.map(day => {
              const date = getDateForDay(day);
              const isToday = formatDate(date, 'YYYY-MM-DD') === formatDate(new Date(), 'YYYY-MM-DD');
              return (
                <div 
                  key={day} 
                  className={`timetable__cell timetable__cell--header ${isToday ? 'timetable__cell--today' : ''}`}
                >
                  <span className="timetable__day-label">{DAY_LABELS[day]}</span>
                  <span className="timetable__day-date">{date.getDate()}</span>
                </div>
              );
            })}
          </div>

          {/* 시간 행 */}
          {hours.map(hour => (
            <div key={hour} className="timetable__row">
              <div className="timetable__cell timetable__cell--time">
                <span>{String(hour).padStart(2, '0')}:00</span>
              </div>
              {displayDays.map(day => {
                const lecturesAtTime = getLectureAtTime(day, hour);
                const date = getDateForDay(day);
                const isToday = formatDate(date, 'YYYY-MM-DD') === formatDate(new Date(), 'YYYY-MM-DD');
                
                return (
                  <div 
                    key={`${day}-${hour}`} 
                    className={`timetable__cell ${isToday ? 'timetable__cell--today-col' : ''}`}
                  >
                    {lecturesAtTime.map(lecture => {
                      if (!isLectureStart(lecture, hour)) return null;
                      
                      const duration = getLectureDuration(lecture);
                      const bgColor = getLectureColor(lecture.title);
                      const textColor = getLectureTextColor(bgColor);
                      
                      return (
                        <div
                          key={lecture.id}
                          className="timetable__lecture"
                          style={{
                            backgroundColor: bgColor,
                            color: textColor,
                            height: `calc(${duration * 100}% + ${(duration - 1) * 1}px)`,
                          }}
                          onClick={() => handleOpenEditModal(lecture)}
                        >
                          <span className="timetable__lecture-title">{lecture.title}</span>
                          <span className="timetable__lecture-time">
                            {lecture.start_time?.slice(0, 5)} - {lecture.end_time?.slice(0, 5)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* 강의 추가 모달 */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="강의 추가"
      >
        <div className="timetable__modal-content">
          <Input
            label="강의명"
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            placeholder="예: 데이터베이스 실습"
          />
          
          <div className="timetable__form-row">
            <Input
              label="시작 시간"
              type="time"
              value={formData.start_time}
              onChange={(e) => setFormData(prev => ({ ...prev, start_time: e.target.value }))}
            />
            <Input
              label="종료 시간"
              type="time"
              value={formData.end_time}
              onChange={(e) => setFormData(prev => ({ ...prev, end_time: e.target.value }))}
            />
          </div>
          
          <div className="timetable__form-row">
            <Input
              label="시작 날짜"
              type="date"
              value={formData.start_day}
              onChange={(e) => setFormData(prev => ({ ...prev, start_day: e.target.value }))}
            />
            <Input
              label="종료 날짜"
              type="date"
              value={formData.end_day}
              onChange={(e) => setFormData(prev => ({ ...prev, end_day: e.target.value }))}
            />
          </div>

          <div className="timetable__form-group">
            <label className="timetable__form-label">요일 선택</label>
            <div className="timetable__day-selector">
              {[1, 2, 3, 4, 5, 6, 0].map(day => (
                <button
                  key={day}
                  type="button"
                  className={`timetable__day-btn ${formData.week.includes(day) ? 'timetable__day-btn--selected' : ''}`}
                  onClick={() => handleDayToggle(day)}
                >
                  {DAY_LABELS[day]}
                </button>
              ))}
            </div>
          </div>

          <div className="timetable__modal-actions">
            <Button variant="ghost" onClick={() => setIsAddModalOpen(false)}>
              취소
            </Button>
            <Button onClick={handleAddLecture} disabled={isSubmitting}>
              {isSubmitting ? '추가 중...' : '추가'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* 강의 편집 모달 */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="강의 편집"
      >
        <div className="timetable__modal-content">
          <Input
            label="강의명"
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            placeholder="예: 데이터베이스 실습"
          />
          
          <div className="timetable__form-row">
            <Input
              label="시작 시간"
              type="time"
              value={formData.start_time}
              onChange={(e) => setFormData(prev => ({ ...prev, start_time: e.target.value }))}
            />
            <Input
              label="종료 시간"
              type="time"
              value={formData.end_time}
              onChange={(e) => setFormData(prev => ({ ...prev, end_time: e.target.value }))}
            />
          </div>
          
          <div className="timetable__form-row">
            <Input
              label="시작 날짜"
              type="date"
              value={formData.start_day}
              onChange={(e) => setFormData(prev => ({ ...prev, start_day: e.target.value }))}
            />
            <Input
              label="종료 날짜"
              type="date"
              value={formData.end_day}
              onChange={(e) => setFormData(prev => ({ ...prev, end_day: e.target.value }))}
            />
          </div>

          <div className="timetable__form-group">
            <label className="timetable__form-label">요일 선택</label>
            <div className="timetable__day-selector">
              {[1, 2, 3, 4, 5, 6, 0].map(day => (
                <button
                  key={day}
                  type="button"
                  className={`timetable__day-btn ${formData.week.includes(day) ? 'timetable__day-btn--selected' : ''}`}
                  onClick={() => handleDayToggle(day)}
                >
                  {DAY_LABELS[day]}
                </button>
              ))}
            </div>
          </div>

          <div className="timetable__modal-actions timetable__modal-actions--edit">
            <Button variant="danger" onClick={handleDeleteLecture} disabled={isSubmitting}>
              삭제
            </Button>
            <div className="timetable__modal-actions-right">
              <Button variant="ghost" onClick={() => setIsEditModalOpen(false)}>
                취소
              </Button>
              <Button onClick={handleEditLecture} disabled={isSubmitting}>
                {isSubmitting ? '저장 중...' : '저장'}
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Timetable;
