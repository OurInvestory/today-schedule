import api from './api';

/**
 * 챗봇 메시지 전송
 */
export const sendChatMessage = async (
  text,
  baseDate = null,
  selectedScheduleId = null,
  userContext = {},
  files = null
) => {
  try {
    const now = new Date();
    const timezone =
      Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Seoul';

    // FormData를 사용하여 파일과 텍스트를 함께 전송
    if (files && files.length > 0) {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('baseDate', baseDate || now.toISOString().split('T')[0]);
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
      baseDate: baseDate || now.toISOString().split('T')[0],
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
    const response = await api.post('/api/schedule', payload);
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
    const response = await api.post(
      `/api/schedule/${scheduleId}/sub-tasks`,
      payload
    );
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
export const analyzeTimetableImage = async (imageFile, autoSave = false) => {
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

    const lectures = response.data?.data?.lectures || [];

    // autoSave가 true이면 자동으로 강의 저장
    let saveResult = null;
    if (autoSave && lectures.length > 0) {
      saveResult = await saveLectures(lectures);
    }

    return {
      success: true,
      message: response.data?.data?.assistantMessage || '이미지 분석 완료',
      parsedResult: response.data?.data?.parsedResult,
      lectures: lectures,
      saveResult: saveResult,
      imagePreview: URL.createObjectURL(imageFile),
    };
  } catch (error) {
    console.error('Failed to analyze timetable:', error);
    throw error;
  }
};
