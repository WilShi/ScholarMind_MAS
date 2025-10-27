# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unified API response models with `APIResponse`, `ErrorDetail`, and `PaginatedResponse`
- Environment variable support for all configuration options in `config.py`
- Comprehensive `pyproject.toml` with project metadata and tool configurations
- Pre-commit hooks configuration (`.pre-commit-config.yaml`)
- Locked dependency versions in `requirements-lock.txt`
- `CONTRIBUTING.md` with detailed contribution guidelines
- MIT License file

### Fixed
- Duplicate `safe_execute()` function definition in `error_handler.py`
- Duplicate exception handling block in `insight_generation_agent.py`
- Missing `Path` import in `resource_retrieval_agent.py`

### Changed
- Updated `.env.example` with all configuration options
- Enhanced `config.py` to support environment variable overrides for:
  - `MAX_PDF_SIZE`, `PDF_PARSE_TIMEOUT`
  - `MAX_TEXT_LENGTH`, `CHUNK_SIZE`
  - `MAX_WORKERS`, `PARALLEL_TIMEOUT`
  - `REPORT_TEMPLATE_DIR`, `OUTPUT_DIR`
  - `DEFAULT_REPORT_FORMAT`, `DEFAULT_OUTPUT_LANGUAGE`
  - `CACHE_TTL`, `CACHE_DIR`, `MAX_CACHE_SIZE`

### Improved
- Code quality and consistency across the project
- Configuration flexibility and customization options
- Development workflow with pre-commit hooks and standardized tools

## [0.1.0] - 2025-01-XX

### Added
- Initial release of ScholarMind MAS
- 5-agent DAG workflow architecture:
  - ResourceRetrievalAgent: Paper parsing and information extraction
  - MethodologyAgent: Deep methodology analysis
  - ExperimentEvaluatorAgent: Experiment design evaluation
  - InsightGenerationAgent: Critical analysis and insights
  - SynthesizerAgent: Final report generation
- Multiple input modes:
  - Interactive dialogue mode
  - Command-line mode
  - Runtime API mode (FastAPI-based)
- Academic API integrations:
  - ArXiv API support
  - Semantic Scholar API support
- Multi-language support (Chinese/English)
- User background adaptation (beginner/intermediate/advanced)
- Parallel processing for methodology and experiment agents
- Comprehensive error handling and logging
- Chinese path support
- Model availability testing
- Enhanced configuration management

### Features
- PDF, DOCX, and TXT paper parsing
- Structured output with Pydantic models
- Async/await throughout for better performance
- Flexible model configuration (OpenAI, ModelScope, custom endpoints)
- Report generation in multiple formats
- Caching support for improved performance

## [0.0.1] - 2024-XX-XX

### Added
- Initial project structure
- Basic agent implementations
- Core workflow pipeline

---

## Release Notes

### Version 0.2.0 (Upcoming)

**Code Quality Improvements**
- Fixed critical code defects (duplicate definitions, missing imports)
- Added unified API response models for consistency
- Enhanced configuration flexibility with environment variables

**Developer Experience**
- Added pre-commit hooks for code quality enforcement
- Created comprehensive contribution guidelines
- Added locked dependency versions for reproducible builds
- Configured pyproject.toml with tool settings

**Next Steps**
- Implement input validation and sanitization
- Add authentication middleware for Runtime API
- Increase test coverage to 70%+
- Add CI/CD pipeline with GitHub Actions
- Create comprehensive API documentation

### Version 0.1.0

**Initial Release**
- Complete 5-agent multi-agent system
- Support for PDF/DOCX/TXT paper analysis
- Multiple operating modes (CLI, Interactive, Runtime API)
- Academic database integrations
- Multi-language and multi-level report generation

---

For more details on each release, see the [GitHub Releases](https://github.com/WilShi/ScholarMind_MAS/releases) page.
