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
const patchJSON = (path, data) => 
  request(path, {
    method: "PATCH", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data),
  });

// get me!

export const getMe = () => get("/api/me");

// authentication and signup endpoints

export const login    = ({ email, password }) => postJSON("/api/auth/login", { email, password });
export const logout   = () => request("/api/auth/logout", { method: "POST" });
export const refresh  = () => request("/api/auth/refresh", { method: "POST" });

export const registerStudent = (formData) => postForm("/api/students", formData);
export const registerTeacher = (formData) => postForm("/api/teachers", formData);
export const registerParent  = (formData) => postForm("/api/parents",  formData);

// classes API

export const createClass = (className) => postJSON("/api/classes", { class_name: className });
export const getClasses  = () => get("/api/classes");

// Class Subresources

export const getClassStudents = (class_id) => get(`/api/classes/${class_id}/students`); // teacher student list
export const getMyChildren = () => get("/api/parents/children");
export const parentSendChildRequest = (email) => postJSON("/api/parents/family/requests/", { email });
// export const getMyChildClasses = (childId) => get(`/api/parents/children/${childId}/classes`); 
// export const getChildAttendanceInClass = (childId, classId) => get(`/api/parents/children/${childId}/classes/${classId}/attendance`);
// export const getMyAttendanceInClass = (classId) => get(`/api/classes/${classId}/attendance/me`); // student self

export const getStudentFamilyRequests = (status = "pending") =>
  get(`/api/students/family/requests/?status=${encodeURIComponent(status)}`);;

export const getStudentClassInvites = (status = "pending") =>
  get(`/api/students/classes/requests?status=${encodeURIComponent(status)}`);

// respond actions (unchanged names, just reminding)
export const studentRespondToParentRequest = (request_id, response) =>
  patchJSON(`/api/students/family/requests/${request_id}`, { response });

export const studentRespondToClassInvite = (request_id, response) =>
  patchJSON(`/api/students/classes/requests/${request_id}`, { response });

export const getMyParentsAsStudent = () => get("/api/students/family");

export const getStudentIncomingFamilyRequests = (status="pending") =>
  request(`/api/students/family/requests?status=${encodeURIComponent(status)}`, { method: "GET" });

export const getParentIncomingFamilyRequests = (status="pending") =>
  get(`/api/parents/family/requests/incoming?status=${encodeURIComponent(status)}`);

export const getParentOutgoingFamilyRequests = (status="pending") =>
  get(`/api/parents/family/requests/outgoing?status=${encodeURIComponent(status)}`);

export const parentRespondToStudentRequest = (requestId, response) =>
  request(`/api/parents/family/requests/${requestId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ response }),
  });

export const getClassCode = (class_id) =>
  get(`/api/classes/${class_id}/code`);

export const removeStudentFromClass = (class_id, student_id) =>
  request(`/api/teachers/classes/${class_id}/requests/${student_id}`, { method: "DELETE" });

// OPTIONAL (attendance today) — add only if you add the backend below
export const getTodayAttendanceForClass = (class_id) =>
  get(`/api/classes/${class_id}/attendance/today`);

export const teacherInviteStudent = (class_id, email) =>
  request(`/api/teachers/classes/${class_id}/requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

// JOIN: student -> class (by class code)
// Backend route requires a class_id in the path but ignores it; 0 is fine.
export const studentJoinClassByCode = (code) =>
  request(`/api/students/classes/requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });


export const getTeacherClassJoinRequests = (class_id, status = "pending") =>
  request(`/api/teachers/classes/${class_id}/requests?status=${encodeURIComponent(status)}`, {
    method: "GET",
  });

export const teacherRespondToJoinRequest = (class_id, request_id, response) =>
  request(`/api/teachers/classes/${class_id}/requests/${request_id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ response }),
  });

  export const getStudentClassMeta = (class_id) =>
  request(`/api/students/classes/${class_id}/meta`, { method: "GET" });

export const getStudentAttendanceToday = (class_id) =>
  request(`/api/students/classes/${class_id}/attendance/today`, { method: "GET" });

export const getStudentAttendanceHistory = (class_id, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  const url = qs ? `/api/students/classes/${class_id}/attendance?${qs}` 
                 : `/api/students/classes/${class_id}/attendance`;
  return request(url, { method: "GET" });
};

// Parent -> child classes
export const getChildClasses = (student_id) =>
  request(`/api/parents/children/${student_id}/classes`, { method: "GET" });

// Parent -> child class meta / attendance
export const getParentChildClassMeta = (student_id, class_id) =>
  request(`/api/parents/children/${student_id}/classes/${class_id}/meta`, { method: "GET" });

export const getParentChildAttendanceToday = (student_id, class_id) =>
  request(`/api/parents/children/${student_id}/classes/${class_id}/attendance/today`, { method: "GET" });

export const getParentChildAttendanceHistory = (student_id, class_id, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  const url = qs
    ? `/api/parents/children/${student_id}/classes/${class_id}/attendance?${qs}`
    : `/api/parents/children/${student_id}/classes/${class_id}/attendance`;
  return request(url, { method: "GET" });
};
export const studentSendParentRequest = (email) =>
  postJSON("/api/students/family/requests/", { email });

export async function markAttendanceFromFrame(classId, blob) {
  const form = new FormData();
  form.append("frame", blob, "frame.jpg");
  return request(`spi/classes/${classId}/attendance/mark`, {
    method: "POST",
    body: form,
  });
}