import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Button from '../components/common/Button';
import './TaskDetail.css';

const TaskDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // TODO: Fetch task detail by ID

  return (
    <div className="task-detail">
      <div className="task-detail__container">
        <div className="task-detail__header">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            ← 뒤로
          </Button>
          <h1 className="task-detail__title">과제 상세</h1>
        </div>

        <div className="task-detail__content">
          <p>Task ID: {id}</p>
          <p>상세 페이지는 향후 구현 예정입니다.</p>
        </div>
      </div>
    </div>
  );
};

export default TaskDetail;