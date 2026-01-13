import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getScheduleById, updateCalendarEvent, deleteCalendarEvent } from '../services/calendarService';
import Button from '../components/common/Button';
import './ScheduleDetail.css';

const ScheduleDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    date: '',
    startDate: '',
    endDate: '',
    startTime: '',
    endTime: '',
    isAllDay: false,
  });

  // 일정 상세 정보 불러오기
  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getScheduleById(id);
        console.log('조회된 일정:', data);
        setSchedule(data);
        setFormData(data);
      } catch (err) {
        console.error('일정 조회 실패:', err);
        setError(err.message || '일정을 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSchedule();
  }, [id]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    try {
      console.log('일정 저장:', formData);
      await updateCalendarEvent(id, formData);
      setSchedule(formData);
      setIsEditing(false);
      alert('일정이 수정되었습니다.');
    } catch (err) {
      console.error('일정 수정 실패:', err);
      alert('일정 수정에 실패했습니다.');
    }
  };

  const handleDelete = async () => {
    if (window.confirm('이 일정을 삭제하시겠습니까?')) {
      try {
        console.log('일정 삭제:', id);
        await deleteCalendarEvent(id);
        alert('일정이 삭제되었습니다.');
        navigate(-1);
      } catch (err) {
        console.error('일정 삭제 실패:', err);
        alert('일정 삭제에 실패했습니다.');
      }
    }
  };

  if (loading) {
    return (
      <div className="schedule-detail">
        <div className="schedule-detail__container">
          <p>로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="schedule-detail">
        <div className="schedule-detail__container">
          <p>{error}</p>
          <Button onClick={() => navigate(-1)}>돌아가기</Button>
        </div>
      </div>
    );
  }

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
                <label>시작 날짜</label>
                <input
                  type="date"
                  name="startDate"
                  value={formData.startDate || formData.date}
                  onChange={handleInputChange}
                />
              </div>

              <div className="schedule-detail__field">
                <label>종료 날짜</label>
                <input
                  type="date"
                  name="endDate"
                  value={formData.endDate || formData.date}
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
