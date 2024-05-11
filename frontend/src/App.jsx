import { ErrorMessage, Field, Form, Formik } from "formik";
import CreateStorageDevice from "./CreateStorageDevice";
import Loading from "./Loading";
import StorageDeviceCard from "./StorageDeviceCard";
import TaskCard from "./TaskCard";
import {
  useAddAuth,
  useAddServer,
  useGetCheckConfig,
  useGetStorageDevices,
  useGetTasks,
} from "./query";
import { bitsToGB } from "./util";

function App() {
  const {
    data: config,
    status: configStatus,
    error: configError,
  } = useGetCheckConfig();
  const { data: tasks, status: tasksStatus, error: tasksError } = useGetTasks();
  const {
    data: storageDevices,
    status: storageDevicesStatus,
    error: storageDevicesError,
  } = useGetStorageDevices();
  const { mutate: addAuth } = useAddAuth();
  const { mutate: addServer } = useAddServer();
  return (
    <Loading
      statuses={[configStatus, tasksStatus, storageDevicesStatus]}
      errors={[configError, tasksError, storageDevicesError]}
      className="bg-gray-900 w-screen h-screen text-white overflow-auto">
      <div className="top-0 sticky w-full bg-slate-950 py-2 px-3 flex z-10 opacity-90">
        <h1 className="text-white text-2xl font-semibold rounded bg-slate-800 shrink px-1">
          GatoSnap
        </h1>
      </div>
      <div className="flex container mx-auto flex-col sm:flex-col">
        {config?.auth_token && config?.server ? (
          <>
            <div className="flex flex-row">
              <div className="w-1/2">
                <h2 className="text-white text-center text-2xl font-semibold">
                  Tasks (
                  {tasks?.filter(task => task.func !== "transfer_file").length})
                </h2>
                <div className="flex flex-col overflow-y-auto max-h-[40vh]">
                  {tasks
                    ?.filter(task => task.func !== "transfer_file")
                    ?.sort((a, b) => -(a.progress - b.progress))
                    ?.map(task => <TaskCard key={task.id} task={task} />) || (
                    <p className="text-white text-center">No tasks running</p>
                  )}
                </div>
              </div>
              <div className="w-1/2">
                <h2 className="text-white text-center text-2xl font-semibold">
                  Transfers
                </h2>
                <div className="mx-2">
                  {tasks?.filter(task => task.func === "transfer_file").length}{" "}
                  Transfers |{" "}
                  {
                    tasks
                      ?.filter(task => task.func === "transfer_file")
                      ?.filter(task =>
                        ["running", "pending"].includes(task.status)
                      ).length
                  }{" "}
                  To Do |{" "}
                  {
                    tasks
                      ?.filter(task => task.func === "transfer_file")
                      ?.filter(task => task.status === "success").length
                  }{" "}
                  Successful |{" "}
                  {bitsToGB(
                    tasks
                      ?.filter(task => task.func === "transfer_file")
                      ?.filter(task =>
                        ["running", "pending"].includes(task.status)
                      )
                      .reduce((acc, task) => acc + task.progress, 0)
                  )}{" "}
                  /{" "}
                  {bitsToGB(
                    tasks
                      ?.filter(task => task.func === "transfer_file")
                      ?.filter(task =>
                        ["running", "pending"].includes(task.status)
                      )
                      .reduce((acc, task) => acc + task.total, 0)
                  )}
                </div>
                <div className="overflow-y-auto max-h-[40vh]">
                  {tasks
                    ?.filter(task => task.func === "transfer_file")
                    ?.sort(
                      (a, b) =>
                        a.status === "running" && b.status !== "running" && -1
                    )
                    ?.map(task => <TaskCard key={task.id} task={task} />) || (
                    <p className="text-white text-center">
                      No transfers running
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div className="">
              <h2 className="text-white text-center text-2xl font-semibold">
                Storage Devices
              </h2>
              <CreateStorageDevice />
              {storageDevices?.map(storageDevice => (
                <StorageDeviceCard
                  key={storageDevice.id}
                  storageDevice={storageDevice}
                />
              ))}
            </div>
          </>
        ) : !config?.auth_token ? (
          <div className="mx-auto rounded p-2 bg-slate-600 h-min mt-2">
            <h1 className="text-white text-2xl font-semibold">Setup Plex</h1>
            <Formik
              initialValues={{ username: "", password: "" }}
              onSubmit={async (values, { setSubmitting }) => {
                addAuth(values);
                setSubmitting(false);
              }}>
              {({ isSubmitting }) => (
                <Form className="flex flex-col gap-y-2">
                  <div className="flex flex-col">
                    <label htmlFor="username">Username</label>
                    <Field
                      type="text"
                      name="username"
                      placeholder="Username"
                      className="mx-1 px-1 rounded text-black"
                    />
                    <ErrorMessage name="username" component="div" />
                  </div>
                  <div className="flex flex-col">
                    <label htmlFor="password">Password</label>
                    <Field
                      type="password"
                      name="password"
                      placeholder="Password"
                      className="mx-1 px-1 rounded text-black"
                    />
                    <ErrorMessage name="password" component="div" />
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded">
                    Login
                  </button>
                </Form>
              )}
            </Formik>
          </div>
        ) : (
          <div className="mx-auto rounded p-2 bg-slate-600 h-min mt-2">
            <h1 className="text-white text-2xl font-semibold">Setup Server</h1>
            <Formik
              initialValues={{ server: "" }}
              onSubmit={async (values, { setSubmitting }) => {
                await addServer(values);
                setSubmitting(false);
              }}>
              {({ isSubmitting }) => (
                <Form className="flex flex-col gap-y-2">
                  <div className="flex flex-col">
                    <label htmlFor="server">Server</label>
                    <Field
                      type="text"
                      name="server"
                      placeholder="Server"
                      className="mx-1 px-1 rounded text-black"
                    />
                    <ErrorMessage name="server" component="div" />
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded">
                    Save Server
                  </button>
                </Form>
              )}
            </Formik>
          </div>
        )}
      </div>
    </Loading>
  );
}

export default App;
