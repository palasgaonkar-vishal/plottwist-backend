# PlotTwist Troubleshooting Guide

This guide helps resolve common issues encountered while setting up and running the PlotTwist development environment.

## 🐛 Common Docker Issues

### Frontend Build Errors

#### Issue: Node.js Version Incompatibility
```
npm warn EBADENGINE Unsupported engine {
npm warn EBADENGINE   package: 'react-router@7.8.1',
npm warn EBADENGINE   required: { node: '>=20.0.0' },
npm warn EBADENGINE   current: { node: 'v18.20.8', npm: '10.8.2' }
```

**Solution:**
```bash
# Update your Docker images to use the latest versions
docker-compose down
docker-compose pull
docker-compose build --no-cache
docker-compose up -d
```

The Dockerfile has been updated to use Node 20 which resolves this issue.

#### Issue: npm Authentication Error
```
npm error code E401
npm error Incorrect or missing password.
```

**Solutions:**

1. **Clear Docker build cache:**
   ```bash
   docker system prune -a
   docker-compose build --no-cache
   ```

2. **If you have corporate npm settings, create `.npmrc` in frontend directory:**
   ```bash
   cd plottwist-frontend
   echo "registry=https://registry.npmjs.org/" > .npmrc
   ```

3. **Use local development instead of Docker:**
   ```bash
   cd plottwist-frontend
   npm install
   npm start
   ```

### Backend Build Errors

#### Issue: Python Package Installation Fails
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solution:**
```bash
# Clear Docker cache and rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache backend
docker-compose up -d
```

### Database Connection Issues

#### Issue: Database Connection Refused
```
FATAL: password authentication failed for user "plottwist"
```

**Solutions:**

1. **Reset database volume:**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

2. **Check if PostgreSQL is running:**
   ```bash
   docker-compose ps
   docker-compose logs postgres
   ```

3. **Manually create database:**
   ```bash
   docker-compose exec postgres psql -U plottwist -c "CREATE DATABASE plottwist_test;"
   ```

## 🔧 Port Conflicts

### Issue: Port Already in Use
```
Error starting userland proxy: listen tcp 0.0.0.0:3000: bind: address already in use
```

**Solutions:**

1. **Find and stop the process using the port:**
   ```bash
   # Check what's using the port
   lsof -i :3000  # Frontend
   lsof -i :8000  # Backend
   lsof -i :5432  # Database
   
   # Kill the process (replace PID with actual process ID)
   kill -9 <PID>
   ```

2. **Change ports in docker-compose.yml:**
   ```yaml
   ports:
     - "3001:3000"  # Change frontend port
     - "8001:8000"  # Change backend port
     - "5433:5432"  # Change database port
   ```

## 🖥️ Platform-Specific Issues

### macOS Issues

#### Issue: Docker Performance on macOS
**Solution:**
```bash
# Increase Docker resources
# Docker Desktop → Settings → Resources → Advanced
# RAM: 4GB+ recommended
# CPUs: 2+ cores recommended
```

#### Issue: File watching not working
**Solution:**
Add to your docker-compose environment:
```yaml
environment:
  - CHOKIDAR_USEPOLLING=true
  - WATCHPACK_POLLING=true
```

### Windows Issues

#### Issue: Line ending problems
**Solution:**
```bash
# Configure git to handle line endings
git config --global core.autocrlf true

# Or convert existing files
git config core.autocrlf true
git rm --cached -r .
git reset --hard
```

#### Issue: Docker volume mounting issues
**Solution:**
```bash
# Ensure Docker Desktop has access to your drive
# Docker Desktop → Settings → Resources → File Sharing
```

## 🌐 Network Issues

### Issue: Services Can't Communicate
**Solutions:**

1. **Check if all services are on the same network:**
   ```bash
   docker network ls
   docker network inspect plottwist_plottwist-network
   ```

2. **Restart all services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Use service names for internal communication:**
   ```bash
   # Use 'backend' instead of 'localhost' in frontend API calls
   # Use 'postgres' instead of 'localhost' in backend database connections
   ```

## 🧪 Testing Issues

### Issue: Tests Fail Due to Missing Dependencies
**Solution:**
```bash
# Backend tests
cd plottwist-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest

# Frontend tests
cd plottwist-frontend
npm install
npm test
```

### Issue: Test Database Connection Fails
**Solution:**
```bash
# Ensure test database exists
docker-compose exec postgres psql -U plottwist -c "CREATE DATABASE plottwist_test;"

# Or recreate with volume reset
docker-compose down -v
docker-compose up -d
```

## 🚀 Performance Optimization

### Slow Docker Builds

1. **Use Docker BuildKit:**
   ```bash
   export DOCKER_BUILDKIT=1
   docker-compose build
   ```

2. **Enable Docker layer caching:**
   ```bash
   docker-compose build --build-arg BUILDKIT_INLINE_CACHE=1
   ```

3. **Cleanup unused Docker resources:**
   ```bash
   docker system prune -a
   docker volume prune
   ```

### Slow File Watching (Hot Reload)

1. **For macOS/Windows, use polling:**
   ```yaml
   environment:
     - CHOKIDAR_USEPOLLING=true
     - WATCHPACK_POLLING=true
   ```

2. **Reduce polling interval:**
   ```yaml
   environment:
     - CHOKIDAR_INTERVAL=1000
   ```

## 🆘 Getting Help

If none of these solutions work:

1. **Check logs:**
   ```bash
   docker-compose logs frontend
   docker-compose logs backend
   docker-compose logs postgres
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   docker-compose top
   ```

3. **Full reset:**
   ```bash
   docker-compose down -v
   docker system prune -a
   git pull origin main  # Get latest updates
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Create an issue:**
   - [Backend Issues](https://github.com/palasgaonkar-vishal/plottwist-backend/issues)
   - [Frontend Issues](https://github.com/palasgaonkar-vishal/plottwist-frontend/issues)

Include in your issue:
- Operating system and version
- Docker version
- Complete error logs
- Steps to reproduce

## 📞 Contact

For urgent issues or questions, contact the development team with:
- Your operating system
- Docker version (`docker --version`)
- Complete error message
- What you were trying to do when the error occurred 