# PlotTwist Development Setup Guide

This guide will help you set up the PlotTwist development environment using Docker Compose.

## 🏗️ Project Structure

PlotTwist consists of two main repositories:
- **Backend**: [plottwist-backend](https://github.com/palasgaonkar-vishal/plottwist-backend) (Python FastAPI)
- **Frontend**: [plottwist-frontend](https://github.com/palasgaonkar-vishal/plottwist-frontend) (React TypeScript)

## 🚀 Quick Start (Recommended)

### Full-Stack Development Setup

```bash
# 1. Create workspace directory
mkdir plottwist-workspace
cd plottwist-workspace

# 2. Clone both repositories
git clone git@github.com:palasgaonkar-vishal/plottwist-backend.git
git clone git@github.com:palasgaonkar-vishal/plottwist-frontend.git

# 3. Download the docker-compose configuration
curl -O https://raw.githubusercontent.com/palasgaonkar-vishal/plottwist-backend/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/palasgaonkar-vishal/plottwist-backend/main/init-db.sql

# 4. Start all services
docker-compose up -d

# 5. Verify services are running
docker-compose ps
```

**Services will be available at:**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 🗄️ **Database**: localhost:5432
- 📚 **API Documentation**: http://localhost:8000/api/v1/docs

## 🔧 Development Options

### Option 1: Backend-Only Development

```bash
cd plottwist-backend
docker-compose -f docker-compose.dev.yml up -d
```

### Option 2: Frontend-Only Development

```bash
cd plottwist-frontend
docker-compose -f docker-compose.dev.yml up -d
```

### Option 3: Local Development (No Docker)

**Prerequisites:** Python 3.11+, Node.js 16+, PostgreSQL

```bash
# Backend setup
cd plottwist-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup (in another terminal)
cd plottwist-frontend
npm install
npm start

# Database setup (in another terminal)
# Install PostgreSQL locally and create database:
createdb plottwist
createdb plottwist_test
```

## 🧪 Testing

### Backend Testing

```bash
cd plottwist-backend
docker-compose -f docker-compose.dev.yml up -d postgres  # Start database
python -m pytest --cov=app --cov-report=html
```

### Frontend Testing

```bash
cd plottwist-frontend
npm test
```

## 🔄 Development Workflow

1. **Start Services**: Use the full-stack docker-compose for complete development
2. **Make Changes**: Edit code in either repository
3. **Hot Reload**: Changes are automatically reflected (no restart needed)
4. **Test**: Run tests locally before committing
5. **Commit**: Push changes to respective repositories

## 📁 Workspace Structure

After setup, your workspace should look like:

```
plottwist-workspace/
├── plottwist-backend/          # Backend repository
├── plottwist-frontend/         # Frontend repository
├── docker-compose.yml             # Full-stack configuration
└── init-db.sql                # Database initialization
```

## 🐛 Troubleshooting

If you encounter issues, check the [Troubleshooting Guide](https://github.com/palasgaonkar-vishal/plottwist-backend/blob/main/TROUBLESHOOTING.md).

Common solutions:
- **Port conflicts**: Check if ports 3000, 8000, or 5432 are in use
- **Docker issues**: Run `docker-compose down -v` and rebuild with `--no-cache`
- **Permission errors**: Ensure Docker has access to your file system

## 🤝 Contributing

1. Fork the repository you want to contribute to
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and test thoroughly
4. Commit with clear message: `git commit -m "Add: your feature description"`
5. Push and create a Pull Request

## 📚 Additional Resources

- [Backend README](https://github.com/palasgaonkar-vishal/plottwist-backend/blob/main/README.md)
- [Frontend README](https://github.com/palasgaonkar-vishal/plottwist-frontend/blob/main/README.md)
- [Business PRD](./business.prd.md)
- [Technical PRD](./technical.prd.md)
- [Task Breakdown](./tasks/)

## 🆘 Need Help?

If you're stuck:
1. Check the troubleshooting guide
2. Review the README files in each repository
3. Create an issue in the relevant repository with:
   - Your operating system
   - Docker version
   - Complete error logs
   - Steps to reproduce

---

Happy coding! 🚀 