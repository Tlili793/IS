const MS1_ENDPOINT = import.meta.env.VITE_MS1_ENDPOINT ?? '/api/ms1/hello';

export async function fetchMs1Hello(token) {
  const response = await fetch(MS1_ENDPOINT, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (response.status === 401) {
    const error = new Error('The access token was rejected by the gateway.');
    error.status = 401;
    throw error;
  }

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `MS1 request failed with status ${response.status}`);
  }

  return response.json();
}
