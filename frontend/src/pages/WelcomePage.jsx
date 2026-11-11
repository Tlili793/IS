import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../auth/LoginController';
import { fetchMs1Hello } from '../api/ms1';

export default function WelcomePage() {
  const { username, name, email, token, keycloak, logout } = useAuth();
  const displayName = name || username;
  const [msResult, setMsResult] = useState(null);
  const [msStatus, setMsStatus] = useState('loading');
  const [msError, setMsError] = useState(null);

  const loadMicroservices = useCallback(async () => {
    setMsStatus('loading');
    setMsError(null);

    try {
      let result;

      try {
        result = await fetchMs1Hello(token);
      } catch (error) {
        if (error.status !== 401) {
          throw error;
        }

        await keycloak.updateToken(-1);
        result = await fetchMs1Hello(keycloak.token);
      }

      setMsResult(result);
      setMsStatus('success');
    } catch (error) {
      setMsError(error.message);
      setMsStatus('error');
    }
  }, [keycloak, token]);

  useEffect(() => {
    if (token) {
      loadMicroservices();
    }
  }, [token, loadMicroservices]);

  return (
    <main className="center-screen">
      <section className="card">
        <p className="eyebrow">Login successful</p>
        <h1>Welcome{displayName ? `, ${displayName}` : ''}!</h1>
        <p className="muted">You are authenticated with Keycloak.</p>

        <dl className="user-details">
          <div>
            <dt>Username</dt>
            <dd>{username ?? '-'}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{email ?? '-'}</dd>
          </div>
        </dl>

        <section className="microservice-panel">
          <h2>Microservice response</h2>
          {msStatus === 'loading' && <p>Calling MS1 through the gateway...</p>}
          {msStatus === 'error' && <p className="error-text">{msError}</p>}
          {msStatus === 'success' && msResult && (
            <dl className="user-details">
              <div>
                <dt>MS1</dt>
                <dd>{msResult.message ?? msResult.ms1 ?? '-'}</dd>
              </div>
              <div>
                <dt>MS2</dt>
                <dd>{msResult.ms2 ?? '-'}</dd>
              </div>
              <div>
                <dt>Final response</dt>
                <dd>{msResult.result ?? '-'}</dd>
              </div>
            </dl>
          )}
          <button type="button" className="secondary-button" onClick={loadMicroservices}>
            Call MS1 again
          </button>
        </section>

        <details>
          <summary>JWT access token</summary>
          <pre>{token ?? 'No token available'}</pre>
        </details>

        <button type="button" onClick={logout}>
          Log out
        </button>
      </section>
    </main>
  );
}
