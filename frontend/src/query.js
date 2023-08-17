import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

export const gatoClient = axios.create({
  baseURL:
    process.env.NODE_ENV === "development"
      ? "http://localhost:8000/api"
      : "/api",
  crossDomain: "true",
  withCookie: true,
  timeout: 1000 * 30,
  responseType: "json",
  responseEncoding: "utf8",
  headers: {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Origin, Content-Type, X-Auth-Token",
  },
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

export const useGetTasks = () =>
  useQuery(["tasks"], () => gatoClient.get("/tasks/").then(res => res.data), {
    refetchInterval: 1000,
    refetchIntervalInBackground: false,
  });

export const useCreateTask = () => {
  const queryClient = useQueryClient();
  return useMutation(task => gatoClient.post("/tasks/", task), {
    onSuccess: () => {
      queryClient.invalidateQueries("tasks");
    },
  });
};

export const useDeleteTask = () => {
  const queryClient = useQueryClient();
  return useMutation(id => gatoClient.delete(`/tasks/${id}/`), {
    onSuccess: () => {
      queryClient.invalidateQueries("tasks");
    },
  });
};

export const useGetStorageDevices = () =>
  useQuery(["storage_devices"], () =>
    gatoClient.get("/storage_devices/").then(res => res.data)
  );

export const useCreateStorageDevice = () => {
  const queryClient = useQueryClient();
  return useMutation(
    storageDevice => gatoClient.post("/storage_devices/", storageDevice),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("storage_devices");
      },
    }
  );
};

export const useGetFiles = storage_device_id =>
  useQuery(["files", storage_device_id], () =>
    gatoClient
      .get(`/storage_devices/${storage_device_id}/files/`)
      .then(res => res.data)
  );
