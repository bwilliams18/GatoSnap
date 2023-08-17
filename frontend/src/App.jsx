import CreateStorageDevice from "./CreateStorageDevice";
import StorageDeviceCard from "./StorageDeviceCard";
import TaskCard from "./TaskCard";
import { useGetStorageDevices, useGetTasks } from "./query";

function App() {
  const { data: tasks, isLoading, error } = useGetTasks();
  const { data: storageDevices } = useGetStorageDevices();
  return (
    <div className="bg-gray-900 w-screen h-screen text-white overflow-scroll flex px-8">
      <div className="w-1/2">
        <h1 className="text-white text-center text-2xl font-semibold">
          Storage Devices
        </h1>
        <CreateStorageDevice />
        {storageDevices?.map(storageDevice => (
          <StorageDeviceCard
            key={storageDevice.id}
            storageDevice={storageDevice}
          />
        ))}
      </div>
      <div className="w-1/2">
        <h1 className="text-white text-center text-2xl font-semibold">Tasks</h1>
        {isLoading && <p className="text-white">Loading...</p>}
        {error && <p className="text-white">Error</p>}
        {tasks
          ?.filter(task => task.func !== "transfer_file")
          ?.sort((a, b) => -(a.progress - b.progress))
          ?.map(task => <TaskCard key={task.id} task={task} />) || (
          <p className="text-white text-center">No tasks running</p>
        )}
        {
          <div>
            <h2 className="text-white text-center text-xl font-semibold">
              Transfers
            </h2>
            {tasks
              ?.filter(task => task.func === "transfer_file")
              ?.filter(task => task.progress !== task.total || task.total === 0)
              ?.sort((a, b) => a.progress / a.total - b.progress / b.total)
              ?.map(task => <TaskCard key={task.id} task={task} />) || (
              <p className="text-white text-center">No transfers running</p>
            )}
          </div>
        }
      </div>
    </div>
  );
}

export default App;
