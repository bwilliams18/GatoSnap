import { Disclosure } from "@headlessui/react";
import React from "react";
import { useCreateTask, useGetFiles } from "./query";

const StorageDeviceCard = ({ storageDevice }) => {
  const { mutate: createTask } = useCreateTask();
  const { data: files } = useGetFiles(storageDevice.id);
  console.log(files);
  return (
    <div className="rounded bg-slate-700 p-3 m-2">
      <b>{storageDevice.name}</b>
      <div className="flex gap-2 mx-auto">
        <button
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
          onClick={() => {
            createTask({
              name: "Check Files",
              func: "check_files",
              args: [storageDevice.id],
              kwargs: {},
            });
          }}>
          Check Files
        </button>
        <button
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
          onClick={() => {
            createTask({
              name: "Get Files",
              func: "get_files",
              args: [storageDevice.id],
              kwargs: {},
            });
          }}>
          Get Files
        </button>
        <button
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
          onClick={() => {
            createTask({
              name: "Transfer Files",
              func: "transfer_files",
              args: [storageDevice.id],
              kwargs: {},
            });
          }}>
          Transfer Files
        </button>
      </div>
      <Disclosure>
        <Disclosure.Button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded my-2">
          Files
        </Disclosure.Button>
        <Disclosure.Panel className="flex flex-col gap-2 m-2">
          {files?.map(file => (
            <div key={file.id} className="text-white p-2 bg-slate-600 rounded">
              <b>{file.title}</b> <i>{file.status}</i>{" "}
              {(file.file_size / 1024 / 1024 / 1024).toFixed(2)} GB
              {file.status === "missing" && (
                <button
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold ml-1 px-1 text-sm rounded"
                  onClick={() => {
                    createTask({
                      name: "Transfer File",
                      func: "transfer_file",
                      args: [file.id],
                      kwargs: {},
                    });
                  }}>
                  Transfer
                </button>
              )}
              {file.status === "synced" && (
                <button
                  className="bg-green-500 hover:bg-green-700 text-white font-bold ml-1 px-1 text-sm rounded"
                  onClick={() => {
                    createTask({
                      name: "Mark Watched",
                      func: "mark_watched",
                      args: [file.id],
                      kwargs: {},
                    });
                  }}>
                  Mark Watched
                </button>
              )}
            </div>
          ))}
        </Disclosure.Panel>
      </Disclosure>
    </div>
  );
};

export default StorageDeviceCard;
