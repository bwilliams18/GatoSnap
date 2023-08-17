import React from "react";

const ProgressBar = ({ progress, total }) => (
  <div className="w-60 bg-gray-400 border border-white rounded">
    <div
      className="bg-blue-500 h-full animate-pulse text-center"
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
