const API_BASE_URL = '/api';    // ALL REQUESTS ARE SENT TO PATHS UNDER /api
// (VITE PROXIES THIS TO OUR FLASK SERVER, keeps url short in app code.)

/**
 * this is a thin fetch wrapper:
 * - ALWAYS includes cookies
 * - retries once on 401 by POST /auth/refresh, then replays original request
 * - parses JSON and throws rich errors
 */
export async function request(path, { retry = true, ...options } = {}) {
  
  // first we fetch, we "include" credentials to every request so HttpOnly cookies
  // (access/refresh) go along, basically the browser automatically attaches the cookies
  // to every request that matches the API domain.

  // when you log in, the backend sets httponly cookies and the browser stores them
  // so on any future request, including auth/refresh, the cookies go along automatically

  // we wanna avoid manually passing headers like headers: {"Authorization": `Bearer${token}`}
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...options,
  });

  if (res.status === 401 && retry) {
    // if we get a 401 refresh once
    const r = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (r.ok) { // if succeeded replay original request (retry false to avoid loops)
      return request(path, { ...options, retry: false });
    }
  }

  // try to parse json response regardless...
  let data = null;
  try { data = await res.json(); } catch {}

  if (!res.ok) {  // refresh fails, throw error.
    const err = new Error(data?.message || `Request failed (${res.status})`);
    err.status = res.status;
    err.payload = data;
    throw err;
  }
  return data;
}

export { API_BASE_URL };
