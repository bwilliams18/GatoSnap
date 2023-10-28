import { Disclosure } from "@headlessui/react";
import LoadingCircle from "./LoadingCircle";

const Loading = ({
  statuses = ["loading"],
  errors = [],
  children,
  wrap = true,
  ...props
}) => {
  // status can be "idle", "loading", "success", "error"
  // if all statuses are "success", then status is "success"
  // if any status is "error", then status is "error"
  // if any status is "loading", then status is "loading"
  // if all statuses are "idle", then status is "idle"
  const status = statuses.reduce((acc, status) => {
    if (acc === null) return status;
    if (acc === "error") return acc;
    if (status === "error") return "error";
    if (acc === "loading") return acc;
    if (status === "loading") return "loading";
    if (acc === "idle") return acc;
    if (status === "idle") return "idle";
    return "success";
  }, null);
  switch (status) {
    case "success":
      return wrap ? <div {...props}>{children}</div> : <>{children}</>;
    case "error":
      return (
        <div {...props}>
          <div className="flex flex-col bg-white rounded-3xl justify-center align-middle shrink text-black my-auto">
            <h2 className="text-center text-3xl font-bold my-3 text-red-600 shrink">
              Something went wrong
            </h2>
            <Disclosure>
              {({ open }) => (
                <div className="text-center">
                  <Disclosure.Button className="text-red-600 border border-red-600 rounded-md px-2 py-1">
                    {open ? "Hide" : "Show"} Details
                  </Disclosure.Button>

                  <Disclosure.Panel>
                    <pre className="text-center shrink">
                      {errors
                        .filter(error => error)
                        .map((error, idx) => (
                          <div key={idx}>
                            "{error?.config?.url}":{error?.message}
                          </div>
                        ))}
                    </pre>
                  </Disclosure.Panel>
                </div>
              )}
            </Disclosure>
            <img
              src="/crash_low.png"
              alt="error"
              className="object-contain w-1/2 m-auto"
            />
          </div>
        </div>
      );
    case "idle":
    case "loading":
    default:
      return (
        <div {...props}>
          <h1 className="text-center text-2xl m-auto capitalize">
            {status}
            {status === "loading" && (
              <LoadingCircle className="ml-2 -mr-1 h-5 w-5 text-white inline-block" />
            )}
          </h1>
        </div>
      );
  }
};

export default Loading;
