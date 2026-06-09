# ShopSmart — Interactive Showcase

An interactive static showcase for **ShopSmart**, a full-stack price-comparison app that helps
users find the best prices across supermarkets and identifies the cheapest store for their basket.

🔗 **Live site:** https://andreaisabelmontana.github.io/shopsmart/

## What it does
- **Shopping list** — add items with autocomplete and manage the whole list.
- **Multi-store comparison** — compare item prices across multiple supermarkets.
- **Best-price finder** — automatically identifies the cheapest store for your basket.
- **Persistent state** — the list survives navigation and browser sessions.
- **Auth & responsive** — sign up / log in; works on desktop and mobile.

**Architecture:** React/Vite (Nginx) → FastAPI → PostgreSQL, containerised on Azure App Service.
**Stack:** React 18 + Vite · FastAPI (Python 3.11) · SQLAlchemy + Alembic · PostgreSQL · Docker + ACR · GitHub Actions CI/CD · Application Insights.

## About this repo
An original, hand-built static site (single `index.html`, no framework) presenting the project,
with a scripted interactive price-comparison demo (build a basket → see the cheapest store live).
Built from scratch; store names and prices are sample data.
