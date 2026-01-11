import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Button from '../components/common/Button';
import './ScheduleDetail.css';

const ScheduleDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [schedule, setSchedule] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    date: '',
    startTime: '',
    endTime: '',
    isAllDay: false,
  });

  // TODO: Fetch schedule detail by ID
  useEffect(() => {
    const fetchSchedule = async () => {
      // 임시 데이터 (실제로는 calendarService에서 가져옴)
      const mockSchedule = {
        id,
        title: '팀 미팅',
        description: '프로젝트 진행 상황 공유',
        date: '2026-01-12',
        startTime: '14:00',
        endTime: '15:00',
        isAllDay: false,
        type: 'schedule',
      };
      setSchedule(mockSchedule);
      setFormData(mockSchedule);
    };
    
    fetchSchedule();
  }, [id]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    // TODO: updateCalendarEvent 호출
    console.log('일정 저장:', formData);
    setSchedule(formData);
    setIsEditing(false);
  };

  const handleDelete = () => {
    if (window.confirm('이 일정을 삭제하시겠습니까?')) {
      // TODO: deleteCalendarEvent 호출
      console.log('일정 삭제:', id);
      navigate(-1);
    }
  };

  if (!schedule) {
    return (
      <div className="schedule-detail">
        <div className="schedule-detail__container">
          <p>로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="schedule-detail">
      <div className="schedule-detail__container">
        <div className="schedule-detail__header">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            뒤로
          </Button>
          <h1 className="schedule-detail__title">일정 상세</h1>
          <div className="schedule-detail__actions">
            {isEditing ? (
              <Button variant="primary" onClick={handleSave}>
                저장
              </Button>
            ) : (
              <Button variant="ghost" onClick={() => setIsEditing(true)}>
                편집
              </Button>
            )}
          </div>
        </div>

        <div className="schedule-detail__content">
          {isEditing ? (
            <form className="schedule-detail__form">
              <div className="schedule-detail__field">
                <label>제목</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="일정 제목"
                />
              </div>

              <div className="schedule-detail__field">
                <label>날짜</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleInputChange}
                />
              </div>

              {/* 종일 토글 */}
              <div className="schedule-detail__toggle-row">
                <span className="schedule-detail__toggle-label">종일</span>
                <label className="schedule-detail__toggle">
                  <input 
                    type="checkbox" 
                    checked={formData.isAllDay} 
                    onChange={(e) => setFormData(prev => ({ ...prev, isAllDay: e.target.checked }))} 
                  />
                  <span className="schedule-detail__toggle-slider" />
                </label>
              </div>

              {!formData.isAllDay && (
              <div className="schedule-detail__time-row">
                <div className="schedule-detail__field">
                  <label>시작 시간</label>
                  <input
                    type="time"
                    name="startTime"
                    value={formData.startTime}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="schedule-detail__field">
                  <label>종료 시간</label>
                  <input
                    type="time"
                    name="endTime"
                    value={formData.endTime}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
              )}

              <div className="schedule-detail__field">
                <label>메모</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="메모 (선택사항)"
                  rows={4}
                />
              </div>
            </form>
          ) : (
            <div className="schedule-detail__view">
              <div className="schedule-detail__info">
                <h2 className="schedule-detail__info-title">{schedule.title}</h2>
                <div className="schedule-detail__info-row">
                  <span className="schedule-detail__info-label">📅 날짜</span>
                  <span className="schedule-detail__info-value">{schedule.date}</span>
                </div>
                {schedule.isAllDay ? (
                  <div className="schedule-detail__info-row">
                    <span className="schedule-detail__info-label">⏰ 시간</span>
                    <span className="schedule-detail__info-value">종일</span>
                  </div>
                ) : (
                  <div className="schedule-detail__info-row">
                    <span className="schedule-detail__info-label">🕐 시간</span>
                    <span className="schedule-detail__info-value">
                      {schedule.startTime} - {schedule.endTime}
                    </span>
                  </div>
                )}
                {schedule.description && (
                  <div className="schedule-detail__info-row">
                    <span className="schedule-detail__info-label">📝 메모</span>
                    <span className="schedule-detail__info-value">{schedule.description}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="schedule-detail__footer">
          <Button variant="danger" onClick={handleDelete}>
            일정 삭제
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ScheduleDetail;
