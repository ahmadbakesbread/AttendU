import { request } from "./apiClient";    // import the request wrapper we made around fetch() .

// this is the central api layer of the app. it bridges the frontend and backend.

const get = (path) => request(path, { method: "GET" });     // simple get helper
const postJSON = (path, data) =>                            // simple post helper convert javascript obj into json data
  request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });                 
const postForm = (path, formData) =>                        // simple post helper convert javascript obj into form data
  request(path, { method: "POST", body: formData });

// authentication and signup endpoints

export const login    = ({ email, password }) => postJSON("/auth/login", { email, password });
export const logout   = () => request("/auth/logout", { method: "POST" });
export const refresh  = () => request("/auth/refresh", { method: "POST" });

export const registerStudent = (formData) => postForm("/students", formData);
export const registerTeacher = (formData) => postForm("/teachers", formData);
export const registerParent  = (formData) => postForm("/parents",  formData);

// classes API

export const createClass = (className) => postJSON("/classes", { class_name: className });
export const getClasses  = () => get("/classes");
