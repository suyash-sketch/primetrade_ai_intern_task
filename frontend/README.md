# Frontend

React + Vite client for testing backend auth and task APIs.

## Features

- Register user
- Login with JWT
- Fetch protected profile
- List tasks
- Create task
- Load single task for editing
- Update task
- Delete task
- Filter tasks by search, status, priority

## Run

```bash
npm install
npm run dev
```

Default dev URL:

```text
http://127.0.0.1:5173
```

## Backend API URL

Frontend uses:

```text
http://127.0.0.1:8000/api/v1
```

Override with env file:

```bash
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1' > .env
```

## Build

```bash
npm run build
npm run preview
```
