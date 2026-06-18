# Trade Cycle Engine

A graph-based multi-party trade matching platform that enables direct and cyclic item exchanges using DFS-powered cycle detection.

## Problem Statement

Traditional barter systems suffer from the double coincidence of wants problem:

User A wants an item from User B,
but User B may not want anything from User A.

Trade Cycle Engine solves this by modeling users and their interests as a directed graph and discovering trade cycles such as:

A → B → C → A

allowing all participants to receive desired items even when direct trades are impossible.

---

## Key Features

- JWT Authentication & Authorization
- Role-Based Access Control (RBAC)
- Item Management APIs
- Want Management APIs
- Direct Trade Discovery
- Multi-Party Trade Cycle Detection
- UUID-Based Public Identifiers
- Swagger/OpenAPI Documentation
- Automated Test Suite
- Pagination Support

---

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL Ready
- SimpleJWT
- drf-spectacular
- OpenAPI / Swagger