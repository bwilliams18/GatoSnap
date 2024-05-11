import moment from "moment";
import React from "react";
import ProgressBar from "./ProgressBar";
import { useDeleteTask, useUpdateTask } from "./query";
import { bitsToGB } from "./util";

const TaskCard = ({ task }) => {
  const { mutate: deleteTask } = useDeleteTask();
  const { mutate: updateTask } = useUpdateTask();
  return (
    <div className="flex flex-col rounded bg-slate-700 p-3 m-2 gap-y-1 min-w-fit overflow-hidden">
      <div className="flex gap-x-1">
        <div className="max-w-xs truncate grow">
          <b>{task.name}</b>
        </div>
        <div className="ml-auto">
          {task.status === "stopped" && (
            <button
              className="text-white font-bold px-1 text-sm rounded bg-green-500 hover:bg-green-700"
              onClick={() => {
                updateTask({ id: task.id, status: "pending" });
              }}>
              Restart
            </button>
          )}
          {task.status === "running" ? (
            <button
              className="text-white font-bold px-1 text-sm rounded bg-red-500 hover:bg-red-700"
              onClick={() => {
                updateTask({ id: task.id, status: "stopped" });
              }}>
              Stop
            </button>
          ) : (
            <button
              className={`text-white font-bold px-1 text-sm rounded
             ${
               task.status === "success"
                 ? "bg-green-500 hover:bg-green-700"
                 : task.status === "failed"
                 ? "bg-red-500 hover:bg-red-700"
                 : "bg-blue-500 hover:bg-blue-700"
             }
            `}
              onClick={() => {
                deleteTask(task.id);
              }}>
              {task.status === "success" ? "Clear" : "Cancel"}
            </button>
          )}
        </div>
      </div>
      <div className="flex">
        <ProgressBar
          progress={task.progress}
          total={task.total}
          barColor={
            task.status === "success"
              ? "bg-green-500"
              : task.status === "failed"
              ? "bg-red-500"
              : task.status === "running"
              ? "bg-blue-500"
              : "bg-gray-500"
          }
        />
      </div>
      {task.func === "transfer_file" && task.status === "running" ? (
        <div className="flex divide-x gap-x-1">
          <div className="text-xs text-gray-400 text-center grow">
            {bitsToGB(task.progress)}/{bitsToGB(task.total)}
          </div>
          <div className="text-xs text-gray-400 text-center grow">
            {(
              bperSec(task.progress, task.total, task.started) /
              1024 /
              1024
            ).toFixed(2)}
            Mbps
          </div>
          <div className="text-xs text-gray-400 text-center grow">
            {moment
              .duration(
                (task.total - task.progress) /
                  bperSec(task.progress, task.total, task.started),
                "seconds"
              )
              .humanize()}
          </div>
          <div className="text-xs text-gray-400 text-center grow">
            {moment()
              .add(
                (task.total - task.progress) /
                  bperSec(task.progress, task.total, task.started),
                "seconds"
              )
              .format("HH:mm:ss")}
          </div>
        </div>
      ) : null}
    </div>
  );
};

const bperSec = (progress, total, started) => {
  return progress / moment().diff(moment.utc(started).local(), "seconds");
};

export default TaskCard;
