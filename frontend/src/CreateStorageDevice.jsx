import { Disclosure } from "@headlessui/react";
import { ErrorMessage, Field, Form, Formik } from "formik";
import React from "react";
import { useCreateStorageDevice } from "./query";

const CreateStorageDevice = () => {
  const { mutate: createStorageDevice } = useCreateStorageDevice();
  return (
    <Disclosure>
      <Disclosure.Button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded my-2">
        Create Storage Device
      </Disclosure.Button>
      <Disclosure.Panel className="flex flex-col gap-2 m-2 bg-slate-600 p-2 rounded ">
        <Formik
          initialValues={{ name: "", base_path: "" }}
          onSubmit={(values, { setSubmitting }) => {
            createStorageDevice(values);
            setSubmitting(false);
          }}>
          {({ isSubmitting }) => (
            <Form className="gap-1 flex flex-col">
              <div>
                <label htmlFor="name">Name:</label>
                <Field
                  type="text"
                  name="name"
                  placeholder="Name"
                  className="mx-1 px-1 rounded text-black"
                />
                <ErrorMessage name="name" component="div" />
              </div>
              <div>
                <label htmlFor="base_path">Path</label>
                <Field
                  type="text"
                  name="base_path"
                  placeholder="Path"
                  className="mx-1 px-1 rounded text-black"
                />
                <ErrorMessage name="path" component="div" />
              </div>
              <div>
                <Field type="checkbox" name="sync_on_deck" />
                <label htmlFor="sync_on_deck">Sync on Deck</label>

                <ErrorMessage name="sync_on_deck" component="div" />
              </div>
              <div>
                <Field type="checkbox" name="sync_continue_watching" />
                <label htmlFor="sync_continue_watching">
                  Sync Continue Watching
                </label>
                <ErrorMessage name="sync_continue_watching" component="div" />
              </div>
              <div>
                <Field
                  type="text"
                  name="sync_playlist"
                  placeholder="Sync Playlist"
                  className="mx-1 px-1 rounded text-black"
                />
                <ErrorMessage name="sync_playlist" component="div" />
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-800 text-white font-bold py-1 px-2 rounded my-2">
                Submit
              </button>
            </Form>
          )}
        </Formik>
      </Disclosure.Panel>
    </Disclosure>
  );
};

export default CreateStorageDevice;
