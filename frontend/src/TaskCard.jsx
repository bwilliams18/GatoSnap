import React from "react";
import ProgressBar from "./ProgressBar";
import { useDeleteTask } from "./query";

const TaskCard = ({ task }) => {
  const { mutate: deleteTask } = useDeleteTask();
  return (
    <div className="flex flex-col rounded bg-slate-700 p-3 m-2">
      <div className="flex">
        <b>{task.name}</b>
        {task.status === "pending" && (
          <button
            className="bg-red-500 hover:bg-red-700 text-white font-bold px-1 text-sm rounded"
            onClick={() => {
              deleteTask(task.id);
            }}>
            Cancel
          </button>
        )}
      </div>
      <div className="flex">
        <ProgressBar progress={task.progress} total={task.total} />
        {task.func === "transfer_file" ? (
          <span className="ml-2">
            {(task.progress / 1000000000).toFixed(2)}GB/
            {(task.total / 1000000000).toFixed(2)}GB
          </span>
        ) : (
          <span className="ml-2">
            {task.progress}/{task.total}
          </span>
        )}
      </div>
    </div>
  );
};

export default TaskCard;
