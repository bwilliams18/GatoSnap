import { Disclosure } from "@headlessui/react";
import React from "react";
import {
  useCreateTask,
  useGetFiles,
  useGetStorageDevices,
  useUpdateFile,
} from "./query";
import { bitsToGB } from "./util";

const StorageDeviceCard = ({ storageDevice }) => {
  const { mutate: createTask } = useCreateTask();
  const { mutate: updateFile } = useUpdateFile();
  const { refetch: refetchSD } = useGetStorageDevices();
  const { data: files, refetch: refetchFiles } = useGetFiles(storageDevice.id);
  const [filter, setFilter] = React.useState("all");
  return (
    <div className="rounded bg-slate-700 p-3 m-2 overflow-hidden gap-y-2 flex flex-col">
      <div className="flex flex-col gap-y-2 overflow-hidden max-w-full">
        <div className="gap-y-1 flex flex-col">
          <div className="truncate">
            <b className="block w-full truncate">{storageDevice.name}</b>
          </div>
          <div className="flex gap-x-1 flex-wrap">
            <code className="font-mono text-sm bg-slate-900 rounded px-1.5 py-0.5">
              {storageDevice.base_path}
            </code>
            {storageDevice.connected ? (
              <i className="bg-green-600 text-sm px-1.5 py-0.5 rounded">
                Connected
              </i>
            ) : (
              <i className="bg-red-600 text-sm px-1.5 py-0.5 rounded">
                Disconnected
              </i>
            )}
          </div>
          <div className="flex gap-x-1 flex-wrap">
            <span className="text-sm px-1.5 py-0.5 rounded bg-slate-800">
              {bitsToGB(
                files
                  ?.filter(file => file.status === "synced")
                  ?.reduce((acc, file) => acc + file.file_size, 0)
              )}
            </span>
            <span className=" text-sm bg-slate-800 px-1.5 py-0.5 rounded">
              {files?.reduce(
                (acc, file) => (file.status === "synced" ? acc + 1 : acc),
                0
              )}{" "}
              of {files?.length} Files Synced
            </span>
          </div>
        </div>
        <div className="flex gap-2 min-w-min whitespace-nowrap">
          {storageDevice.connected && (
            <button
              className="bg-red-500 enabled:hover:bg-red-700 text-white font-bold py-1 px-2 rounded"
              onClick={() => {
                createTask({
                  name: `Eject ${storageDevice.name}`,
                  func: "eject_sd",
                  args: [storageDevice.id],
                  kwargs: {},
                });
                setTimeout(() => refetchSD(), 2500);
              }}>
              Eject
            </button>
          )}
          <button
            className="bg-blue-500 enabled:hover:bg-blue-700 disabled:saturate-50 disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
            disabled={!storageDevice.connected}
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
            className="bg-blue-500 enabled:hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
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
          {files?.length -
            files?.reduce(
              (acc, file) => (file.status === "synced" ? acc + 1 : acc),
              0
            ) >
            0 && (
            <button
              className="bg-blue-500 enabled:hover:bg-blue-700 disabled:saturate-50	disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
              disabled={!storageDevice.connected}
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
          )}
        </div>
      </div>
      <Disclosure className="rounded" as="div">
        <Disclosure.Button
          className="bg-slate-800 hover:bg-slate-900 text-white font-bold py-1 px-2 rounded w-full"
          onClick={refetchFiles}>
          {({ open }) => (open ? "Hide Files" : "Show Files")}
        </Disclosure.Button>
        <Disclosure.Panel className="">
          <div className="flex gap-2 my-2 w-full">
            {["all", "missing", "synced", "watched"].map(filterName => (
              <button
                key={filterName}
                type="button"
                className={`${
                  filter === filterName
                    ? "bg-blue-500 hover:bg-blue-700"
                    : "bg-slate-800 hover:bg-slate-900"
                } text-white font-bold py-1 px-2 rounded`}
                onClick={() => setFilter(filterName)}>
                {" "}
                {filterName.charAt(0).toUpperCase() + filterName.slice(1)}(
                {files?.reduce(
                  (acc, file) =>
                    filterName === "all"
                      ? acc + 1
                      : file.status === filterName
                      ? acc + 1
                      : acc,
                  0
                )}
                )
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-2 p-2 mt-1 rounded max-h-[60vh] overflow-y-scroll drop-shadow bg-slate-800">
            {files
              ?.filter(file => filter === "all" || file.status === filter)
              ?.sort((a, b) => a.title.localeCompare(b.title))
              ?.map(file => (
                <div
                  key={file.id}
                  className="text-white p-2 bg-slate-600 rounded flex flex-col sm:flex-row gap-x-1">
                  <div className="grow truncate">
                    <div className="truncate">
                      <b className="">{file.title}</b>
                    </div>
                    <span className="text-sm px-1.5 py-0.5 rounded bg-slate-800 mr-1">
                      {bitsToGB(file.file_size)}
                    </span>
                    <i
                      className={`${
                        file.status === "missing"
                          ? "bg-red-600"
                          : file.status === "watched"
                          ? "bg-blue-700"
                          : "bg-green-600"
                      } text-sm px-1.5 py-0.5 rounded mx-1`}>
                      {file.status}
                    </i>
                  </div>
                  <div className="flex gap-2 my-1 justify-center sm:justify-end whitespace-nowrap">
                    {file.status === "watched" && (
                      <button
                        className="bg-blue-500 enabled:hover:bg-blue-700 disabled:saturate-50	disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
                        disabled={!storageDevice.connected}
                        onClick={() => {
                          updateFile({
                            storage_device_id: storageDevice.id,
                            file_id: file.id,
                            status: "missing",
                          });
                        }}>
                        Mark Missing
                      </button>
                    )}
                    {file.status === "missing" && (
                      <button
                        className="bg-blue-500 enabled:hover:bg-blue-700 disabled:saturate-50	disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
                        disabled={!storageDevice.connected}
                        onClick={() => {
                          createTask({
                            name: `Transfer ${file.title} to ${storageDevice.name}`,
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
                        className="bg-green-500 enabled:hover:bg-green-700 disabled:saturate-50	disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
                        disabled={!storageDevice.connected}
                        onClick={() => {
                          updateFile({
                            storage_device_id: storageDevice.id,
                            file_id: file.id,
                            status: "watched",
                          });
                        }}>
                        Mark Watched
                      </button>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </Disclosure.Panel>
      </Disclosure>
    </div>
  );
};

export default StorageDeviceCard;
