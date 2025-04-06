# UnisKit Template

Welcome to UnisKit! This is a **full-stack application template** designed to accelerate your development process. It provides a pre-configured setup using modern technologies within a monorepo structure.

Use this template as a foundation to quickly build applications featuring a web frontend, mobile app, backend API, and shared components.

## Project Structure & Template Philosophy

This project is structured as a **monorepo** managed using `pnpm workspaces`. This means all the foundational code for the different application parts (web, mobile, backend, shared packages) reside within this single repository.

-   `/apps/backend`: Python FastAPI backend service starter.
-   `/apps/mobile`: React Native (Expo) mobile application starter.
-   `/apps/web`: React (Vite) web frontend starter.
-   `/packages/shared`: Shared code (themes, types, utilities) pre-configured for use across the different applications.

**Why a Monorepo Template?**

Using a monorepo template offers several advantages:

-   **Rapid Development:** Get started quickly with pre-linked shared code (like themes and types).
-   **Consistency:** Ensures consistent tooling (TypeScript, linting) and dependency management across your project from the start.
-   **Simplified Setup:** Reduces the boilerplate needed to connect frontend, backend, and mobile applications.
-   **Easy Extension:** Provides a clear structure to build upon.

## Getting Started

### Prerequisites

-   [Node.js](https://nodejs.org/) (LTS version recommended)
-   [`pnpm`](https://pnpm.io/installation) (v8.0.0 or higher, as specified in `package.json`)
-   [Python](https://www.python.org/downloads/) (3.10+ recommended for FastAPI)
-   Standard Python package management tools (`pip`, `venv`)
-   [Expo CLI](https://docs.expo.dev/get-started/installation/) (if developing for mobile)

### Installation

1.  **Clone or Use Template:**
    *   Clone this repository: `git clone <your-repository-url>`
    *   Or, preferably, use this repository as a template on GitHub/GitLab.
    *   Navigate into the project directory: `cd uniskit` (or your chosen name).

2.  **Install JavaScript dependencies:**
    Run `pnpm install` from the **root** directory. This installs Node.js dependencies for web, mobile, and shared packages, and links the local workspace packages.
    ```bash
    pnpm install
    ```

3.  **Backend Setup:** The backend service (including Python dependencies and Redis) is managed via Docker Compose. See the `backend/README.md` for instructions on configuring and running the backend containers.

## Technology Stack

-   **Monorepo Management:** `pnpm workspaces`
-   **Frontend (Web):** React, Vite, TypeScript, CSS Modules
-   **Frontend (Mobile):** React Native, Expo, TypeScript
-   **Backend:** Python, FastAPI, MongoDB
-   **Shared Code:** TypeScript

## Building Your Application

This template provides the starting point. Refer to the README files within each application's directory (`apps/web/README.md`, `apps/mobile/README.md`, `apps/backend/README.md`) for specific instructions on running each part in development mode and how to extend them.