import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTimetable } from '../hooks/useTimetable';
import {
  getLectureColor,
  getLectureTextColor,
} from '../services/lectureService';
import { formatDate } from '../utils/dateUtils';
import Modal from '../components/common/Modal';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import './Timetable.css';

// 요일 라벨 (백엔드: 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일)
const DAY_LABELS = {
  0: '월',
  1: '화',
  2: '수',
  3: '목',
  4: '금',
  5: '토',
  6: '일',
};

// 기본 시간 슬롯
const DEFAULT_TIME_SLOT = { day: 1, start_time: '09:00', end_time: '10:30' };
const MAX_TIME_SLOTS = 7;

const Timetable = () => {
  const navigate = useNavigate();
  const {
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

  // 강의 추가용 폼 데이터 (시간 슬롯 배열 지원)
  const [formData, setFormData] = useState({
    title: '',
    start_day: '',
    end_day: '',
    timeSlots: [{ ...DEFAULT_TIME_SLOT }],
  });

  // 강의 편집용 폼 데이터 (단일 시간)
  const [editFormData, setEditFormData] = useState({
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

  // 폼 초기화 (추가용)
  const resetForm = () => {
    const today = new Date();
    const threeMonthsLater = new Date();
    threeMonthsLater.setMonth(threeMonthsLater.getMonth() + 3);

    setFormData({
      title: '',
      start_day: formatDate(today, 'YYYY-MM-DD'),
      end_day: formatDate(threeMonthsLater, 'YYYY-MM-DD'),
      timeSlots: [{ ...DEFAULT_TIME_SLOT }],
    });
  };

  // 시간 슬롯 추가
  const addTimeSlot = () => {
    if (formData.timeSlots.length >= MAX_TIME_SLOTS) {
      alert(`시간 슬롯은 최대 ${MAX_TIME_SLOTS}개까지 추가할 수 있습니다.`);
      return;
    }
    setFormData((prev) => ({
      ...prev,
      timeSlots: [...prev.timeSlots, { ...DEFAULT_TIME_SLOT }],
    }));
  };

  // 시간 슬롯 삭제
  const removeTimeSlot = (index) => {
    if (formData.timeSlots.length <= 1) {
      alert('최소 1개의 시간 슬롯이 필요합니다.');
      return;
    }
    setFormData((prev) => ({
      ...prev,
      timeSlots: prev.timeSlots.filter((_, i) => i !== index),
    }));
  };

  // 시간 슬롯 업데이트
  const updateTimeSlot = (index, field, value) => {
    setFormData((prev) => ({
      ...prev,
      timeSlots: prev.timeSlots.map((slot, i) =>
        i === index ? { ...slot, [field]: value } : slot
      ),
    }));
  };

  // 강의 추가 모달 열기
  const handleOpenAddModal = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  // 강의 편집 모달 열기
  const handleOpenEditModal = (lecture) => {
    if (!lecture || (!lecture.id && !lecture.lecture_id)) {
      console.error('Invalid lecture data:', lecture);
      return;
    }
    // lecture_id 또는 id 사용
    const lectureWithId = {
      ...lecture,
      id: lecture.id || lecture.lecture_id,
    };
    setSelectedLecture(lectureWithId);
    setEditFormData({
      title: lecture.title || '',
      start_time: lecture.start_time?.slice(0, 5) || '09:00',
      end_time: lecture.end_time?.slice(0, 5) || '10:30',
      start_day: lecture.start_day || '',
      end_day: lecture.end_day || '',
      week: lecture.week || [],
    });
    setIsEditModalOpen(true);
  };

  // 요일 토글 (편집용)
  const handleDayToggle = (day) => {
    setEditFormData((prev) => ({
      ...prev,
      week: prev.week.includes(day)
        ? prev.week.filter((d) => d !== day)
        : [...prev.week, day].sort((a, b) => a - b),
    }));
  };

  // 시간 유효성 검사
  const validateTimeSlot = (slot) => {
    const startParts = slot.start_time.split(':');
    const endParts = slot.end_time.split(':');
    const startMinutes = parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
    const endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);
    return endMinutes > startMinutes;
  };

  // 강의 추가 처리 (여러 시간 슬롯)
  const handleAddLecture = async () => {
    // 유효성 검사
    if (!formData.title.trim()) {
      alert('강의명을 입력해주세요.');
      return;
    }

    if (!formData.start_day || !formData.end_day) {
      alert('시작 날짜와 종료 날짜를 입력해주세요.');
      return;
    }

    if (formData.timeSlots.length === 0) {
      alert('최소 1개의 시간을 추가해주세요.');
      return;
    }

    // 각 시간 슬롯 유효성 검사
    for (let i = 0; i < formData.timeSlots.length; i++) {
      const slot = formData.timeSlots[i];
      if (!validateTimeSlot(slot)) {
        alert(`${i + 1}번째 시간의 종료 시간이 시작 시간보다 빠릅니다.`);
        return;
      }
    }

    setIsSubmitting(true);
    try {
      // 각 시간 슬롯별로 강의 생성
      for (const slot of formData.timeSlots) {
        await addLecture({
          title: formData.title,
          start_time: slot.start_time + ':00',
          end_time: slot.end_time + ':00',
          start_day: formData.start_day,
          end_day: formData.end_day,
          week: [slot.day],
        });
      }
      setIsAddModalOpen(false);
      resetForm();
    } catch (err) {
      console.error('Add lecture error:', err);
      alert(err.message || '강의 추가에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 강의 수정 처리
  const handleEditLecture = async () => {
    if (!formData.title?.trim() && !editFormData.title?.trim()) {
      alert('강의명을 입력해주세요.');
      return;
    }

    if (!selectedLecture?.id) {
      alert('선택된 강의가 없습니다.');
      return;
    }

    // 시간 유효성 검사
    const startParts = editFormData.start_time.split(':');
    const endParts = editFormData.end_time.split(':');
    const startMinutes = parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
    const endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);

    if (endMinutes <= startMinutes) {
      alert('종료 시간이 시작 시간보다 빠릅니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      await editLecture(selectedLecture.id, {
        ...editFormData,
        start_time: editFormData.start_time + ':00',
        end_time: editFormData.end_time + ':00',
      });
      setIsEditModalOpen(false);
      setSelectedLecture(null);
    } catch (err) {
      console.error('Edit lecture error:', err);
      alert(err.message || '강의 수정에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 강의 삭제 처리
  const handleDeleteLecture = async () => {
    if (!selectedLecture?.id) {
      alert('선택된 강의가 없습니다.');
      return;
    }

    if (!window.confirm('이 강의를 삭제하시겠습니까?')) return;

    setIsSubmitting(true);
    try {
      await removeLecture(selectedLecture.id);
      setIsEditModalOpen(false);
      setSelectedLecture(null);
    } catch (err) {
      console.error('Delete lecture error:', err);
      alert(err.message || '강의 삭제에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 특정 시간대의 강의 찾기
  const getLectureAtTime = (dayOfWeek, hour) => {
    const dayLectures = getLecturesForDay(dayOfWeek);
    if (!Array.isArray(dayLectures)) return [];

    return dayLectures.filter((lecture) => {
      if (!lecture?.start_time || !lecture?.end_time) return false;

      const startHour = parseInt(lecture.start_time.split(':')[0], 10);
      const endHour = parseInt(lecture.end_time.split(':')[0], 10);
      const endMinute = parseInt(lecture.end_time.split(':')[1], 10);
      const effectiveEndHour = endMinute > 0 ? endHour : endHour - 1;
      return hour >= startHour && hour <= effectiveEndHour;
    });
  };

  // 강의 셀 높이 계산 (시간 단위)
  const getLectureDuration = (lecture) => {
    if (!lecture?.start_time || !lecture?.end_time) return 1;

    const startHour = parseInt(lecture.start_time.split(':')[0], 10);
    const startMinute = parseInt(lecture.start_time.split(':')[1], 10);
    const endHour = parseInt(lecture.end_time.split(':')[0], 10);
    const endMinute = parseInt(lecture.end_time.split(':')[1], 10);

    return (endHour * 60 + endMinute - startHour * 60 - startMinute) / 60;
  };

  // 강의가 해당 시간의 시작인지 확인
  const isLectureStart = (lecture, hour) => {
    if (!lecture?.start_time) return false;
    const startHour = parseInt(lecture.start_time.split(':')[0], 10);
    return startHour === hour;
  };

  // 뒤로가기
  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className="timetable">
      {/* 헤더 - FullCalendar 스타일 */}
      <header className="timetable__header">
        <button
          className="timetable__back-btn"
          onClick={handleBack}
          aria-label="뒤로 가기"
        >
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
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>

        <h1 className="timetable__title">이번 주 시간표</h1>

        <button
          className="timetable__add-btn"
          onClick={handleOpenAddModal}
          aria-label="강의 추가"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </header>

      {/* 네비게이션 바 */}
      <div className="timetable__nav-bar">
        <div className="timetable__nav">
          <button className="timetable__nav-btn" onClick={goToPreviousWeek}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <span className="timetable__nav-title">
            {year}년 {weekNumber}주
          </span>
          <button className="timetable__nav-btn" onClick={goToNextWeek}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>
        <button className="timetable__today-btn" onClick={goToToday}>
          오늘
        </button>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="timetable__error">
          <span>⚠️ {error}</span>
          <button onClick={() => window.location.reload()}>새로고침</button>
        </div>
      )}

      {/* 시간표 그리드 */}
      <div className="timetable__grid-container">
        <div className="timetable__grid">
          {/* 헤더 행 (요일) */}
          <div className="timetable__row timetable__row--header">
            <div className="timetable__cell timetable__cell--time"></div>
            {displayDays.map((day) => {
              const date = getDateForDay(day);
              const isToday =
                date &&
                formatDate(date, 'YYYY-MM-DD') ===
                  formatDate(new Date(), 'YYYY-MM-DD');
              return (
                <div
                  key={day}
                  className={`timetable__cell timetable__cell--header ${
                    isToday ? 'timetable__cell--today' : ''
                  }`}
                >
                  <span className="timetable__day-label">
                    {DAY_LABELS[day]}
                  </span>
                  <span className="timetable__day-date">
                    {date?.getDate() || ''}
                  </span>
                </div>
              );
            })}
          </div>

          {/* 시간 행 */}
          {hours.map((hour) => (
            <div key={hour} className="timetable__row">
              <div className="timetable__cell timetable__cell--time">
                <span>{String(hour).padStart(2, '0')}:00</span>
              </div>
              {displayDays.map((day) => {
                const lecturesAtTime = getLectureAtTime(day, hour);
                const date = getDateForDay(day);
                const isToday =
                  date &&
                  formatDate(date, 'YYYY-MM-DD') ===
                    formatDate(new Date(), 'YYYY-MM-DD');

                return (
                  <div
                    key={`${day}-${hour}`}
                    className={`timetable__cell ${
                      isToday ? 'timetable__cell--today-col' : ''
                    }`}
                  >
                    {lecturesAtTime.map((lecture) => {
                      if (!isLectureStart(lecture, hour)) return null;

                      const duration = getLectureDuration(lecture);
                      const bgColor = getLectureColor(lecture.title || '');
                      const textColor = getLectureTextColor(bgColor);
                      const lectureKey = lecture.lecture_id || lecture.id;

                      return (
                        <div
                          key={lectureKey}
                          className="timetable__lecture"
                          style={{
                            backgroundColor: bgColor,
                            color: textColor,
                            height: `calc(${duration * 100}% + ${
                              (duration - 1) * 1
                            }px)`,
                          }}
                          onClick={() => handleOpenEditModal(lecture)}
                        >
                          <span className="timetable__lecture-title">
                            {lecture.title}
                          </span>
                          <span className="timetable__lecture-time">
                            {lecture.start_time?.slice(0, 5)} -{' '}
                            {lecture.end_time?.slice(0, 5)}
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
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, title: e.target.value }))
            }
            placeholder="예: 데이터베이스 실습"
          />

          <div className="timetable__form-row">
            <Input
              label="시작 날짜"
              type="date"
              value={formData.start_day}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, start_day: e.target.value }))
              }
            />
            <Input
              label="종료 날짜"
              type="date"
              value={formData.end_day}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, end_day: e.target.value }))
              }
            />
          </div>

          {/* 시간 슬롯 목록 */}
          <div className="timetable__time-slots">
            <div className="timetable__time-slots-header">
              <label className="timetable__form-label">시간 설정</label>
              <span className="timetable__time-slots-count">
                {formData.timeSlots.length}/{MAX_TIME_SLOTS}
              </span>
            </div>

            {formData.timeSlots.map((slot, index) => (
              <div key={index} className="timetable__time-slot">
                <div className="timetable__time-slot-header">
                  <span className="timetable__time-slot-number">
                    {index + 1}
                  </span>
                  {formData.timeSlots.length > 1 && (
                    <button
                      type="button"
                      className="timetable__time-slot-remove"
                      onClick={() => removeTimeSlot(index)}
                      aria-label="시간 삭제"
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="timetable__time-slot-content">
                  <div className="timetable__time-slot-day">
                    <label className="timetable__form-label-sm">요일</label>
                    <select
                      value={slot.day}
                      onChange={(e) =>
                        updateTimeSlot(index, 'day', parseInt(e.target.value))
                      }
                      className="timetable__select"
                    >
                      {[1, 2, 3, 4, 5, 6, 0].map((day) => (
                        <option key={day} value={day}>
                          {DAY_LABELS[day]}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="timetable__time-slot-times">
                    <div className="timetable__time-slot-time">
                      <label className="timetable__form-label-sm">시작</label>
                      <input
                        type="time"
                        value={slot.start_time}
                        onChange={(e) =>
                          updateTimeSlot(index, 'start_time', e.target.value)
                        }
                        className="timetable__time-input"
                      />
                    </div>
                    <span className="timetable__time-slot-separator">~</span>
                    <div className="timetable__time-slot-time">
                      <label className="timetable__form-label-sm">종료</label>
                      <input
                        type="time"
                        value={slot.end_time}
                        onChange={(e) =>
                          updateTimeSlot(index, 'end_time', e.target.value)
                        }
                        className="timetable__time-input"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* 시간 추가 버튼 */}
            {formData.timeSlots.length < MAX_TIME_SLOTS && (
              <button
                type="button"
                className="timetable__add-time-btn"
                onClick={addTimeSlot}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                <span>시간 추가</span>
              </button>
            )}
          </div>

          <div className="timetable__modal-actions">
            <Button
              onClick={handleAddLecture}
              disabled={isSubmitting}
              fullWidth
            >
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
            value={editFormData.title}
            onChange={(e) =>
              setEditFormData((prev) => ({ ...prev, title: e.target.value }))
            }
            placeholder="예: 데이터베이스 실습"
          />

          <div className="timetable__form-row">
            <Input
              label="시작 시간"
              type="time"
              value={editFormData.start_time}
              onChange={(e) =>
                setEditFormData((prev) => ({
                  ...prev,
                  start_time: e.target.value,
                }))
              }
            />
            <Input
              label="종료 시간"
              type="time"
              value={editFormData.end_time}
              onChange={(e) =>
                setEditFormData((prev) => ({
                  ...prev,
                  end_time: e.target.value,
                }))
              }
            />
          </div>

          <div className="timetable__form-row">
            <Input
              label="시작 날짜"
              type="date"
              value={editFormData.start_day}
              onChange={(e) =>
                setEditFormData((prev) => ({
                  ...prev,
                  start_day: e.target.value,
                }))
              }
            />
            <Input
              label="종료 날짜"
              type="date"
              value={editFormData.end_day}
              onChange={(e) =>
                setEditFormData((prev) => ({
                  ...prev,
                  end_day: e.target.value,
                }))
              }
            />
          </div>

          <div className="timetable__form-group">
            <label className="timetable__form-label">요일 선택</label>
            <div className="timetable__day-selector">
              {[1, 2, 3, 4, 5, 6, 0].map((day) => (
                <button
                  key={day}
                  type="button"
                  className={`timetable__day-btn ${
                    editFormData.week.includes(day)
                      ? 'timetable__day-btn--selected'
                      : ''
                  }`}
                  onClick={() => handleDayToggle(day)}
                >
                  {DAY_LABELS[day]}
                </button>
              ))}
            </div>
          </div>

          <div className="timetable__modal-actions timetable__modal-actions--edit">
            <Button
              variant="danger"
              onClick={handleDeleteLecture}
              disabled={isSubmitting}
            >
              삭제
            </Button>
            <Button onClick={handleEditLecture} disabled={isSubmitting}>
              {isSubmitting ? '저장 중...' : '저장'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Timetable;
