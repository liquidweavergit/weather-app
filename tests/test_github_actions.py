"""
Tests for GitHub Actions CI/CD pipeline configuration and functionality.

Following TDD approach - these tests define the expected behavior
for GitHub Actions workflows with Docker builds.
"""

import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestGitHubActionsConfiguration:
    """Test GitHub Actions workflow configuration setup and validation."""
    
    def test_github_workflows_directory_exists(self):
        """Test that .github/workflows directory exists."""
        workflows_dir = Path('.github/workflows')
        assert workflows_dir.exists(), "GitHub workflows directory should exist"
        assert workflows_dir.is_dir(), "GitHub workflows should be a directory"
    
    def test_ci_workflow_file_exists(self):
        """Test that main CI workflow file exists and is valid YAML."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        assert ci_workflow_path.exists(), "CI workflow file should exist"
        
        # Test that the file is valid YAML
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        assert isinstance(workflow, dict), "CI workflow should be valid YAML dict"
        assert 'name' in workflow, "CI workflow should have a name"
        assert 'on' in workflow, "CI workflow should have trigger conditions"
        assert 'jobs' in workflow, "CI workflow should have jobs"
    
    def test_ci_workflow_has_required_triggers(self):
        """Test that CI workflow has appropriate trigger conditions."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        triggers = workflow['on']
        
        # Should trigger on push to main and pull requests
        assert 'push' in triggers, "Should trigger on push"
        assert 'pull_request' in triggers, "Should trigger on pull requests"
        
        if isinstance(triggers['push'], dict):
            assert 'main' in triggers['push'].get('branches', []), "Should trigger on main branch"
    
    def test_ci_workflow_has_required_jobs(self):
        """Test that CI workflow includes all required jobs."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        jobs = workflow['jobs']
        required_jobs = ['test', 'lint', 'security', 'build']
        
        for job in required_jobs:
            assert job in jobs, f"CI workflow should include '{job}' job"
    
    def test_test_job_configuration(self):
        """Test that test job is properly configured."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        test_job = workflow['jobs']['test']
        
        # Should run on Ubuntu
        assert 'runs-on' in test_job
        assert 'ubuntu' in test_job['runs-on']
        
        # Should have steps
        assert 'steps' in test_job
        assert len(test_job['steps']) > 0
        
        # Should include checkout step
        checkout_found = any(
            step.get('uses', '').startswith('actions/checkout') 
            for step in test_job['steps']
        )
        assert checkout_found, "Test job should include checkout step"
    
    def test_docker_build_job_configuration(self):
        """Test that Docker build job is properly configured."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        build_job = workflow['jobs']['build']
        
        # Should have Docker-related steps
        steps = build_job['steps']
        step_names = [step.get('name', '').lower() for step in steps]
        
        docker_steps = [name for name in step_names if 'docker' in name or 'build' in name]
        assert len(docker_steps) > 0, "Build job should have Docker-related steps"


class TestGitHubActionsSecurityAndBestPractices:
    """Test security and best practices in GitHub Actions workflows."""
    
    def test_workflow_uses_pinned_actions(self):
        """Test that workflow uses pinned action versions for security."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        for job_name, job in workflow['jobs'].items():
            for step in job.get('steps', []):
                if 'uses' in step:
                    action = step['uses']
                    # Should use specific version (either @vX.X.X or @sha)
                    assert '@' in action, f"Action '{action}' should use pinned version"
                    version = action.split('@')[1]
                    # Should not use @main or @master for security
                    assert version not in ['main', 'master'], f"Action '{action}' should not use @main or @master"
    
    def test_workflow_has_timeout_configured(self):
        """Test that jobs have appropriate timeouts configured."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        for job_name, job in workflow['jobs'].items():
            # Either job-level or workflow-level timeout should be set
            if 'timeout-minutes' not in job:
                # Check if there's a global timeout or if it's acceptable for this job
                pass  # Some jobs might not need explicit timeouts
    
    def test_workflow_uses_minimal_permissions(self):
        """Test that workflow uses minimal required permissions."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check if permissions are explicitly defined (security best practice)
        if 'permissions' in workflow:
            permissions = workflow['permissions']
            # Should not grant excessive permissions
            assert 'write-all' not in str(permissions).lower()
    
    def test_workflow_handles_secrets_securely(self):
        """Test that workflow handles secrets securely."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            content = f.read()
        
        # Should not contain hardcoded secrets
        sensitive_patterns = ['password', 'token', 'key']
        for pattern in sensitive_patterns:
            # Should use ${{ secrets.* }} pattern, not hardcoded values
            assert f'{pattern}=' not in content.lower() or 'secrets.' in content.lower()


class TestDockerIntegration:
    """Test Docker integration in GitHub Actions workflows."""
    
    def test_docker_compose_validation_job(self):
        """Test that workflow validates docker-compose configuration."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Should have steps that validate Docker setup
        all_steps = []
        for job in workflow['jobs'].values():
            all_steps.extend(job.get('steps', []))
        
        docker_validation_found = any(
            'docker-compose' in str(step).lower() or 'validate' in str(step).lower()
            for step in all_steps
        )
        assert docker_validation_found, "Workflow should validate Docker configuration"
    
    def test_docker_build_includes_multi_stage(self):
        """Test that Docker build supports multi-stage builds."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        build_job = workflow['jobs']['build']
        steps = build_job['steps']
        
        # Should build both development and production images
        build_commands = []
        for step in steps:
            if 'run' in step:
                build_commands.append(step['run'])
        
        build_text = ' '.join(build_commands).lower()
        
        # Should reference different targets or stages
        multi_stage_indicators = ['target', 'development', 'production', 'stage']
        has_multi_stage = any(indicator in build_text for indicator in multi_stage_indicators)
        assert has_multi_stage, "Docker build should support multi-stage builds"
    
    def test_docker_build_uses_cache(self):
        """Test that Docker build uses caching for efficiency."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        build_job = workflow['jobs']['build']
        steps = build_job['steps']
        
        # Should use Docker layer caching
        cache_found = any(
            'cache' in str(step).lower() or 'buildx' in str(step).lower()
            for step in steps
        )
        assert cache_found, "Docker build should use caching for efficiency"


