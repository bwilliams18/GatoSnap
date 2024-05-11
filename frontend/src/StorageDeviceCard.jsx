import { Disclosure } from "@headlessui/react";
import React from "react";
import {
  useCreateTask,
  useGetFiles,
  useGetStorageDevices,
  useUpdateFile,
  useUpdateFilesStatus,
} from "./query";
import { bitsToGB } from "./util";
// Title match "{series} | s{season}e{episode} | {title}";
const title_match =
  /(?<series>.+) \| s(?<season>\d+)e(?<episode>\d+) \| (?<title>.+)/;

const FileCard = ({
  file,
  storageDevice,
  selectedFiles,
  setSelectedFiles,
  updateFile,
  createTask,
}) => (
  <div className="text-white p-2 bg-slate-600 rounded flex flex-col sm:flex-row gap-x-1">
    <div className="flex flex-col gap-1 align-middle">
      {/*Selected File?*/}
      <input
        type="checkbox"
        className="h-5 w-5 rounded"
        checked={selectedFiles.includes(file.id)}
        onChange={e => {
          if (e.target.checked) {
            setSelectedFiles([...selectedFiles, file.id]);
          } else {
            setSelectedFiles(selectedFiles.filter(id => id !== file.id));
          }
        }}
      />
    </div>
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
            : file.status === "ignored"
            ? "bg-gray-500"
            : "bg-green-600"
        } text-sm px-1.5 py-0.5 rounded mx-1`}>
        {file.status}
      </i>
    </div>
    <div className="flex gap-2 my-1 justify-end whitespace-nowrap">
      {["watched", "ignored"].includes(file.status) ? (
        <button
          className="bg-red-600 enabled:hover:bg-red-700 disabled:saturate-50	disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
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
      ) : (
        <>
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
          <button
            className="bg-gray-500 enabled:hover:bg-gray-700 disabled:saturate-50	disabled:cursor-not-allowed text-white font-bold py-1 px-2 rounded"
            disabled={!storageDevice.connected}
            onClick={() => {
              updateFile({
                storage_device_id: storageDevice.id,
                file_id: file.id,
                status: "ignored",
              });
            }}>
            Ignore
          </button>
        </>
      )}
    </div>
  </div>
);

const StorageDeviceCard = ({ storageDevice }) => {
  const { mutate: createTask } = useCreateTask();
  const { mutate: updateFile } = useUpdateFile();
  const { mutate: updateFilesStatus } = useUpdateFilesStatus();
  const { refetch: refetchSD } = useGetStorageDevices();
  const { data: files, refetch: refetchFiles } = useGetFiles(storageDevice.id);
  const [filter, setFilter] = React.useState("all");
  const [titleFilter, setTitleFilter] = React.useState("");
  const [selectedFiles, setSelectedFiles] = React.useState([]);
  const groupedFiles = React.useMemo(
    () =>
      files
        ?.reduce((acc, file) => {
          const match = file.title.match(title_match);
          const fileWithMetadata = {
            ...file,
            series: match?.groups.series,
            season: match?.groups.season,
            episode: match?.groups.episode,
            clean_title: match?.groups.title,
          };
          if (!fileWithMetadata.series) {
            if (
              (filter === "all" || fileWithMetadata.status === filter) &&
              (!titleFilter ||
                fileWithMetadata.title
                  .toLowerCase()
                  .includes(titleFilter.toLowerCase()))
            ) {
              acc.push({ ...fileWithMetadata, type: "file" });
            }
            return acc;
          }
          let series = acc.find(s => s.series_name === fileWithMetadata.series);
          if (!series) {
            series = {
              series_name: fileWithMetadata.series,
              seasons: {},
              filtered_file_ids: [],
              file_count: 0,
              file_size: 0,
              filtered_file_count: 0,
              filtered_file_size: 0,
              type: "series",
              title: fileWithMetadata.series,
            };
            acc.push(series);
          }

          let season = series?.seasons?.[fileWithMetadata?.season];
          if (!season) {
            season = {
              season_no: fileWithMetadata.season,
              all_files: [],
              filtered_file_ids: [],
              filtered_files: [],
              file_count: 0,
              file_size: 0,
              filtered_file_count: 0,
              filtered_file_size: 0,
            };
            series.seasons[fileWithMetadata.season] = season;
          }

          season.all_files.push(fileWithMetadata);
          season.file_count++;
          season.file_size += fileWithMetadata.file_size; // assuming file has a size property
          series.file_count++;
          series.file_size += fileWithMetadata.file_size;

          if (
            (filter === "all" || fileWithMetadata.status === filter) &&
            (!titleFilter ||
              fileWithMetadata.title
                .toLowerCase()
                .includes(titleFilter.toLowerCase()))
          ) {
            season.filtered_files.push(fileWithMetadata);
            season.filtered_file_ids.push(fileWithMetadata.id);
            season.filtered_file_count++;
            season.filtered_file_size += fileWithMetadata.file_size;

            series.filtered_file_ids.push(fileWithMetadata.id);
            series.filtered_file_count++;
            series.filtered_file_size += fileWithMetadata.file_size;
          }

          return acc;
        }, [])
        .sort((a, b) => a?.title.localeCompare(b?.title)),
    [files, filter, titleFilter]
  );

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
        <div className="flex gap-2 flex-wrap whitespace-nowrap">
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
                name: "Check Storage Device",
                func: "check_files",
                args: [storageDevice.id],
                kwargs: {},
              });
            }}>
            Check Storage Device
          </button>
          <button
            className="bg-blue-500 enabled:hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
            onClick={() => {
              createTask({
                name: "Sync from Plex",
                func: "get_files",
                args: [storageDevice.id],
                kwargs: {},
              });
            }}>
            Sync from Plex
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
          <div className="flex gap-2 my-2 w-full flex-wrap">
            {["all", "missing", "synced", "watched", "ignored"].map(
              filterName => (
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
              )
            )}
          </div>
          {/* Search Box */}
          <div className="flex gap-2 my-2 w-full flex-wrap">
            <input
              type="text"
              placeholder="Filter By Title"
              className="bg-slate-800 text-white font-bold py-1 px-2 rounded"
              value={titleFilter}
              onChange={e => setTitleFilter(e.target.value)}></input>
            {titleFilter && (
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
                onClick={() => setTitleFilter("")}>
                X
              </button>
            )}
            {/* {filteredFiles?.length > 0 && ( */}
            <button
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
              // onClick={() =>
              //   setSelectedFiles(filteredFiles.map(file => file.id))
              // }
            >
              Select
            </button>
            {/* )} */}
            {selectedFiles.length > 0 && (
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
                onClick={() => setSelectedFiles([])}>
                Clear
              </button>
            )}
          </div>

          {selectedFiles.length > 0 && (
            <div>
              <p className="text-white">
                {selectedFiles.length} Files{" "}
                {bitsToGB(
                  files
                    ?.filter(file => selectedFiles.includes(file.id))
                    ?.reduce((acc, file) => acc + file.file_size, 0)
                )}
              </p>
            </div>
          )}

          {/* Bulk Actions */}
          {selectedFiles.length > 0 && (
            <div className="flex gap-2 my-2 w-full flex-wrap">
              <button
                className="bg-red-600 hover:bg-red-700 text-white font-bold py-1 px-2 rounded"
                onClick={() => {
                  updateFilesStatus({
                    status: "missing",
                    storage_device_id: storageDevice.id,
                    file_ids: selectedFiles,
                  });
                  setSelectedFiles([]);
                }}>
                Mark Missing
              </button>
              <button
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded"
                onClick={() => {
                  updateFilesStatus({
                    status: "watched",
                    storage_device_id: storageDevice.id,
                    file_ids: selectedFiles,
                  });
                  setSelectedFiles([]);
                }}>
                Mark Watched
              </button>
              <button
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-1 px-2 rounded"
                onClick={() => {
                  updateFilesStatus({
                    status: "ignored",
                    storage_device_id: storageDevice.id,
                    file_ids: selectedFiles,
                  });
                  setSelectedFiles([]);
                }}>
                Ignore
              </button>
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
                onClick={() => {
                  createTask({
                    name: `Transfer ${selectedFiles.length} Files`,
                    func: "transfer_some_files",
                    args: [storageDevice.id, selectedFiles],
                    kwargs: {},
                  });
                  setSelectedFiles([]);
                }}>
                Transfer
              </button>
            </div>
          )}
          {/* Files */}
          <div className="flex flex-col gap-2 p-2 mt-1 rounded max-h-[80vh] overflow-y-scroll drop-shadow bg-slate-800">
            {groupedFiles?.length === 0 ? (
              <>
                <p className="text-white text-center">No Files</p>
                <button
                  className="bg-blue-500 enabled:hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
                  onClick={() => {
                    setFilter("all");
                    setTitleFilter("");
                  }}>
                  Clear Filters
                </button>
              </>
            ) : (
              groupedFiles
                ?.filter(file =>
                  file.type === "series" ? file.filtered_file_count > 0 : true
                )
                ?.map(file =>
                  file.type === "file" ? (
                    <FileCard
                      key={file.title || file.series_name}
                      file={file}
                      storageDevice={storageDevice}
                      selectedFiles={selectedFiles}
                      setSelectedFiles={setSelectedFiles}
                      updateFile={updateFile}
                      createTask={createTask}
                    />
                  ) : file.type === "series" ? (
                    <div className="text-white p-2 bg-slate-600 rounded flex flex-col gap-y-1">
                      <div className="flex flex-col sm:flex-row gap-x-1">
                        <div className="flex flex-col gap-1 align-middle">
                          {/* input for all files in the series
                        partially check if any files are selected
                        fully check if all are selected
                         */}
                          <input
                            type="checkbox"
                            className="h-5 w-5 rounded"
                            checked={file.filtered_file_ids.every(id =>
                              selectedFiles.includes(id)
                            )}
                            onChange={e => {
                              if (e.target.checked) {
                                setSelectedFiles([
                                  ...selectedFiles,
                                  ...file.filtered_file_ids,
                                ]);
                              } else {
                                setSelectedFiles(
                                  selectedFiles.filter(
                                    id => !file.filtered_file_ids.includes(id)
                                  )
                                );
                              }
                            }}
                          />
                        </div>
                        <div className="grow truncate">
                          <div>
                            <b className="">{file.series_name}</b>
                          </div>
                          <span className="text-sm px-1.5 py-0.5 rounded bg-slate-800 mr-1">
                            <b>Filtered</b>: {file.filtered_file_count} files |{" "}
                            {bitsToGB(file.filtered_file_size)}
                          </span>
                          <span className="text-sm px-1.5 py-0.5 rounded bg-slate-800 mr-1">
                            <b>Total</b>: {file.file_count} files |{" "}
                            {bitsToGB(file.file_size)}
                          </span>
                        </div>
                      </div>
                      <Disclosure className="rounded" as="div">
                        <Disclosure.Button
                          className="bg-slate-800 hover:bg-slate-900 text-white font-bold py-1 px-2 rounded w-full"
                          onClick={refetchFiles}>
                          {({ open }) =>
                            open ? "Hide Seasons" : "Show Seasons"
                          }
                        </Disclosure.Button>
                        <Disclosure.Panel className="flex flex-col gap-y-1 mt-2">
                          {Object.values(file.seasons)
                            ?.filter(season => season.filtered_file_count > 0)
                            ?.map(season => (
                              <div
                                key={season.season_no}
                                className="text-white p-2 bg-slate-800 rounded flex flex-col gap-y-1">
                                <div className="flex flex-col sm:flex-row gap-x-1">
                                  <div className="flex flex-col gap-1 align-middle">
                                    <input
                                      type="checkbox"
                                      className="h-5 w-5 rounded"
                                      checked={season.filtered_file_ids.every(
                                        id => selectedFiles.includes(id)
                                      )}
                                      onChange={e => {
                                        if (e.target.checked) {
                                          setSelectedFiles([
                                            ...selectedFiles,
                                            ...season.filtered_file_ids,
                                          ]);
                                        } else {
                                          setSelectedFiles(
                                            selectedFiles.filter(
                                              id =>
                                                !season.filtered_file_ids.includes(
                                                  id
                                                )
                                            )
                                          );
                                        }
                                      }}
                                    />
                                  </div>
                                  <div className="grow truncate">
                                    <div>
                                      <b className="">
                                        Season {season.season_no}
                                      </b>
                                    </div>
                                    <span className="text-sm px-1.5 py-0.5 rounded bg-slate-600 mr-1">
                                      {season.filtered_file_count} filtered |{" "}
                                      {season.file_count} files
                                    </span>
                                    <span className="text-sm px-1.5 py-0.5 rounded bg-slate-600 mr-1">
                                      {bitsToGB(season.filtered_file_size)}{" "}
                                      filtered | {bitsToGB(season.file_size)}
                                    </span>
                                  </div>
                                </div>
                                <Disclosure>
                                  <Disclosure.Button className="bg-slate-600 hover:bg-slate-900 text-white font-bold py-1 px-2 rounded w-full">
                                    {({ open }) =>
                                      open ? "Hide Files" : "Show Files"
                                    }
                                  </Disclosure.Button>
                                  <Disclosure.Panel className="flex flex-col gap-1">
                                    {season.filtered_files.map(file => (
                                      <FileCard
                                        key={file.title}
                                        file={file}
                                        storageDevice={storageDevice}
                                        selectedFiles={selectedFiles}
                                        setSelectedFiles={setSelectedFiles}
                                        updateFile={updateFile}
                                        createTask={createTask}
                                      />
                                    ))}
                                  </Disclosure.Panel>
                                </Disclosure>
                              </div>
                            ))}
                        </Disclosure.Panel>
                      </Disclosure>
                    </div>
                  ) : null
                )
            )}
          </div>
        </Disclosure.Panel>
      </Disclosure>
    </div>
  );
};

export default StorageDeviceCard;
