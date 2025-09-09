const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
// remember in vite env vars are accessed via meta.env


// a thin wrapper around fetch that always reduces cookies
// retries once on 401 by calling auth/refresh (again, cookies)
// parses json and throws errors
async function request(path, {retry = true, ...options} = {}) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
        credentials: 'include',
        ...options,
    });

// path (endpt we wanna call, retry is obvs, ...options any other options
// youd normaly pass to fetch() like method, headers, body)

    if (res.status == 401 && retry) {
        // lets try to refresh once
        const r = await fetch()(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            credentials: 'include',
          });
          if (r.ok) {
            // retry original request once
            return request(path, { ...options, retry: false });
          }
        }
      
    // try to parse json either way
    let data;
    try {
        data = await res.json();
    } catch {
        data = null;
    }

    if (!res.ok) {
        const message = data?.message || `Request failed (${res.status})`;
        const err = new Error(message);
        err.status = res.status;
        err.payload = data;
        throw err; // womp womp
    }

    return data;
}

export {request, API_BASE_URL}