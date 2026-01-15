import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  getLectures,
  createLecture,
  updateLecture,
  deleteLecture,
  getWeekNumber,
  getWeekRange,
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

  // 현재 주의 시작/종료일 (useMemo로 안정화)
  const { startOfWeek, endOfWeek } = useMemo(
    () => getWeekRange(currentDate),
    [currentDate.getTime()]
  );

  // 날짜 문자열 (useCallback 의존성용)
  const fromDateStr = useMemo(
    () => formatDate(startOfWeek, 'YYYY-MM-DD'),
    [startOfWeek]
  );
  const toDateStr = useMemo(
    () => formatDate(endOfWeek, 'YYYY-MM-DD'),
    [endOfWeek]
  );

  // 현재 주차 번호
  const weekNumber = getWeekNumber(currentDate);
  const year = currentDate.getFullYear();

  // 토/일 강의가 있는지 확인 (백엔드: 0=월, 5=토, 6=일)
  const hasWeekendLectures = lectures.some((lecture) => {
    const weekDays = lecture.week || [];
    return weekDays.includes(5) || weekDays.includes(6); // 5=토, 6=일
  });

  // 표시할 요일 결정 (항상 월~일 7일 표시)
  const displayDays = [0, 1, 2, 3, 4, 5, 6]; // 월~일

  // 시간 범위 계산 (기본 9~17시, 강의에 따라 확장)
  const calculateTimeRange = useCallback(() => {
    let minHour = 9;
    let maxHour = 17;

    lectures.forEach((lecture) => {
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
      const response = await getLectures(fromDateStr, toDateStr);

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
  }, [fromDateStr, toDateStr]);

  // 강의 추가
  const addLecture = async (lectureData) => {
    try {
      const response = await createLecture(lectureData);
      // lectureService는 response.data를 반환하므로 response 자체가 {status, data, message}
      if (response && (response.status === 200 || response.status === 201)) {
        await fetchLectures();
        return response;
      }
      // status가 없으면 성공으로 간주 (일부 API는 직접 데이터만 반환)
      if (response && !response.status) {
        await fetchLectures();
        return { status: 200, data: response };
      }
      throw new Error(response?.message || '강의 추가에 실패했습니다.');
    } catch (err) {
      console.error('Failed to add lecture:', err);
      throw err;
    }
  };

  // 강의 수정
  const editLecture = async (lectureId, lectureData) => {
    try {
      const response = await updateLecture(lectureId, lectureData);
      // lectureService는 response.data를 반환하므로 response 자체가 {status, data, message}
      if (response && (response.status === 200 || response.status === 201)) {
        await fetchLectures();
        return response;
      }
      // status가 없으면 성공으로 간주
      if (response && !response.status) {
        await fetchLectures();
        return { status: 200, data: response };
      }
      throw new Error(response?.message || '강의 수정에 실패했습니다.');
    } catch (err) {
      console.error('Failed to update lecture:', err);
      throw err;
    }
  };

  // 강의 삭제
  const removeLecture = async (lectureId) => {
    try {
      const response = await deleteLecture(lectureId);
      // 삭제 API는 빈 응답을 반환할 수 있으므로 성공으로 간주
      await fetchLectures();
      return response || { status: 200 };
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
    return lectures.filter((lecture) => {
      const weekDays = lecture.week || [];
      return weekDays.includes(dayOfWeek);
    });
  };

  // 특정 요일의 날짜 계산 (백엔드: 0=월, 1=화, ..., 6=일)
  const getDateForDay = (dayOfWeek) => {
    const date = new Date(startOfWeek);
    // startOfWeek은 월요일, dayOfWeek 0=월이므로 그대로 더하면 됨
    date.setDate(date.getDate() + dayOfWeek);
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
