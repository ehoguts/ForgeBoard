# Frontend-specific instructions

Scope: all files under `frontend/`. Follow root `AGENTS.md` too.

## Stack and structure
- Use React + TypeScript + Vite, React Router, and TanStack Query.
- Keep API access in a typed client module; use the same-origin `/api/v1` path and Vite's development proxy.
- Implement responsive, accessible UI with semantic HTML, labels, keyboard navigation, and visible focus states.
- Use a coherent design system with reusable primitives, without introducing a heavy component framework by default.

## UX for milestone 1
- Provide registration, login, dashboard, projects list/detail, issue creation/editing, and logout.
- Every async view needs explicit loading, empty, error, and success states.
- Show useful form validation messages; prevent accidental double submission.
- Keep filters (status, priority, search) in URL/query state where practical.
- Never store session tokens in localStorage or sessionStorage; browser cookies are handled by the API.
- Retrieve and send the server-approved CSRF token for mutating authenticated requests, as required by backend contract.
- Never make account authorization decisions solely in the client; server authorization is authoritative.

## Quality
- Avoid `any` in TypeScript unless unavoidable and documented.
- Write component tests for authentication, critical forms, and issue filtering using Vitest and React Testing Library.
- Keep user-facing copy clear and consistent in English.
- Prefer small focused components over large all-in-one pages.
