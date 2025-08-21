# PlotTwist Development Setup Guide

This guide provides different options for setting up the PlotTwist development environment depending on your needs.

## 🏗️ Project Structure

The PlotTwist platform consists of two separate repositories:

- **Backend**: [plottwist-backend](https://github.com/palasgaonkar-vishal/plottwist-backend) - FastAPI + PostgreSQL
- **Frontend**: [plottwist-frontend](https://github.com/palasgaonkar-vishal/plottwist-frontend) - React + TypeScript + Material-UI

## 🚀 Quick Start (Recommended)

### Full-Stack Development Setup

For most development scenarios, you'll want both frontend and backend running:

```bash
# 1. Create a workspace directory
mkdir plottwist-workspace
cd plottwist-workspace

# 2. Clone both repositories
git clone git@github.com:palasgaonkar-vishal/plottwist-backend.git
git clone git@github.com:palasgaonkar-vishal/plottwist-frontend.git

# 3. Download the docker-compose configuration
# Option 1: Stable version (RECOMMENDED - uses battle-tested dependencies)
curl -O https://raw.githubusercontent.com/palasgaonkar-vishal/plottwist-backend/main/docker-compose.fullstack.stable.yml
curl -O https://raw.githubusercontent.com/palasgaonkar-vishal/plottwist-backend/main/init-db.sql

# 4. Start all services
docker-compose -f docker-compose.fullstack.stable.yml up -d

# 5. Verify services are running
docker-compose -f docker-compose.fullstack.stable.yml ps

# Alternative options (if stable version has issues):
# Option 2: Simple version
# curl -O https://raw.githubusercontent.com/palasgaonkar-vishal/plottwist-backend/main/docker-compose.fullstack.simple.yml
# docker-compose -f docker-compose.fullstack.simple.yml up -d

# Option 3: No health checks version
# curl -O https://raw.githubusercontent.com/palasgaonkar-vishal/plottwist-backend/main/docker-compose.fullstack.simple-no-health.yml
# docker-compose -f docker-compose.fullstack.simple-no-health.yml up -d
```

**Services will be available at:**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/api/v1/docs
- 🗄️ **Database**: localhost:5432

## 🔧 Development Options

### Option 1: Backend-Only Development

If you're working exclusively on backend features:

```bash
git clone git@github.com:palasgaonkar-vishal/plottwist-backend.git
cd plottwist-backend
docker-compose -f docker-compose.dev.yml up -d
```

### Option 2: Frontend-Only Development

If you're working exclusively on frontend features (requires backend running separately):

```bash
git clone git@github.com:palasgaonkar-vishal/plottwist-frontend.git
cd plottwist-frontend

# Using Docker
docker-compose -f docker-compose.dev.yml up -d

# Or using npm
npm install
npm start
```

### Option 3: Local Development (No Docker)

#### Backend Setup:
```bash
cd plottwist-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run the application
uvicorn app.main:app --reload
```

#### Frontend Setup:
```bash
cd plottwist-frontend
npm install
npm start
```

## 🧪 Testing

### Backend Testing:
```bash
cd plottwist-backend
source venv/bin/activate
pytest --cov=app --cov-report=html
```

### Frontend Testing:
```bash
cd plottwist-frontend
npm test -- --coverage --watchAll=false
```

## 🔄 Development Workflow

1. **Make Changes**: Work on your feature in the appropriate repository
2. **Test Locally**: Run tests to ensure your changes work
3. **Commit**: Use descriptive commit messages
4. **Push**: Push to your feature branch
5. **Pull Request**: Create a PR for review

## 📁 Workspace Structure

After setup, your workspace should look like:

```
plottwist-workspace/
├── plottwist-backend/          # Backend repository
├── plottwist-frontend/         # Frontend repository
├── docker-compose.fullstack.yml # Full-stack docker setup
└── init-db.sql                # Database initialization
```

## 🐛 Troubleshooting

### Port Conflicts
If you get port conflict errors:
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Database

# Stop conflicting services or change ports in docker-compose.yml
```

### Database Issues
```bash
# Reset database volume
docker-compose -f docker-compose.fullstack.yml down -v
docker-compose -f docker-compose.fullstack.yml up -d
```

### Permission Issues
```bash
# Fix Docker permission issues (Linux/Mac)
sudo chown -R $USER:$USER plottwist-workspace/
```

## 🤝 Contributing

1. Fork both repositories you plan to work on
2. Create feature branches (`git checkout -b feature/your-feature-name`)
3. Make your changes with appropriate tests
4. Ensure all tests pass
5. Commit with descriptive messages
6. Push to your fork
7. Create Pull Requests

## 📚 Additional Resources

- [Backend Documentation](https://github.com/palasgaonkar-vishal/plottwist-backend/blob/main/README.md)
- [Frontend Documentation](https://github.com/palasgaonkar-vishal/plottwist-frontend/blob/main/README.md)
- [Technical PRD](./technical.prd.md)
- [Business PRD](./business.prd.md)

## 🆘 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Review the individual repository READMEs
3. Open an issue in the relevant repository
4. Contact the development team

Happy coding! 🚀 