# AI-Powered Collaboration Analytics Platform

Enterprise meeting room analytics platform integrating Microsoft Graph API,
FastAPI, and Power BI to surface collaboration trends and optimization insights.

## Architecture

Microsoft Graph API → FastAPI (Python) → SQLite → Power BI Dashboard

## Features

- Room utilization analysis across conference rooms
- Capacity mismatch detection (large rooms used for small meetings)
- Booking heatmap by day and hour
- 90-day hybrid meeting trend tracking
- Azure OpenAI transcript analysis (toggle-ready)
- Designed for Azure Functions + Azure SQL upgrade path

## Tech Stack

Python · FastAPI · SQLite · Microsoft Graph API · Power BI · Azure OpenAI