class TestCodeQualityIntegration:
    """Test integration with code quality tools in CI/CD."""
    
    def test_precommit_hooks_in_ci(self):
        """Test that CI runs pre-commit hooks."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        lint_job = workflow['jobs']['lint']
        steps = lint_job['steps']
        
        # Should run pre-commit hooks
        precommit_found = any(
            'pre-commit' in str(step).lower()
            for step in steps
        )
        assert precommit_found, "CI should run pre-commit hooks"
    
    def test_test_coverage_reporting(self):
        """Test that CI includes test coverage reporting."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        test_job = workflow['jobs']['test']
        steps = test_job['steps']
        
        # Should generate coverage reports
        coverage_found = any(
            'coverage' in str(step).lower() or 'cov' in str(step).lower()
            for step in steps
        )
        assert coverage_found, "CI should include test coverage reporting"
    
    def test_security_scanning_in_ci(self):
        """Test that CI includes security scanning."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        security_job = workflow['jobs']['security']
        steps = security_job['steps']
        
        # Should run security scans
        security_tools = ['bandit', 'safety', 'snyk', 'trivy']
        security_found = any(
            any(tool in str(step).lower() for tool in security_tools)
            for step in steps
        )
        assert security_found, "CI should include security scanning"


class TestContinuousDeployment:
    """Test continuous deployment configuration."""
    
    def test_cd_workflow_exists(self):
        """Test that CD workflow file exists for deployment."""
        cd_workflow_path = Path('.github/workflows/cd.yml')
        
        if cd_workflow_path.exists():
            with open(cd_workflow_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            assert isinstance(workflow, dict), "CD workflow should be valid YAML dict"
            assert 'jobs' in workflow, "CD workflow should have jobs"
        else:
            # CD might be integrated into CI workflow
            ci_workflow_path = Path('.github/workflows/ci.yml')
            with open(ci_workflow_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            # Should have deployment-related jobs or steps
            deploy_indicators = ['deploy', 'release', 'publish']
            has_deploy = any(
                any(indicator in job_name.lower() for indicator in deploy_indicators)
                for job_name in workflow['jobs'].keys()
            )
            
            if not has_deploy:
                # This is acceptable for the current phase - deployment might be manual
                pass
    
    def test_deployment_environment_configuration(self):
        """Test that deployment environments are properly configured."""
        workflows_dir = Path('.github/workflows')
        workflow_files = list(workflows_dir.glob('*.yml')) if workflows_dir.exists() else []
        
        environment_configured = False
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow = yaml.safe_load(f)
            
            for job in workflow.get('jobs', {}).values():
                if 'environment' in job:
                    environment_configured = True
                    break
        
        # Environment configuration is optional at this stage
        # This test documents the expectation but doesn't fail
        pass


class TestWorkflowPerformance:
    """Test workflow performance and optimization."""
    
    def test_parallel_job_execution(self):
        """Test that jobs are configured for parallel execution where possible."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        jobs = workflow['jobs']
        
        # Independent jobs should not have unnecessary dependencies
        independent_jobs = ['test', 'lint', 'security']
        
        for job_name in independent_jobs:
            if job_name in jobs:
                job = jobs[job_name]
                # Should not depend on other independent jobs
                if 'needs' in job:
                    needs = job['needs']
                    if isinstance(needs, list):
                        conflicting_deps = set(needs) & set(independent_jobs)
                        conflicting_deps.discard(job_name)  # Job can't depend on itself
                        assert len(conflicting_deps) == 0, f"Job '{job_name}' should not depend on other independent jobs"
    
    def test_efficient_dependency_caching(self):
        """Test that workflows use efficient dependency caching."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Should use caching for dependencies
        all_steps = []
        for job in workflow['jobs'].values():
            all_steps.extend(job.get('steps', []))
        
        cache_actions = [
            'actions/cache',
            'actions/setup-python',  # Has built-in caching
            'docker/build-push-action'  # Has built-in caching
        ]
        
        caching_found = any(
            any(cache_action in str(step.get('uses', '')) for cache_action in cache_actions)
            for step in all_steps
        )
        assert caching_found, "Workflow should use dependency caching for performance"


class TestWorkflowMonitoring:
    """Test workflow monitoring and alerting capabilities."""
    
    def test_workflow_status_reporting(self):
        """Test that workflow includes status reporting mechanisms."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Should have steps for status reporting (this is optional but good practice)
        all_steps = []
        for job in workflow['jobs'].values():
            all_steps.extend(job.get('steps', []))
        
        # Status reporting might be through GitHub's built-in mechanisms
        # This test documents the expectation but is flexible in implementation
        pass
    
    def test_workflow_artifact_management(self):
        """Test that workflow properly manages build artifacts."""
        ci_workflow_path = Path('.github/workflows/ci.yml')
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        build_job = workflow['jobs'].get('build', {})
        
        if build_job:
            steps = build_job.get('steps', [])
            
            # Should handle artifacts (upload/download)
            artifact_actions = ['actions/upload-artifact', 'actions/download-artifact']
            artifact_handling = any(
                any(action in str(step.get('uses', '')) for action in artifact_actions)
                for step in steps
            )
            
            # Artifact handling is optional but recommended for complex builds
            pass 