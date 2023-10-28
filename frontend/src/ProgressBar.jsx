import React from "react";

const ProgressBar = ({ progress, total, barColor = "bg-blue-500" }) => (
  <div className="w-full bg-gray-400 border border-white rounded">
    <div
      className={`${barColor} h-full ${
        progress > 0 && progress !== total ? "animate-pulse" : ""
      } text-center`}
      style={{
        width: `${((progress / total) * 100 || 0).toFixed(2)}%`,
      }}>
      <span className="px-1 font-bold">
        {((progress / total) * 100 || 0).toFixed(2)}%
      </span>
    </div>
  </div>
);

export default ProgressBar;
