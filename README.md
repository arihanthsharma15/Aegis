# Aegis API – Security & Analytics Middleware

## Overview
**Aegis API** is a proactive API Security and Analytics Middleware built with **FastAPI** and **Redis**.  
It is designed to protect high-resource and AI-driven applications from abuse, unauthorized access, and sudden traffic spikes while maintaining minimal latency overhead.  
The system acts as a **protective layer before requests reach the core business logic.**

---

## Key Features
- **Intelligent Rate Limiting** – Sliding Window algorithm using Redis for high-speed request tracking and DDoS prevention
- **Security Analytics** – Real-time monitoring of IP traffic patterns, latency, and server health
- **Plug-and-Play Middleware** – Easily integrable with FastAPI applications
- **High Performance** – Optimized for low-latency validation and scalable workloads
- **Attack Simulation & Load Testing** – Includes scripts and Locust configuration for stress testing

---

## Custom Middleware Library
Aegis is also structured as a **reusable Python middleware library** (`aegis_middleware`) built from scratch and validated through a demo FastAPI application.

- Implements **Redis-powered Sliding Window Rate Limiting**
- Fully modular plug-and-play architecture
- Not yet published on PyPI, but production-ready and reusable across FastAPI projects

---

## Tech Stack
- **Backend:** Python, FastAPI  
- **Caching & Rate Limiting:** Redis  
- **Containerization:** Docker, Docker Compose  
- **Load Testing:** Locust  
- **Environment:** Linux  

---

## Use Case
Ideal for **AI platforms, SaaS products, and production APIs** that require:
- Traffic control  
- Abuse prevention  
- Real-time security insights  

before requests reach core application services.

---

## Project Structure

app/
├─ api/           # API endpoints
├─ core/          # Configurations & Logger
├─ middleware/    # Rate limiting logic
└─ services/      # Redis client

aegis_middleware/ # Reusable middleware package
examples/         # Demo FastAPI apps
scripts/          # Attack simulation scripts
locustfile.py     # Load testing configuration

---

## Impact
Enhances **API reliability, scalability, and security** by filtering malicious or excessive traffic at the middleware layer, reducing server load, and safeguarding high-resource AI applications from misuse and unexpected spikes.