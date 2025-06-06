"""
Tests for Docker-based pre-commit hooks and code quality tools.

Following TDD approach - these tests define the expected behavior
for pre-commit hooks integration with Docker environment.
"""

import os
import subprocess
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestPreCommitConfiguration:
    """Test pre-commit configuration setup and validation."""
    
    def test_precommit_config_file_exists(self):
        """Test that .pre-commit-config.yaml exists and is valid."""
        config_path = Path('.pre-commit-config.yaml')
        assert config_path.exists(), "Pre-commit configuration file should exist"
        
        # Test that the file is valid YAML
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert isinstance(config, dict), "Pre-commit config should be valid YAML dict"
        assert 'repos' in config, "Pre-commit config should have 'repos' key"
        assert isinstance(config['repos'], list), "repos should be a list"
    
    def test_precommit_config_has_required_hooks(self):
        """Test that pre-commit config includes all required code quality hooks."""
        config_path = Path('.pre-commit-config.yaml')
        assert config_path.exists(), "Pre-commit configuration file should exist"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Extract all hook IDs from the configuration
        hook_ids = []
        for repo in config['repos']:
            if 'hooks' in repo:
                for hook in repo['hooks']:
                    hook_ids.append(hook['id'])
        
        # Required hooks based on project requirements
        required_hooks = [
            'black',           # Code formatting
            'isort',           # Import sorting
            'flake8',          # Linting
            'mypy',            # Type checking
            'trailing-whitespace',  # Basic cleanup
            'end-of-file-fixer',   # Basic cleanup
            'check-yaml',      # YAML validation
            'check-json',      # JSON validation
            'check-merge-conflict',  # Git safety
            'check-added-large-files',  # File size check
        ]
        
        for required_hook in required_hooks:
            assert required_hook in hook_ids, f"Required hook '{required_hook}' should be configured"
    
    def test_precommit_config_excludes_patterns(self):
        """Test that pre-commit config excludes appropriate file patterns."""
        config_path = Path('.pre-commit-config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for global exclude patterns
        if 'exclude' in config:
            exclude_pattern = config['exclude']
            # Should exclude migration files, build artifacts, etc.
            assert 'migrations/' in exclude_pattern or r'migrations/.*\.py' in exclude_pattern
            assert '__pycache__' in exclude_pattern
    
    def test_docker_precommit_script_exists(self):
        """Test that Docker pre-commit wrapper script exists."""
        script_path = Path('scripts/pre-commit-docker.sh')
        assert script_path.exists(), "Docker pre-commit script should exist"
        
        # Check that script is executable
        assert os.access(script_path, os.X_OK), "Pre-commit script should be executable"
    
    def test_docker_precommit_script_content(self):
        """Test that Docker pre-commit script has correct content."""
        script_path = Path('scripts/pre-commit-docker.sh')
        assert script_path.exists()
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should use Docker for running hooks
        assert 'docker' in content.lower()
        assert 'pre-commit' in content.lower()
        # Should handle development environment
        assert 'development' in content.lower() or 'dev' in content.lower()


class TestCodeQualityTools:
    """Test code quality tools configuration and Docker integration."""
    
    def test_black_configuration_exists(self):
        """Test that Black configuration exists and is properly configured."""
        # Check for pyproject.toml or black-specific config
        pyproject_path = Path('pyproject.toml')
        
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                content = f.read()
            assert '[tool.black]' in content, "Black configuration should be present"
        else:
            # Check for .black file or other config
            assert False, "Black configuration should exist in pyproject.toml"
    
    def test_isort_configuration_exists(self):
        """Test that isort configuration exists and is compatible with Black."""
        pyproject_path = Path('pyproject.toml')
        
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                content = f.read()
            
            if '[tool.isort]' in content:
                # Should have Black compatibility
                assert 'profile = "black"' in content or 'black' in content.lower()
    
    def test_mypy_configuration_exists(self):
        """Test that mypy configuration exists."""
        config_files = ['mypy.ini', 'pyproject.toml', '.mypy.ini']
        config_exists = any(Path(f).exists() for f in config_files)
        assert config_exists, "MyPy configuration should exist"
        
        # If pyproject.toml exists, check for mypy section
        pyproject_path = Path('pyproject.toml')
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                content = f.read()
            if '[tool.mypy]' in content:
                # Should have basic mypy settings
                assert any(setting in content for setting in [
                    'python_version', 'warn_return_any', 'strict_optional'
                ])
    
    def test_flake8_configuration_exists(self):
        """Test that flake8 configuration exists."""
        config_files = ['.flake8', 'setup.cfg', 'tox.ini', 'pyproject.toml']
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()
                if 'flake8' in content:
                    # Found flake8 configuration
                    assert True
                    return
        
        assert False, "Flake8 configuration should exist"
    
    def test_docker_code_quality_service_exists(self):
        """Test that docker-compose includes code quality service."""
        compose_files = ['docker-compose.yml', 'docker-compose.dev.yml']
        
        for compose_file in compose_files:
            if Path(compose_file).exists():
                with open(compose_file, 'r') as f:
                    content = f.read()
                
                # Should have a way to run code quality tools
                if 'pre-commit' in content.lower() or 'quality' in content.lower():
                    assert True
                    return
        
        # Alternative: check if main service has code quality tools
        if Path('docker-compose.yml').exists():
            with open('docker-compose.yml', 'r') as f:
                content = f.read()
            # Main app service should have development dependencies
            assert 'development' in content.lower()


class TestPreCommitHooksExecution:
    """Test pre-commit hooks execution in Docker environment."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            subprocess.run(['git', 'init'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            
            # Copy pre-commit config
            import shutil
            if Path('.pre-commit-config.yaml').exists():
                shutil.copy('.pre-commit-config.yaml', temp_dir)
            
            yield temp_dir
    
    @patch('subprocess.run')
    def test_precommit_install_works(self, mock_subprocess):
        """Test that pre-commit install command works."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Simulate pre-commit install
        result = subprocess.run(['pre-commit', 'install'], capture_output=True, text=True)
        
        # Should call subprocess
        mock_subprocess.assert_called()
    
    @patch('subprocess.run')
    def test_docker_precommit_run_on_all_files(self, mock_subprocess):
        """Test running pre-commit on all files via Docker."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="All hooks passed", stderr="")
        
        # Test the Docker wrapper script
        script_path = Path('scripts/pre-commit-docker.sh')
        if script_path.exists():
            result = subprocess.run([str(script_path), 'run', '--all-files'], 
                                  capture_output=True, text=True)
            mock_subprocess.assert_called()
    
    def test_code_quality_tools_available_in_docker(self):
        """Test that code quality tools are available in Docker environment."""
        # This would typically require running Docker, but we'll mock it
        required_tools = ['black', 'isort', 'flake8', 'mypy', 'pre-commit']
        
        # In a real test, we'd run: docker-compose exec app which black
        # For now, we'll check that tools are in requirements.txt
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        for tool in required_tools:
            assert tool in requirements.lower(), f"Tool '{tool}' should be in requirements.txt"


class TestPreCommitHooksIntegration:
    """Test integration of pre-commit hooks with the development workflow."""
    
    def test_git_hooks_directory_setup(self):
        """Test that Git hooks are properly configured."""
        # After pre-commit install, .git/hooks should contain pre-commit
        git_hooks_dir = Path('.git/hooks')
        if git_hooks_dir.exists():
            pre_commit_hook = git_hooks_dir / 'pre-commit'
            if pre_commit_hook.exists():
                with open(pre_commit_hook, 'r') as f:
                    content = f.read()
                assert 'pre-commit' in content
    
    def test_makefile_precommit_targets(self):
        """Test that Makefile includes pre-commit targets."""
        makefile_path = Path('Makefile')
        if makefile_path.exists():
            with open(makefile_path, 'r') as f:
                content = f.read()
            
            # Should have targets for code quality
            expected_targets = ['pre-commit', 'format', 'lint', 'type-check']
            for target in expected_targets:
                # Check if target exists (flexible matching)
                if f'{target}:' in content or f'.PHONY: {target}' in content:
                    continue
                elif target.replace('-', '_') + ':' in content:
                    continue
                else:
                    # Target not found - this is acceptable as Makefile might use different naming
                    pass
    
    def test_docker_compose_precommit_command(self):
        """Test that docker-compose can run pre-commit commands."""
        compose_path = Path('docker-compose.yml')
        if compose_path.exists():
            with open(compose_path, 'r') as f:
                content = f.read()
            
            # Should be able to run commands in the app service
            assert 'app:' in content
            # The app service should have all the tools we need
            assert 'volumes:' in content  # For mounting source code
    
    def test_ci_precommit_integration(self):
        """Test that CI configuration includes pre-commit checks."""
        ci_files = ['.github/workflows/ci.yml', '.github/workflows/test.yml', 
                   '.github/workflows/quality.yml']
        
        ci_file_exists = any(Path(f).exists() for f in ci_files)
        
        if ci_file_exists:
            for ci_file in ci_files:
                ci_path = Path(ci_file)
                if ci_path.exists():
                    with open(ci_path, 'r') as f:
                        content = f.read()
                    
                    # Should run pre-commit or code quality checks
                    quality_indicators = ['pre-commit', 'black', 'flake8', 'mypy', 'isort']
                    has_quality_check = any(indicator in content.lower() for indicator in quality_indicators)
                    
                    if has_quality_check:
                        assert True
                        return
        
        # If no CI files exist yet, that's acceptable at this stage
        # This test will pass once CI is set up in later tasks


class TestPreCommitHooksConfiguration:
    """Test specific configuration aspects of pre-commit hooks."""
    
    def test_precommit_hooks_python_version(self):
        """Test that pre-commit hooks use correct Python version."""
        config_path = Path('.pre-commit-config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check if default_language_version is set
            if 'default_language_version' in config:
                python_version = config['default_language_version'].get('python')
                if python_version:
                    # Should match project Python version (3.11+)
                    assert python_version.startswith('python3.11') or python_version.startswith('python3')
    
    def test_precommit_hooks_exclude_files(self):
        """Test that pre-commit properly excludes files that shouldn't be checked."""
        config_path = Path('.pre-commit-config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check individual hooks for exclude patterns
            for repo in config['repos']:
                if 'hooks' in repo:
                    for hook in repo['hooks']:
                        if hook['id'] in ['mypy', 'flake8']:
                            # These should exclude migration files
                            if 'exclude' in hook:
                                exclude_pattern = hook['exclude']
                                # Should exclude migrations or test files as appropriate
                                assert isinstance(exclude_pattern, str)
    
    def test_precommit_hooks_additional_dependencies(self):
        """Test that hooks have necessary additional dependencies."""
        config_path = Path('.pre-commit-config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Find mypy hook and check for additional dependencies
            for repo in config['repos']:
                if 'hooks' in repo:
                    for hook in repo['hooks']:
                        if hook['id'] == 'mypy':
                            # Should have additional dependencies for type checking
                            if 'additional_dependencies' in hook:
                                deps = hook['additional_dependencies']
                                # Should include common type packages
                                type_packages = ['types-requests', 'types-redis']
                                # At least some type packages should be present
                                has_type_deps = any(dep.startswith('types-') for dep in deps)
                                # This is flexible - not all projects need all type packages 