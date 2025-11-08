# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, deployment, and maintenance of the AI Stack Build project.

## 📋 Available Workflows

### 🚀 `deploy.yml` - Main CI/CD Pipeline

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Manual workflow dispatch

**Features:**
- Automated testing and Docker image building
- Security scanning with Trivy
- Deployment to staging (automatic) and production (manual)
- Slack/Discord notifications
- Rollback capabilities on deployment failure

**Required Secrets:**
- `STAGING_SSH_PRIVATE_KEY` - SSH key for staging server
- `STAGING_SSH_USER` - SSH username for staging
- `STAGING_HOST` - Staging server hostname
- `PRODUCTION_SSH_PRIVATE_KEY` - SSH key for production
- `PRODUCTION_SSH_USER` - SSH username for production
- `PRODUCTION_HOST` - Production server hostname
- `SLACK_WEBHOOK_URL` - Slack webhook for notifications
- `DISCORD_WEBHOOK` - Discord webhook for notifications

### 🔍 `pr-validation.yml` - Pull Request Validation

**Triggers:**
- Pull request opened, synchronized, or reopened

**Features:**
- Code quality checks (Python syntax, imports)
- JSON configuration validation
- Shell script syntax checking
- Docker Compose validation
- Security scanning
- Sensitive data detection
- Documentation completeness checks

### 🔄 `dependency-updates.yml` - Automated Updates

**Triggers:**
- Weekly schedule (Mondays 2 AM UTC)
- Manual workflow dispatch

**Features:**
- Python dependency updates
- Docker base image updates
- Security vulnerability scanning
- Automated pull request creation
- Package cleanup

### 📦 `release.yml` - Release Management

**Triggers:**
- Git tag push (e.g., `v1.2.3`)
- Manual workflow dispatch

**Features:**
- Docker image building and publishing
- Release archive creation
- GitHub release creation
- Container registry publishing
- Release notes generation

### 🏥 `nightly-health.yml` - Health Monitoring

**Triggers:**
- Daily schedule (3 AM UTC)
- Manual workflow dispatch

**Features:**
- Repository structure validation
- Configuration file checking
- Build process testing
- Security scanning
- Health report generation
- Failure notifications

## 🛠️ Setup Instructions

### 1. Enable GitHub Actions

Ensure GitHub Actions is enabled in your repository settings.

### 2. Configure Required Secrets

Add the following secrets to your repository:

```bash
# SSH Access
STAGING_SSH_PRIVATE_KEY
STAGING_SSH_USER
STAGING_HOST
PRODUCTION_SSH_PRIVATE_KEY
PRODUCTION_SSH_USER
PRODUCTION_HOST

# Notifications
SLACK_WEBHOOK_URL
DISCORD_WEBHOOK
```

### 3. Configure Deployment Environments

Create the following environments in repository settings:

- **staging**: For automatic deployments
- **production**: For manual production deployments

### 4. Set Up Remote Servers

On your staging and production servers:

```bash
# Create deployment directory
sudo mkdir -p /opt/ai-stack-build
sudo chown $USER:$USER /opt/ai-stack-build

# Clone repository
cd /opt/ai-stack-build
git clone https://github.com/yourusername/ai-stack-build.git .

# Set up SSH access for GitHub Actions
# Add the public key from your secrets to ~/.ssh/authorized_keys
```

## 🚦 Workflow Status

| Workflow | Status | Description |
|----------|--------|-------------|
| `deploy.yml` | Production Ready | Full CI/CD with deployment |
| `pr-validation.yml` | Production Ready | PR quality gates |
| `dependency-updates.yml` | Production Ready | Automated maintenance |
| `release.yml` | Production Ready | Release management |
| `nightly-health.yml` | Production Ready | Health monitoring |

## 📊 Monitoring & Alerts

### Health Checks

The nightly health check workflow monitors:
- Repository integrity
- Configuration validity
- Build process functionality
- Security compliance
- Documentation completeness

### Notifications

Configure notifications for:
- Deployment successes/failures
- Security vulnerabilities
- Health check failures
- Release publications

## 🔧 Customization

### Adding New Workflows

1. Create new `.yml` file in this directory
2. Follow naming convention: `feature-name.yml`
3. Add appropriate triggers and jobs
4. Update this README

### Modifying Existing Workflows

1. Edit the relevant `.yml` file
2. Test changes on a feature branch
3. Update documentation
4. Commit and create pull request

### Environment-Specific Configuration

Use GitHub Environments for:
- Different deployment targets
- Environment-specific secrets
- Approval requirements
- Protection rules

## 🐛 Troubleshooting

### Common Issues

**Workflow not triggering:**
- Check branch protection rules
- Verify file paths in triggers
- Check repository settings

**SSH connection failures:**
- Verify SSH keys are correct
- Check server firewall rules
- Ensure SSH service is running

**Docker build failures:**
- Check Docker Hub rate limits
- Verify base image availability
- Check build context size

**Secret access issues:**
- Verify secret names match exactly
- Check environment permissions
- Ensure secrets are not empty

### Debugging

Enable debug logging:
```yaml
jobs:
  debug:
    runs-on: ubuntu-latest
    steps:
      - name: Enable debug
        run: echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
```

Check workflow logs in the Actions tab for detailed error messages.

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build/Push Action](https://github.com/docker/build-push-action)
- [Trivy Security Scanner](https://github.com/aquasecurity/trivy)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

*For questions or issues with CI/CD workflows, please check the troubleshooting guide or create an issue.*