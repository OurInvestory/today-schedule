import api from './api';

/**
 * 서브태스크(할일) 생성
 */
export const createSubTask = async (subTaskData) => {
  try {
    const payload = {
      schedule_id: subTaskData.scheduleId,
      title: subTaskData.title,
      date: subTaskData.date, // YYYY-MM-DD 형식
      estimated_minute: subTaskData.estimatedMinute || null,
      priority: subTaskData.priority || 'medium',
      category: subTaskData.category || 'other',
    };

    console.log('서브태스크 생성 요청:', payload);
    const response = await api.post('/api/sub-tasks', payload);
    console.log('서브태스크 생성 응답:', response.data);
    
    // 백엔드에서 200 OK를 반환하더라도 status가 500이면 실패
    if (response.data && response.data.status !== 200) {
      throw new Error(response.data.message || '서브태스크 생성에 실패했습니다.');
    }
    
    return response;
  } catch (error) {
    console.error('Failed to create sub-task:', error);
    throw error;
  }
};

/**
 * 서브태스크 목록 조회
 */
export const getSubTasks = async (from, to) => {
  try {
    const response = await api.get('/api/sub-tasks', {
      params: { from, to },
    });

    // 백엔드 응답을 프론트엔드 형식으로 변환
    return (response.data.data || []).map(task => ({
      ...task,
      id: task.sub_task_id || task.id,
      scheduleId: task.schedule_id,
      estimatedMinute: task.estimated_minute,
      completed: task.is_completed || false,
      category: task.category,
    }));
  } catch (error) {
    console.error('Failed to fetch sub-tasks:', error);
    throw error;
  }
};

/**
 * 서브태스크 수정
 */
export const updateSubTask = async (id, subTaskData) => {
  try {
    const payload = {};
    
    if (subTaskData.title !== undefined) payload.title = subTaskData.title;
    if (subTaskData.date !== undefined) payload.date = subTaskData.date;
    if (subTaskData.estimatedMinute !== undefined) payload.estimated_minute = subTaskData.estimatedMinute;
    if (subTaskData.completed !== undefined) payload.is_done = subTaskData.completed;
    if (subTaskData.category !== undefined) payload.category = subTaskData.category;
    if (subTaskData.priority !== undefined) payload.priority = subTaskData.priority;

    console.log('서브태스크 수정 요청:', { id, payload });
    const response = await api.put(`/api/sub-tasks/${id}`, payload);
    console.log('서브태스크 수정 응답:', response.data);
    
    if (response.data && response.data.status !== 200) {
      throw new Error(response.data.message || '서브태스크 수정에 실패했습니다.');
    }
    
    return response;
  } catch (error) {
    console.error('Failed to update sub-task:', error);
    console.error('Error details:', error.response?.data);
    throw error;
  }
};

/**
 * 서브태스크 삭제
 */
export const deleteSubTask = async (id) => {
  try {
    const response = await api.delete(`/api/sub-tasks/${id}`);
    
    if (response.data && response.data.status !== 200) {
      throw new Error(response.data.message || '서브태스크 삭제에 실패했습니다.');
    }
    
    return response;
  } catch (error) {
    console.error('Failed to delete sub-task:', error);
    throw error;
  }
};

/**
 * 특정 스케줄의 서브태스크 조회
 */
export const getSubTasksBySchedule = async (scheduleId) => {
  try {
    // 전체 서브태스크를 조회한 후 필터링
    // 백엔드에 schedule_id로 필터링하는 엔드포인트가 있다면 사용
    const today = new Date();
    const from = new Date(today.getFullYear(), today.getMonth() - 1, 1).toISOString().split('T')[0];
    const to = new Date(today.getFullYear(), today.getMonth() + 2, 0).toISOString().split('T')[0];
    
    const allTasks = await getSubTasks(from, to);
    // schedule_id와 scheduleId 둘 다 비교 (문자열 변환 포함)
    return allTasks.filter(task => 
      String(task.scheduleId) === String(scheduleId) || 
      String(task.schedule_id) === String(scheduleId)
    );
  } catch (error) {
    console.error('Failed to fetch sub-tasks by schedule:', error);
    throw error;
  }
};

export default {
  createSubTask,
  getSubTasks,
  updateSubTask,
  deleteSubTask,
  getSubTasksBySchedule,
};
