import { startTransition, useEffect, useEffectEvent, useState } from 'react'
import './App.css'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'primetradeai_access_token'

const emptyTaskForm = {
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
}

const emptyRegisterForm = {
  email: '',
  username: '',
  password: '',
}

const emptyLoginForm = {
  email: '',
  password: '',
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) ?? '')
  const [user, setUser] = useState(null)
  const [tasks, setTasks] = useState([])
  const [selectedTaskId, setSelectedTaskId] = useState(null)
  const [taskForm, setTaskForm] = useState(emptyTaskForm)
  const [registerForm, setRegisterForm] = useState(emptyRegisterForm)
  const [loginForm, setLoginForm] = useState(emptyLoginForm)
  const [authMode, setAuthMode] = useState('login')
  const [filters, setFilters] = useState({
    search: '',
    status_filter: '',
    priority_filter: '',
  })
  const [statusMessage, setStatusMessage] = useState({
    type: 'idle',
    text: 'Connect frontend to backend and test full auth flow.',
  })
  const [busy, setBusy] = useState({
    auth: false,
    profile: false,
    tasks: false,
    saveTask: false,
  })

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
      void bootstrapSession(token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }, [token])

  async function apiRequest(path, options = {}) {
    const headers = new Headers(options.headers ?? {})

    if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    })

    if (response.status === 204) {
      return null
    }

    const contentType = response.headers.get('content-type') ?? ''
    const payload = contentType.includes('application/json')
      ? await response.json()
      : await response.text()

    if (!response.ok) {
      const detail =
        typeof payload === 'object' && payload && 'detail' in payload
          ? payload.detail
          : 'Request failed'
      throw new Error(String(detail))
    }

    return payload
  }

  const bootstrapSession = useEffectEvent(async (activeToken) => {
    setBusy((current) => ({ ...current, profile: true, tasks: true }))

    try {
      const [profile, taskPayload] = await Promise.all([
        fetchWithToken('/users/me', activeToken),
        fetchWithToken('/tasks/', activeToken),
      ])

      setUser(profile)
      startTransition(() => {
        setTasks(taskPayload.tasks ?? [])
      })
      setStatusMessage({
        type: 'success',
        text: `Signed in as ${profile.username}.`,
      })
    } catch (error) {
      clearSession()
      setStatusMessage({
        type: 'error',
        text: error.message || 'Session expired.',
      })
    } finally {
      setBusy((current) => ({ ...current, profile: false, tasks: false }))
    }
  })

  async function fetchWithToken(path, activeToken) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        Authorization: `Bearer ${activeToken}`,
      },
    })

    const payload = response.status === 204 ? null : await response.json()

    if (!response.ok) {
      const detail =
        payload && typeof payload === 'object' && 'detail' in payload
          ? payload.detail
          : 'Request failed'
      throw new Error(String(detail))
    }

    return payload
  }

  function clearSession() {
    setToken('')
    setUser(null)
    setTasks([])
    setSelectedTaskId(null)
    setTaskForm(emptyTaskForm)
  }

  async function handleRegister(event) {
    event.preventDefault()
    setBusy((current) => ({ ...current, auth: true }))

    try {
      await apiRequest('/users/', {
        method: 'POST',
        body: JSON.stringify(registerForm),
      })
      setRegisterForm(emptyRegisterForm)
      setAuthMode('login')
      setStatusMessage({
        type: 'success',
        text: 'Registration complete. Login with new account.',
      })
    } catch (error) {
      setStatusMessage({
        type: 'error',
        text: error.message || 'Registration failed.',
      })
    } finally {
      setBusy((current) => ({ ...current, auth: false }))
    }
  }

  async function handleLogin(event) {
    event.preventDefault()
    setBusy((current) => ({ ...current, auth: true }))

    try {
      const body = new URLSearchParams()
      body.set('username', loginForm.email)
      body.set('password', loginForm.password)

      const payload = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
      }).then(async (response) => {
        const data = await response.json()
        if (!response.ok) {
          throw new Error(data.detail || 'Login failed.')
        }
        return data
      })

      setLoginForm(emptyLoginForm)
      setToken(payload.access_token)
    } catch (error) {
      setStatusMessage({
        type: 'error',
        text: error.message || 'Login failed.',
      })
    } finally {
      setBusy((current) => ({ ...current, auth: false }))
    }
  }

  async function loadTasks(extraMessage) {
    setBusy((current) => ({ ...current, tasks: true }))

    try {
      const params = new URLSearchParams()

      if (filters.search.trim()) {
        params.set('search', filters.search.trim())
      }
      if (filters.status_filter) {
        params.set('status_filter', filters.status_filter)
      }
      if (filters.priority_filter) {
        params.set('priority_filter', filters.priority_filter)
      }

      const query = params.toString() ? `?${params.toString()}` : ''
      const payload = await apiRequest(`/tasks/${query}`)
      startTransition(() => {
        setTasks(payload.tasks ?? [])
      })

      if (extraMessage) {
        setStatusMessage({
          type: 'success',
          text: extraMessage,
        })
      }
    } catch (error) {
      setStatusMessage({
        type: 'error',
        text: error.message || 'Could not load tasks.',
      })
    } finally {
      setBusy((current) => ({ ...current, tasks: false }))
    }
  }

  async function handleTaskSubmit(event) {
    event.preventDefault()
    setBusy((current) => ({ ...current, saveTask: true }))

    try {
      if (selectedTaskId) {
        await apiRequest(`/tasks/${selectedTaskId}`, {
          method: 'PATCH',
          body: JSON.stringify(taskForm),
        })
        await loadTasks('Task updated.')
      } else {
        await apiRequest('/tasks/', {
          method: 'POST',
          body: JSON.stringify(taskForm),
        })
        await loadTasks('Task created.')
      }

      setSelectedTaskId(null)
      setTaskForm(emptyTaskForm)
    } catch (error) {
      setStatusMessage({
        type: 'error',
        text: error.message || 'Could not save task.',
      })
    } finally {
      setBusy((current) => ({ ...current, saveTask: false }))
    }
  }

  async function handleEditTask(taskId) {
    try {
      const task = await apiRequest(`/tasks/${taskId}`)
      setSelectedTaskId(task.id)
      setTaskForm({
        title: task.title,
        description: task.description ?? '',
        status: task.status,
        priority: task.priority,
      })
      setStatusMessage({
        type: 'success',
        text: `Editing task #${task.id}.`,
      })
    } catch (error) {
      setStatusMessage({
        type: 'error',
        text: error.message || 'Could not load task.',
      })
    }
  }

  async function handleDeleteTask(taskId) {
    try {
      await apiRequest(`/tasks/${taskId}`, { method: 'DELETE' })

      if (selectedTaskId === taskId) {
        setSelectedTaskId(null)
        setTaskForm(emptyTaskForm)
      }

      await loadTasks('Task deleted.')
    } catch (error) {
      setStatusMessage({
        type: 'error',
        text: error.message || 'Could not delete task.',
      })
    }
  }

  function handleTaskFormChange(event) {
    const { name, value } = event.target
    setTaskForm((current) => ({ ...current, [name]: value }))
  }

  function handleFilterChange(event) {
    const { name, value } = event.target
    setFilters((current) => ({ ...current, [name]: value }))
  }

  function renderAuthCard() {
    if (authMode === 'register') {
      return (
        <form className="panel auth-panel" onSubmit={handleRegister}>
          <div className="panel-heading">
            <p className="eyebrow">Register</p>
            <h2>Create account</h2>
          </div>

          <label>
            <span>Email</span>
            <input
              required
              type="email"
              value={registerForm.email}
              onChange={(event) =>
                setRegisterForm((current) => ({ ...current, email: event.target.value }))
              }
            />
          </label>

          <label>
            <span>Username</span>
            <input
              required
              minLength="3"
              value={registerForm.username}
              onChange={(event) =>
                setRegisterForm((current) => ({ ...current, username: event.target.value }))
              }
            />
          </label>

          <label>
            <span>Password</span>
            <input
              required
              type="password"
              value={registerForm.password}
              onChange={(event) =>
                setRegisterForm((current) => ({ ...current, password: event.target.value }))
              }
            />
          </label>

          <button className="primary-button" disabled={busy.auth} type="submit">
            {busy.auth ? 'Creating...' : 'Create account'}
          </button>

          <button
            className="ghost-button"
            type="button"
            onClick={() => setAuthMode('login')}
          >
            Have account? Switch to login
          </button>
        </form>
      )
    }

    return (
      <form className="panel auth-panel" onSubmit={handleLogin}>
        <div className="panel-heading">
          <p className="eyebrow">Login</p>
          <h2>Access dashboard</h2>
        </div>

        <label>
          <span>Email</span>
          <input
            required
            type="email"
            value={loginForm.email}
            onChange={(event) =>
              setLoginForm((current) => ({ ...current, email: event.target.value }))
            }
          />
        </label>

        <label>
          <span>Password</span>
          <input
            required
            type="password"
            value={loginForm.password}
            onChange={(event) =>
              setLoginForm((current) => ({ ...current, password: event.target.value }))
            }
          />
        </label>

        <button className="primary-button" disabled={busy.auth} type="submit">
          {busy.auth ? 'Signing in...' : 'Login'}
        </button>

        <button
          className="ghost-button"
          type="button"
          onClick={() => setAuthMode('register')}
        >
          New user? Switch to register
        </button>
      </form>
    )
  }

  return (
    <div className="app-shell">
      <section className="hero-strip">
        <div className="hero-copy">
          <p className="eyebrow">PrimeTradeAI</p>
          <h1>Task command center for auth, RBAC, CRUD.</h1>
          <p className="hero-text">
            Single-screen React frontend for testing register, login, protected profile,
            and task management against FastAPI backend.
          </p>
        </div>

        <div className="hero-status panel">
          <div className="status-row">
            <span className="status-label">API</span>
            <code>{API_BASE_URL}</code>
          </div>
          <div className="status-row">
            <span className="status-label">Session</span>
            <strong>{token ? 'Authenticated' : 'Guest'}</strong>
          </div>
          <div className={`flash flash-${statusMessage.type}`}>{statusMessage.text}</div>
        </div>
      </section>

      <main className="workspace">
        <section className="left-rail">
          {!token ? (
            renderAuthCard()
          ) : (
            <div className="panel profile-card">
              <div className="panel-heading">
                <p className="eyebrow">Profile</p>
                <h2>{busy.profile ? 'Loading...' : user?.username ?? 'User'}</h2>
              </div>

              <dl className="profile-grid">
                <div>
                  <dt>Email</dt>
                  <dd>{user?.email ?? '-'}</dd>
                </div>
                <div>
                  <dt>Role</dt>
                  <dd>{user?.role ?? '-'}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{user?.is_active ? 'active' : 'inactive'}</dd>
                </div>
              </dl>

              <div className="stack-actions">
                <button className="primary-button" type="button" onClick={() => loadTasks()}>
                  Refresh tasks
                </button>
                <button className="ghost-button" type="button" onClick={clearSession}>
                  Logout
                </button>
              </div>
            </div>
          )}

          <form className="panel task-form" onSubmit={handleTaskSubmit}>
            <div className="panel-heading">
              <p className="eyebrow">Task Editor</p>
              <h2>{selectedTaskId ? `Edit task #${selectedTaskId}` : 'Create task'}</h2>
            </div>

            <label>
              <span>Title</span>
              <input
                required
                minLength="2"
                name="title"
                value={taskForm.title}
                onChange={handleTaskFormChange}
              />
            </label>

            <label>
              <span>Description</span>
              <textarea
                name="description"
                rows="5"
                value={taskForm.description}
                onChange={handleTaskFormChange}
              />
            </label>

            <div className="field-row">
              <label>
                <span>Status</span>
                <select name="status" value={taskForm.status} onChange={handleTaskFormChange}>
                  <option value="todo">todo</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                </select>
              </label>

              <label>
                <span>Priority</span>
                <select
                  name="priority"
                  value={taskForm.priority}
                  onChange={handleTaskFormChange}
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
            </div>

            <div className="stack-actions">
              <button className="primary-button" disabled={!token || busy.saveTask} type="submit">
                {busy.saveTask ? 'Saving...' : selectedTaskId ? 'Update task' : 'Create task'}
              </button>

              <button
                className="ghost-button"
                disabled={!selectedTaskId}
                type="button"
                onClick={() => {
                  setSelectedTaskId(null)
                  setTaskForm(emptyTaskForm)
                }}
              >
                Clear editor
              </button>
            </div>
          </form>
        </section>

        <section className="right-rail">
          <div className="panel filter-bar">
            <div className="panel-heading compact-heading">
              <div>
                <p className="eyebrow">Task Feed</p>
                <h2>Protected CRUD workspace</h2>
              </div>
              <button className="ghost-button" type="button" onClick={() => loadTasks()}>
                {busy.tasks ? 'Loading...' : 'Reload'}
              </button>
            </div>

            <div className="filters-grid">
              <label>
                <span>Search</span>
                <input
                  name="search"
                  placeholder="Search title"
                  value={filters.search}
                  onChange={handleFilterChange}
                />
              </label>
              <label>
                <span>Status</span>
                <select
                  name="status_filter"
                  value={filters.status_filter}
                  onChange={handleFilterChange}
                >
                  <option value="">all</option>
                  <option value="todo">todo</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                </select>
              </label>
              <label>
                <span>Priority</span>
                <select
                  name="priority_filter"
                  value={filters.priority_filter}
                  onChange={handleFilterChange}
                >
                  <option value="">all</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
            </div>

            <button className="primary-button" disabled={!token || busy.tasks} onClick={() => loadTasks()} type="button">
              Apply filters
            </button>
          </div>

          <div className="task-grid">
            {tasks.length === 0 ? (
              <div className="panel empty-state">
                <h3>No tasks yet</h3>
                <p>Create task after login or adjust filters.</p>
              </div>
            ) : (
              tasks.map((task) => (
                <article className="panel task-card" key={task.id}>
                  <div className="task-card-head">
                    <div>
                      <p className="task-id">Task #{task.id}</p>
                      <h3>{task.title}</h3>
                    </div>
                    <span className={`chip chip-${task.status}`}>{task.status}</span>
                  </div>

                  <p className="task-description">{task.description || 'No description provided.'}</p>

                  <div className="meta-row">
                    <span className="chip chip-priority">{task.priority}</span>
                    <span className="meta-date">
                      {new Date(task.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="card-actions">
                    <button className="ghost-button" type="button" onClick={() => handleEditTask(task.id)}>
                      Edit
                    </button>
                    <button className="ghost-button danger-button" type="button" onClick={() => handleDeleteTask(task.id)}>
                      Delete
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
