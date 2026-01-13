import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getScheduleById, updateCalendarEvent, deleteCalendarEvent } from '../services/calendarService';
import { getSubTasksBySchedule, createSubTask, updateSubTask, deleteSubTask } from '../services/subTaskService';
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
    category: '',
    priority_score: 5,
    estimated_minute: null,
  });

  // 할 일 목록 관련 상태
  const [subTasks, setSubTasks] = useState([]);
  const [newSubTaskTitle, setNewSubTaskTitle] = useState('');
  const [newSubTaskDate, setNewSubTaskDate] = useState('');
  const [newSubTaskEstimatedMinute, setNewSubTaskEstimatedMinute] = useState(60);
  const [isAddingSubTask, setIsAddingSubTask] = useState(false);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [editingTaskTitle, setEditingTaskTitle] = useState('');
  const [editingTaskCategory, setEditingTaskCategory] = useState('');
  
  // 스와이프 및 더블탭을 위한 상태
  const [swipeStates, setSwipeStates] = useState({});
  const [lastTap, setLastTap] = useState(0);
  const dragStartRef = useRef({});
  const dragCurrentRef = useRef({});

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
        
        // 할 일 목록 조회
        await fetchSubTasks();
      } catch (err) {
        console.error('일정 조회 실패:', err);
        setError(err.message || '일정을 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSchedule();
  }, [id]);

  // 할 일 목록 조회
  const fetchSubTasks = async () => {
    try {
      const tasks = await getSubTasksBySchedule(id);
      console.log('조회된 할 일 목록:', tasks);
      setSubTasks(tasks);
    } catch (err) {
      console.error('할 일 목록 조회 실패:', err);
    }
  };

  // 할 일 추가
  const handleAddSubTask = async () => {
    if (!newSubTaskTitle.trim()) return;
    if (!newSubTaskDate) {
      alert('날짜를 선택해주세요.');
      return;
    }
    
    try {
      await createSubTask({
        scheduleId: id,
        title: newSubTaskTitle.trim(),
        date: newSubTaskDate,
        estimatedMinute: newSubTaskEstimatedMinute || 60,
      });
      
      setNewSubTaskTitle('');
      setNewSubTaskDate('');
      setNewSubTaskEstimatedMinute(60);
      setIsAddingSubTask(false);
      await fetchSubTasks();
    } catch (err) {
      console.error('할 일 추가 실패:', err);
      alert('할 일 추가에 실패했습니다.');
    }
  };

  // 할 일 편집 시작
  const handleEditSubTask = (task) => {
    setEditingTaskId(task.id);
    setEditingTaskTitle(task.title);
    setEditingTaskCategory(task.category || '학업');
  };

  // 할 일 편집 저장
  const handleSaveSubTask = async (taskId) => {
    if (!editingTaskTitle.trim()) return;
    
    try {
      await updateSubTask(taskId, {
        title: editingTaskTitle.trim(),
        category: editingTaskCategory,
      });
      
      setEditingTaskId(null);
      setEditingTaskTitle('');
      setEditingTaskCategory('');
      await fetchSubTasks();
    } catch (err) {
      console.error('할 일 수정 실패:', err);
      alert('할 일 수정에 실패했습니다.');
    }
  };

  // 할 일 편집 취소
  const handleCancelEditSubTask = () => {
    setEditingTaskId(null);
    setEditingTaskTitle('');
    setEditingTaskCategory('');
  };

  // 더블탭 감지 (편집 모드 진입)
  const handleDoubleTap = (task) => {
    const now = Date.now();
    if (now - lastTap < 300) {
      // 더블탭 감지됨 - 편집 모드 진입
      handleEditSubTask(task);
    }
    setLastTap(now);
  };

  // 스와이프 시작
  const handleSwipeStart = (taskId, clientX) => {
    dragStartRef.current[taskId] = clientX;
    dragCurrentRef.current[taskId] = clientX;
  };

  // 스와이프 이동
  const handleSwipeMove = (taskId, clientX) => {
    if (!dragStartRef.current[taskId]) return;
    
    dragCurrentRef.current[taskId] = clientX;
    const diff = clientX - dragStartRef.current[taskId];
    
    // 왼쪽으로만 스와이프 허용
    if (diff < 0) {
      setSwipeStates(prev => ({
        ...prev,
        [taskId]: Math.max(diff, -100)
      }));
    }
  };

  // 스와이프 종료
  const handleSwipeEnd = (taskId) => {
    const offset = swipeStates[taskId] || 0;
    
    if (offset < -60) {
      // 삭제 실행
      handleDeleteSubTask(taskId);
    }
    
    // 스와이프 상태 초기화
    setSwipeStates(prev => {
      const newState = { ...prev };
      delete newState[taskId];
      return newState;
    });
    
    delete dragStartRef.current[taskId];
    delete dragCurrentRef.current[taskId];
  };

  // 할 일 완료 상태 토글
  const handleToggleSubTask = async (taskId, completed) => {
    try {
      await updateSubTask(taskId, { completed: !completed });
      await fetchSubTasks();
    } catch (err) {
      console.error('할 일 상태 변경 실패:', err);
      alert('할 일 상태 변경에 실패했습니다.');
    }
  };

  // 할 일 삭제
  const handleDeleteSubTask = async (taskId) => {
    if (!window.confirm('이 할 일을 삭제하시겠습니까?')) return;
    
    try {
      await deleteSubTask(taskId);
      await fetchSubTasks();
    } catch (err) {
      console.error('할 일 삭제 실패:', err);
      alert('할 일 삭제에 실패했습니다.');
    }
  };

  // 우선순위 표시 함수
  const getPriorityLabel = (score) => {
    if (!score) return '보통';
    if (score >= 7) return '높음';
    if (score >= 4) return '보통';
    return '낮음';
  };

  const getPriorityColor = (score) => {
    if (!score) return '#6b7280';
    if (score >= 7) return '#ef4444';
    if (score >= 4) return '#f59e0b';
    return '#10b981';
  };

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
                <label>카테고리</label>
                <input
                  type="text"
                  name="category"
                  value={formData.category || ''}
                  onChange={handleInputChange}
                  placeholder="예: 과제, 회의, 개인"
                />
              </div>

              <div className="schedule-detail__field">
                <label>우선순위 (1-10)</label>
                <input
                  type="number"
                  name="priority_score"
                  value={formData.priority_score || 5}
                  onChange={handleInputChange}
                  min="1"
                  max="10"
                />
              </div>

              <div className="schedule-detail__field">
                <label>예상 소요 시간 (분)</label>
                <input
                  type="number"
                  name="estimated_minute"
                  value={formData.estimated_minute || ''}
                  onChange={handleInputChange}
                  placeholder="예: 120 (2시간)"
                  min="0"
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
                {schedule.category && (
                  <div className="schedule-detail__info-row">
                    <span className="schedule-detail__info-label">🏷️ 카테고리</span>
                    <span className="schedule-detail__info-value">{schedule.category}</span>
                  </div>
                )}
                <div className="schedule-detail__info-row">
                  <span className="schedule-detail__info-label">🎯 우선순위</span>
                  <span 
                    className="schedule-detail__info-value"
                    style={{ 
                      color: getPriorityColor(schedule.priority_score),
                      fontWeight: 'bold'
                    }}
                  >
                    {getPriorityLabel(schedule.priority_score)} ({schedule.priority_score || 0}/10)
                  </span>
                </div>
                {schedule.estimated_minute && (
                  <div className="schedule-detail__info-row">
                    <span className="schedule-detail__info-label">⏱️ 예상 소요 시간</span>
                    <span className="schedule-detail__info-value">
                      {Math.floor(schedule.estimated_minute / 60)}시간 {schedule.estimated_minute % 60}분
                    </span>
                  </div>
                )}
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

          {/* 할 일 체크리스트 */}
          <div className="schedule-detail__subtasks">
            <div className="schedule-detail__subtasks-header">
              <h3>할 일 목록</h3>
              {!isAddingSubTask && (
                <button 
                  className="schedule-detail__add-subtask-btn"
                  onClick={() => setIsAddingSubTask(true)}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                </button>
              )}
            </div>

            {isAddingSubTask && (
              <div className="schedule-detail__subtask-input">
                <input
                  type="text"
                  placeholder="할 일 제목"
                  value={newSubTaskTitle}
                  onChange={(e) => setNewSubTaskTitle(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddSubTask()}
                  autoFocus
                />
                <input
                  type="date"
                  placeholder="날짜"
                  value={newSubTaskDate}
                  onChange={(e) => setNewSubTaskDate(e.target.value)}
                  required
                />
                <input
                  type="number"
                  placeholder="예상 시간 (분)"
                  value={newSubTaskEstimatedMinute}
                  onChange={(e) => setNewSubTaskEstimatedMinute(parseInt(e.target.value) || 60)}
                  min="5"
                  step="5"
                />
                <div className="schedule-detail__subtask-actions">
                  <button onClick={handleAddSubTask}>추가</button>
                  <button onClick={() => {
                    setIsAddingSubTask(false);
                    setNewSubTaskTitle('');
                    setNewSubTaskDate('');
                    setNewSubTaskEstimatedMinute(60);
                  }}>취소</button>
                </div>
              </div>
            )}

            {subTasks.length === 0 ? (
              <p className="schedule-detail__subtasks-empty">등록된 할 일이 없습니다.</p>
            ) : (
              <ul className="schedule-detail__subtasks-list">
                {subTasks.map((task) => (
                  <li key={task.id} className="schedule-detail__subtask-wrapper">
                    {editingTaskId === task.id ? (
                      <div className="schedule-detail__subtask-edit-mode">
                        <input
                          type="text"
                          value={editingTaskTitle}
                          onChange={(e) => setEditingTaskTitle(e.target.value)}
                          className="schedule-detail__subtask-edit-input"
                          onKeyPress={(e) => e.key === 'Enter' && handleSaveSubTask(task.id)}
                          autoFocus
                        />
                        <select
                          value={editingTaskCategory}
                          onChange={(e) => setEditingTaskCategory(e.target.value)}
                          className="schedule-detail__subtask-edit-select"
                        >
                          <option value="학업">학업</option>
                          <option value="업무">업무</option>
                          <option value="개인">개인</option>
                          <option value="기타">기타</option>
                        </select>
                        <div className="schedule-detail__subtask-edit-actions">
                          <button onClick={() => handleSaveSubTask(task.id)}>저장</button>
                          <button onClick={handleCancelEditSubTask}>취소</button>
                        </div>
                      </div>
                    ) : (
                      <>
                        {/* 삭제 배경 */}
                        <div 
                          className="schedule-detail__subtask-delete-bg"
                          style={{ 
                            width: (swipeStates[task.id] || 0) < 0 ? Math.abs(swipeStates[task.id] || 0) : 0,
                            opacity: (swipeStates[task.id] || 0) < 0 ? 1 : 0 
                          }}
                        >
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                            <path d="M3 6h18M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                          </svg>
                          <span>삭제</span>
                        </div>
                        
                        <div 
                          className="schedule-detail__subtask-item"
                          style={{ transform: `translateX(${swipeStates[task.id] || 0}px)` }}
                          onMouseDown={(e) => handleSwipeStart(task.id, e.clientX)}
                          onMouseMove={(e) => handleSwipeMove(task.id, e.clientX)}
                          onMouseUp={() => handleSwipeEnd(task.id)}
                          onMouseLeave={() => handleSwipeEnd(task.id)}
                          onTouchStart={(e) => handleSwipeStart(task.id, e.touches[0].clientX)}
                          onTouchMove={(e) => handleSwipeMove(task.id, e.touches[0].clientX)}
                          onTouchEnd={() => handleSwipeEnd(task.id)}
                          onClick={() => handleDoubleTap(task)}
                        >
                          <label className="schedule-detail__subtask-label">
                            <input
                              type="checkbox"
                              checked={task.completed || false}
                              onChange={(e) => {
                                e.stopPropagation();
                                handleToggleSubTask(task.id, task.completed);
                              }}
                              onClick={(e) => e.stopPropagation()}
                            />
                            <span className={task.completed ? 'completed' : ''}>
                              {task.title}
                              {task.category && (
                                <span className="schedule-detail__subtask-category">
                                  [{task.category}]
                                </span>
                              )}
                            </span>
                          </label>
                        </div>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
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
