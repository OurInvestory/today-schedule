import { useState, useEffect, useCallback } from 'react';
import { 
  getLectures, 
  createLecture, 
  updateLecture, 
  deleteLecture,
  getWeekNumber,
  getWeekRange 
} from '../services/lectureService';
import { formatDate } from '../utils/dateUtils';

/**
 * 시간표(강의) 관리 훅
 */
export const useTimetable = () => {
  const [lectures, setLectures] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  
  // 현재 주의 시작/종료일
  const { startOfWeek, endOfWeek } = getWeekRange(currentDate);
  
  // 현재 주차 번호
  const weekNumber = getWeekNumber(currentDate);
  const year = currentDate.getFullYear();

  // 토/일 강의가 있는지 확인
  const hasWeekendLectures = lectures.some(lecture => {
    const weekDays = lecture.week || [];
    return weekDays.includes(0) || weekDays.includes(6); // 0=일, 6=토
  });

  // 표시할 요일 결정 (기본 월~금, 주말 강의 있으면 월~일)
  const displayDays = hasWeekendLectures 
    ? [1, 2, 3, 4, 5, 6, 0] // 월~일
    : [1, 2, 3, 4, 5];       // 월~금

  // 시간 범위 계산 (기본 9~17시, 강의에 따라 확장)
  const calculateTimeRange = useCallback(() => {
    let minHour = 9;
    let maxHour = 17;
    
    lectures.forEach(lecture => {
      if (lecture.start_time) {
        const startHour = parseInt(lecture.start_time.split(':')[0], 10);
        minHour = Math.min(minHour, startHour);
      }
      if (lecture.end_time) {
        const endHour = parseInt(lecture.end_time.split(':')[0], 10);
        // 종료 시간이 정각이 아니면 +1
        const endMinute = parseInt(lecture.end_time.split(':')[1], 10);
        maxHour = Math.max(maxHour, endMinute > 0 ? endHour + 1 : endHour);
      }
    });
    
    return { minHour, maxHour };
  }, [lectures]);

  const { minHour, maxHour } = calculateTimeRange();

  // 강의 데이터 조회
  const fetchLectures = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const from = formatDate(startOfWeek, 'YYYY-MM-DD');
      const to = formatDate(endOfWeek, 'YYYY-MM-DD');
      
      const response = await getLectures(from, to);
      
      // response 구조에 따라 처리
      let lectureData = [];
      
      if (response) {
        // { status: 200, data: [...] } 형식
        if (response.status === 200 && response.data) {
          lectureData = response.data;
        }
        // { data: [...] } 형식
        else if (response.data && Array.isArray(response.data)) {
          lectureData = response.data;
        }
        // 직접 배열이 반환된 경우
        else if (Array.isArray(response)) {
          lectureData = response;
        }
      }
      
      setLectures(Array.isArray(lectureData) ? lectureData : []);
    } catch (err) {
      console.error('Failed to fetch lectures:', err);
      // API 에러여도 빈 배열로 설정하고 로딩 종료
      setError(err.message || '강의 목록을 불러오는데 실패했습니다.');
      setLectures([]);
    } finally {
      setLoading(false);
    }
  }, [startOfWeek, endOfWeek]);

  // 강의 추가
  const addLecture = async (lectureData) => {
    try {
      const response = await createLecture(lectureData);
      if (response.status === 200) {
        await fetchLectures();
        return response;
      }
      throw new Error(response.message || '강의 추가에 실패했습니다.');
    } catch (err) {
      console.error('Failed to add lecture:', err);
      throw err;
    }
  };

  // 강의 수정
  const editLecture = async (lectureId, lectureData) => {
    try {
      const response = await updateLecture(lectureId, lectureData);
      if (response.status === 200) {
        await fetchLectures();
        return response;
      }
      throw new Error(response.message || '강의 수정에 실패했습니다.');
    } catch (err) {
      console.error('Failed to update lecture:', err);
      throw err;
    }
  };

  // 강의 삭제
  const removeLecture = async (lectureId) => {
    try {
      const response = await deleteLecture(lectureId);
      if (response.status === 200) {
        await fetchLectures();
        return response;
      }
      throw new Error(response.message || '강의 삭제에 실패했습니다.');
    } catch (err) {
      console.error('Failed to delete lecture:', err);
      throw err;
    }
  };

  // 이전 주로 이동
  const goToPreviousWeek = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() - 7);
    setCurrentDate(newDate);
  };

  // 다음 주로 이동
  const goToNextWeek = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + 7);
    setCurrentDate(newDate);
  };

  // 오늘로 이동
  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // 특정 요일의 강의 목록 가져오기
  const getLecturesForDay = (dayOfWeek) => {
    return lectures.filter(lecture => {
      const weekDays = lecture.week || [];
      return weekDays.includes(dayOfWeek);
    });
  };

  // 특정 요일의 날짜 계산
  const getDateForDay = (dayOfWeek) => {
    const date = new Date(startOfWeek);
    // 월요일(1)부터 시작하므로 조정
    const diff = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    date.setDate(date.getDate() + diff);
    return date;
  };

  // 초기 로드 및 주 변경 시 데이터 조회
  useEffect(() => {
    fetchLectures();
  }, [fetchLectures]);

  return {
    lectures,
    loading,
    error,
    currentDate,
    year,
    weekNumber,
    startOfWeek,
    endOfWeek,
    displayDays,
    hasWeekendLectures,
    minHour,
    maxHour,
    fetchLectures,
    addLecture,
    editLecture,
    removeLecture,
    goToPreviousWeek,
    goToNextWeek,
    goToToday,
    getLecturesForDay,
    getDateForDay,
  };
};
