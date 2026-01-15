import api from './api';

/**
 * 서울 시간 기준으로 현재 날짜 가져오기
 */
const getSeoulDate = () => {
  const now = new Date();
  // 서울 시간대로 변환
  const seoulTime = new Date(
    now.toLocaleString('en-US', { timeZone: 'Asia/Seoul' })
  );
  return seoulTime;
};

/**
 * 서울 시간 기준으로 날짜 문자열 (YYYY-MM-DD) 가져오기
 */
const getSeoulDateString = () => {
  const seoulDate = getSeoulDate();
  const year = seoulDate.getFullYear();
  const month = String(seoulDate.getMonth() + 1).padStart(2, '0');
  const day = String(seoulDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * 키워드로 일정 검색 (마감일이 지나지 않은 최근 한 달 내)
 */
export const searchSchedulesByKeyword = async (keyword) => {
  try {
    const now = new Date();
    const oneMonthAgo = new Date(now);
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

    const fromDate = oneMonthAgo.toISOString().split('T')[0];
    const toDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0]; // 앞으로 30일

    const response = await api.get('/api/schedules', {
      params: { from: fromDate, to: toDate },
    });

    const schedules = response.data?.data || [];

    // 키워드 필터링 및 마감일이 지나지 않은 일정만 반환
    const filtered = schedules.filter((schedule) => {
      const title = schedule.title?.toLowerCase() || '';
      const matchesKeyword = title.includes(keyword.toLowerCase());

      // 마감일(end_at 또는 start_at)이 현재 시간 이후인 것만
      const scheduleTime = schedule.start_at || schedule.end_at;
      if (!scheduleTime) return matchesKeyword;

      const scheduleDate = new Date(scheduleTime);
      return matchesKeyword && scheduleDate >= now;
    });

    return filtered;
  } catch (error) {
    console.error('Failed to search schedules:', error);
    return [];
  }
};

export const sendChatMessage = async (
  text,
  baseDate = null,
  selectedScheduleId = null,
  userContext = {},
  files = null
) => {
  try {
    // 항상 서울 시간 기준
    const timezone = 'Asia/Seoul';

    // FormData를 사용하여 파일과 텍스트를 함께 전송
    if (files && files.length > 0) {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('baseDate', baseDate || getSeoulDateString());
      formData.append('timezone', timezone);
      if (selectedScheduleId) {
        formData.append('selectedScheduleId', selectedScheduleId);
      }
      formData.append('userContext', JSON.stringify(userContext));

      // 파일 추가
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await api.post('/api/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response;
    }

    // 일반 JSON 요청
    const response = await api.post('/api/chat', {
      text,
      baseDate: baseDate || getSeoulDateString(),
      timezone,
      selectedScheduleId,
      userContext,
    });
    return response;
  } catch (error) {
    console.error('Failed to send chat message:', error);
    throw error;
  }
};

/**
 * 챗봇 대화 히스토리 조회
 */
export const getChatHistory = async (conversationId) => {
  try {
    const response = await api.get(`/ai/chat/${conversationId}`);
    return response;
  } catch (error) {
    console.error('Failed to get chat history:', error);
    throw error;
  }
};

/**
 * AI 파싱 결과로 일정 생성
 */
export const createScheduleFromAI = async (payload) => {
  try {
    // AI 응답 필드를 백엔드 스키마에 맞게 변환
    const startAt = payload.start_at || payload.start_time || null;
    let endAt = payload.end_at || payload.end_time || null;

    // start_at만 있고 end_at이 없으면 1시간 후로 설정
    if (startAt && !endAt) {
      const startDate = new Date(startAt);
      startDate.setHours(startDate.getHours() + 1);
      endAt = startDate.toISOString();
    }

    // end_at만 있고 start_at이 없으면 1시간 전으로 설정
    let finalStartAt = startAt;
    if (!startAt && endAt) {
      const endDate = new Date(endAt);
      endDate.setHours(endDate.getHours() - 1);
      finalStartAt = endDate.toISOString();
    }

    const schedulePayload = {
      title: payload.title,
      type: payload.type === 'EVENT' ? 'event' : 'task',
      category: payload.category || '기타',
      start_at: finalStartAt,
      end_at: endAt,
      priority_score: payload.importance_score || payload.priority_score || 5,
      original_text: payload.original_text || null,
      estimated_minute: payload.estimated_minute || 60,
      source: 'ai',
    };

    console.log('Creating schedule:', schedulePayload);
    const response = await api.post('/api/schedules', schedulePayload);
    return response;
  } catch (error) {
    console.error('Failed to create schedule from AI:', error);
    throw error;
  }
};

/**
 * AI 파싱 결과로 할 일 생성
 */
export const createSubTaskFromAI = async (scheduleId, payload) => {
  try {
    // end_at에서 date 추출
    const endAt = payload.end_at || payload.due_date || payload.date;
    const dateStr = endAt
      ? typeof endAt === 'string'
        ? endAt.split('T')[0]
        : endAt
      : new Date().toISOString().split('T')[0];

    // importance_score를 priority로 변환
    let priority = payload.priority || 'medium';
    if (!payload.priority && payload.importance_score) {
      if (payload.importance_score >= 7) priority = 'high';
      else if (payload.importance_score <= 3) priority = 'low';
      else priority = 'medium';
    }

    // AI가 생성한 할 일 데이터를 백엔드 스키마에 맞게 변환
    const subTaskPayload = {
      schedule_id: scheduleId || null, // scheduleId 없으면 독립 할 일
      title: payload.title,
      date: dateStr,
      estimated_minute: payload.estimated_minute || 60,
      priority: priority,
      category: payload.category || '기타',
      tip: payload.tip || payload.reason || null,
    };

    console.log('Creating sub-task:', subTaskPayload);
    // 직접 sub-tasks 엔드포인트로 POST
    const response = await api.post('/api/sub-tasks', subTaskPayload);
    return response;
  } catch (error) {
    console.error('Failed to create sub-task from AI:', error);
    throw error;
  }
};

/**
 * 시간 형식 변환 (HH:mm -> HH:mm:ss)
 */
const formatTimeWithSeconds = (time) => {
  if (!time) return null;
  // 이미 HH:mm:ss 형식인 경우 그대로 반환
  if (time.length === 8) return time;
  // HH:mm 형식인 경우 :00 추가
  return `${time}:00`;
};

const formatDateString = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * 오늘 날짜와 16주 뒤 날짜 계산
 */
const getDefaultDateRange = () => {
  const today = new Date();
  const sixteenWeeksLater = new Date(today);
  sixteenWeeksLater.setDate(today.getDate() + 16 * 7); // 16주 = 112일

  return {
    startDay: formatDateString(today),
    endDay: formatDateString(sixteenWeeksLater),
  };
};

/**
 * 강의 데이터를 백엔드 형식으로 변환
 */
const transformLectureData = (lecture) => {
  const { startDay, endDay } = getDefaultDateRange();

  // week이 정수로 오면 배열로 변환
  const weekArray = Array.isArray(lecture.week) ? lecture.week : [lecture.week];

  return {
    title: lecture.title,
    start_time: formatTimeWithSeconds(lecture.startTime),
    end_time: formatTimeWithSeconds(lecture.endTime),
    start_day: lecture.startDay || startDay,
    end_day: lecture.endDay || endDay,
    week: weekArray,
  };
};

/**
 * 강의 목록 저장 (시간표 분석 결과)
 */
export const saveLectures = async (lectures) => {
  try {
    const results = [];

    for (const lecture of lectures) {
      const payload = transformLectureData(lecture);
      console.log('강의 저장 요청:', payload);

      const response = await api.post('/api/lectures', payload);
      results.push(response.data);
    }

    return {
      success: true,
      message: `${results.length}개의 강의가 저장되었습니다.`,
      results,
    };
  } catch (error) {
    console.error('Failed to save lectures:', error);
    throw error;
  }
};

/**
 * 시간표/포스터 이미지 분석 및 일정 추출
 */
export const analyzeTimetableImage = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append(
      'timezone',
      Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul'
    );

    const response = await api.post('/api/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 이미지 분석은 시간이 걸릴 수 있음
    });

    const data = response.data?.data;
    const parsedResult = data?.parsed_result || data?.parsedResult;
    const assistantMessage =
      data?.assistant_message || data?.assistantMessage || '이미지 분석 완료';
    const lectures = data?.lectures || [];

    // actions에 target 필드 추가 (백엔드에서 없는 경우 대비)
    let actions = parsedResult?.actions || [];

    // lectures가 있으면 LECTURES 액션 추가
    if (lectures.length > 0) {
      actions = [
        ...actions,
        {
          op: 'CREATE',
          target: 'LECTURES',
          payload: lectures,
          description: `${lectures.length}개의 강의를 시간표에 추가합니다.`,
        },
      ];
    } else {
      actions = actions.map((action) => {
        // target 결정: 제목에 [준비]가 있거나 type이 TASK면 SUB_TASK로 강제 지정
        const title = action.payload?.title || '';
        const isSubTask =
          title.includes('[준비]') || action.payload?.type === 'TASK';

        return {
          ...action,
          target: isSubTask ? 'SUB_TASK' : action.target || 'SCHEDULE',
        };
      });
    }

    return {
      success: true,
      message: assistantMessage,
      parsedResult: { ...parsedResult, actions },
      actions: actions,
      lectures: lectures,
      imagePreview: URL.createObjectURL(imageFile),
    };
  } catch (error) {
    console.error('Failed to analyze timetable:', error);
    throw error;
  }
};

/**
 * AI 파싱 결과로 강의(Lecture) 생성
 */
export const createLectureFromAI = async (payload) => {
  try {
    const lecturePayload = {
      title: payload.title,
      start_time: payload.start_time,
      end_time: payload.end_time,
      start_day: payload.start_day,
      end_day: payload.end_day,
      week: payload.week || [],
    };

    console.log('Creating lecture:', lecturePayload);
    const response = await api.post('/api/lectures', lecturePayload);
    return response;
  } catch (error) {
    console.error('Failed to create lecture from AI:', error);
    throw error;
  }
};
