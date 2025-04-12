# Todo List

- Implement auth on web which will block all paths unless authed (use landing.web.tsx that is currently implemented)
- Remove web index to make the root of web load everything with api
- Chat page's title isnt showing the chat name, also implement edit chat information

- ## Improve Token Security (Move Refresh Token to HttpOnly Cookie, Access Token to Memory)
  **Current Issue:** Storing tokens (especially refresh tokens) in localStorage is vulnerable to XSS attacks.
  **Recommended Approach:**
  1. **Refresh Token:** Store in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie set by the backend.
  2. **Access Token:** Store in client-side memory (e.g., React context or a dedicated service module).

  **Implementation Plan:**

  **Backend (`backend/app/features/auth/controllers/auth_controller.py`, `backend/app/main.py`):**
    - Update `/login` and `/refresh` endpoints:
      - Do NOT return `refresh_token` in the JSON body.
      - Set `refresh_token` in a `Set-Cookie` header with `HttpOnly=True`, `Secure=True`, `SameSite=Strict` (or `Lax`), and appropriate `path` and `max_age`/`expires`.
    - Update `/refresh` endpoint:
      - Read `refresh_token` from the incoming request's cookie header.
    - Update `/logout` endpoint:
      - Clear the `refresh_token` cookie (e.g., by setting `Set-Cookie` with `max_age=0` or an expiry date in the past).
    - CORS Configuration (`main.py`):
      - Ensure `allow_credentials=True`.
      - Explicitly list frontend origin(s) in `allow_origins` (cannot use "*").

  **Frontend (`frontend/src/config/storage.config.ts`, `frontend/src/features/auth/context/AuthContext.tsx`, `frontend/src/api/client.ts`, `frontend/src/features/chat/hooks/useChatWebSocket.ts`):**
    - Remove all code storing/retrieving `refresh_token` from `localStorage`/`secureStorage`.
    - Implement in-memory storage for `access_token` (e.g., variable within `AuthContext` or a dedicated auth state module).
    - Update `getAccessToken` to retrieve from memory.
    - Update `setAccessToken`/`setTokens` to store only the access token in memory.
    - Implement logic on app load/refresh (e.g., in `AuthContext`):
      - Check if access token exists in memory.
      - If not, automatically call the backend `/refresh` endpoint (the browser will send the HttpOnly cookie).
      - Store the newly received access token in memory.
      - Handle refresh errors (e.g., redirect to login if refresh token is invalid/expired).
    - Ensure `ApiClient` (for REST calls) and `useChatWebSocket` (for WS connection) get the access token from memory.
    - Update logout function:
      - Clear the access token from memory.
      - Call the backend `/logout` endpoint to clear the HttpOnly refresh token cookie.

- **Frontend:** Create a reusable `BaseMessage` component to serve as the foundation for rendering different message types (user, agent text, thinking, tool use, error).

- **Frontend:** Implement useApiPaginated and centralize FlatLists

- **Backend:** Understand the current architecture and refactor

- **Backend:** Add traces

- **Frontend:** Add settings page with theme and other stuff etc.

- **Backend:** Solidify the chat history functionality

- **Backend:** Correctly setup the exception based flow