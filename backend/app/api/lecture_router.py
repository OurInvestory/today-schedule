from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Union
from datetime import date

from app.db.database import get_db
from app.models.lecture import Lecture
from app.schemas.lecture import SaveLectureRequest, UpdateLectureRequest, LectureResponse
from app.schemas.common import ResponseDTO


router = APIRouter(prefix="/api/lectures", tags=["Lecture"])


# 강의 저장
@router.post("", response_model=ResponseDTO)
def create_lectures(
    obj_in: Union[SaveLectureRequest, List[SaveLectureRequest]], 
    db: Session = Depends(get_db)
):
    test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
    items = obj_in if isinstance(obj_in, list) else [obj_in]
    saved_lectures = []

    try:
        for item in items:
            week_str = ",".join(map(str, item.week))    # 리스트 - 문자열 변환
            
            new_lecture = Lecture(
                user_id=test_user_id,
                title=item.title,
                start_time=item.start_time,
                end_time=item.end_time,
                start_day=item.start_day,
                end_day=item.end_day,
                week=week_str
            )
            db.add(new_lecture)
            saved_lectures.append(new_lecture)
        
        db.commit()
        for l in saved_lectures: db.refresh(l)

        return ResponseDTO(
            status=200,
            message="강의 저장에 성공했습니다.",
            data=[LectureResponse.from_orm_custom(l) for l in saved_lectures]
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"강의 저장에 실패했습니다.", data=None)


# 강의 수정
@router.put("/{lecture_id}", response_model=ResponseDTO)
def update_lecture(lecture_id: str, obj_in: UpdateLectureRequest, db: Session = Depends(get_db)):
    try:
        lecture = db.query(Lecture).filter(Lecture.lecture_id == lecture_id).first()
        if not lecture:
            return ResponseDTO(status=404, message="강의를 찾을 수 없습니다.", data=None)

        update_data = obj_in.dict(exclude_unset=True)
        
        if "week" in update_data and update_data["week"] is not None:
            update_data["week"] = ",".join(map(str, update_data["week"]))

        for key, value in update_data.items():
            setattr(lecture, key, value)
        
        db.commit()
        db.refresh(lecture)

        return ResponseDTO(
            status=200,
            message="강의 수정에 성공했습니다.",
            data=LectureResponse.from_orm_custom(lecture)
        )
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"강의 수정에 실패했습나다.", data=None)


# 강의 삭제
@router.delete("/{lecture_id}", response_model=ResponseDTO)
def delete_lecture(lecture_id: str, db: Session = Depends(get_db)):
    try:
        lecture = db.query(Lecture).filter(Lecture.lecture_id == lecture_id).first()
        if not lecture:
            return ResponseDTO(status=404, message="강의를 찾을 수 없습니다.", data=None)

        db.delete(lecture)
        db.commit()
        return ResponseDTO(status=200, message="강의 삭제에 성공했습니다.", data=None)
    except Exception as e:
        db.rollback()
        return ResponseDTO(status=500, message=f"강의 삭제에 실패했습니다.", data=None)


# 강의 조회
@router.get("", response_model=ResponseDTO)
def get_lectures(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db)
):
    try:
        test_user_id = "7822a162-788d-4f36-9366-c956a68393e1"
        
        lectures = db.query(Lecture).filter(
            and_(
                Lecture.user_id == test_user_id,
                Lecture.start_day <= to_date,
                Lecture.end_day >= from_date
            )
        ).all()

        return ResponseDTO(
            status=200,
            message="강의 조회에 성공했습니다.",
            data=[LectureResponse.from_orm_custom(l) for l in lectures]
        )
    except Exception as e:
        return ResponseDTO(status=500, message=f"강의 조회에 실패했습니다.", data=None)