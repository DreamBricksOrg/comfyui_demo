import axios from "axios";

const BASE_API = "https://dbdemo.ngrok.app/api";

export const API = axios.create({
  baseURL: BASE_API,
});

export const uploadImage = async (file: File, workflow: string) => {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("workflow", workflow);

  const response = await axios.post(`${BASE_API}/test`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const getJobStatus = async (jobId: string) => {
  const response = await API.get(`/result`, {
    params: { request_id: jobId },
  });

  return response.data;
};
