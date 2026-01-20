import pulumi

from git_automation.GitRepositoryComponent import GitRepositoryComponent

_BUILD_PLATFORMS = {
    "docker": [
        {"os": "linux", "arch": "amd64", "runner": "ubuntu-24.04"},
        {"os": "linux", "arch": "arm64", "runner": "ubuntu-24.04-arm"},
    ],
    "go": [
        {"os": "linux", "arch": "amd64", "runner": "ubuntu-24.04"},
        {"os": "linux", "arch": "arm64", "runner": "ubuntu-24.04-arm"},
        {"os": "darwin", "arch": "amd64", "runner": "macos-15-intel"},
        {"os": "darwin", "arch": "arm64", "runner": "macos-15"},
        {"os": "windows", "arch": "amd64", "runner": "windows-2025"},
        {"os": "windows", "arch": "arm64", "runner": "windows-11-arm"},
    ],
    "rust": [
        {"target": "x86_64-unknown-linux-gnu", "runner": "ubuntu-24.04"},
        {"target": "x86_64-unknown-linux-musl", "runner": "ubuntu-24.04"},
        {"target": "aarch64-unknown-linux-gnu", "runner": "ubuntu-24.04-arm"},
        {"target": "aarch64-unknown-linux-musl", "runner": "ubuntu-24.04-arm"},
        {"target": "x86_64-apple-darwin", "runner": "macos-15-intel"},
        {"target": "aarch64-apple-darwin", "runner": "macos-15"},
        {"target": "x86_64-pc-windows-msvc", "runner": "windows-2025"},
        {"target": "x86_64-pc-windows-gnu", "runner": "windows-2025"},
        {"target": "aarch64-pc-windows-msvc", "runner": "windows-11-arm"},
    ],
}

config = pulumi.Config()

author = config.get_object("author")
owner = pulumi.Config("github").require("owner")

if author is None:
    raise ValueError("Author can't be None")

for repository_config in config.get_object("repositories", []):
    workflow = False
    workflow_lint = False
    workflow_test = False
    workflow_package = False
    workflow_documentation = False
    workflow_changelog = False
    if "workflow" in repository_config:
        workflow = True
        workflow_lint = (
            "lint" not in repository_config["workflow"]
            or repository_config["workflow"]["lint"]
        )
        workflow_test = (
            "test" not in repository_config["workflow"]
            or repository_config["workflow"]["test"]
        )
        workflow_package = (
            "package" not in repository_config["workflow"]
            or repository_config["workflow"]["package"]
        )
        workflow_changelog = (
            "changelog" not in repository_config["workflow"]
            or repository_config["workflow"]["changelog"]
        )
        workflow_documentation = (
            "documentation" in repository_config["workflow"]
            and repository_config["workflow"]["documentation"]
        )

    renovatebot = "renovatebot" in repository_config
    package_name = repository_config.get("package", None)
    devcontainer = repository_config.get("devcontainer", False)
    helm_chart_name = repository_config.get("helm_chart_name", None)
    helm = helm_chart_name is not None
    docker = repository_config.get("docker", False)
    language = repository_config.get("language", None)
    versions = repository_config.get("versions", [])
    gitignore = repository_config.get("gitignore", False)

    binary_platforms = _BUILD_PLATFORMS.get(language, None)
    docker_platforms = _BUILD_PLATFORMS["docker"] if docker else None

    repository = GitRepositoryComponent(
        owner=owner,
        name=repository_config["name"],
        default_branch_name=config.get("default_branch_name", "main"),
        branch_name=config.get("branch_name"),
        description=repository_config["description"],
        author_fullname=author["fullname"],
        author_email=author["email"],
        homepage_url=repository_config.get("homepage_url", None),
        topics=repository_config.get("topics", None),
        pages=repository_config.get("pages", None),
    )

    repository.sync_repository_ruleset(
        language,
        versions,
        binary_platforms,
        workflow_lint,
        workflow_test,
        docker,
        docker_platforms,
    )

    repository.sync_workflow_repository_permission()

    app_installation_ids = config.get_object("app_installation_ids")
    # if app_installation_ids:
    #   repository.sync_app_installation(renovatebot, app_installation_ids)

    if "license" in repository_config and repository_config["license"]:
        repository.sync_licence(repository_config["license"])

    funding = config.get_object("funding")
    if funding:
        repository.sync_funding(funding)

    repository.sync_pull_request_template()

    repository.sync_contributing()

    repository.sync_support()

    repository.sync_issue_template(language)

    repository.sync_codeowner()

    repository.sync_vscode_config(language)

    repository.sync_editorconfig(language)

    repository.sync_gitattributes()

    if gitignore:
        repository.sync_gitignore(language, helm)

    contact_email = config.get("contact_email")
    if contact_email:
        repository.sync_code_of_conduct(contact_email)

    security_email = config.get("security_email")
    if security_email:
        repository.sync_security(security_email)

    if "label" in repository_config and repository_config["label"]:
        repository.sync_label(language, docker, renovatebot)

    if renovatebot:
        renovatebot_configs = repository_config["renovatebot"].get("configs", [])

        if devcontainer and "devcontainer" not in renovatebot_configs:
            renovatebot_configs.append("devcontainers")
        if helm and "helm" not in renovatebot_configs:
            renovatebot_configs.append("helm")
        if docker and "docker" not in renovatebot_configs:
            renovatebot_configs.append("docker")
        renovatebot_configs.append(language)

        repository.sync_renovatebot(
            repository_config["renovatebot"].get("schedule", None),
            language,
            renovatebot_configs,
            repository_config["renovatebot"].get("additionnal_configs", []),
        )

    if "logo" in repository_config and bool(repository_config["logo"]):
        repository.sync_logo(repository_config["logo"])

    if "readme" in repository_config and repository_config["readme"]:
        dev = []

        if devcontainer and "devcontainer":
            dev.append("devcontainer")

        repository.sync_readme(
            repository_config["title"],
            repository_config["description"],
            repository_config.get("documentation_url", None),
            "logo" in repository_config and repository_config["logo"],
            language,
            package_name,
            workflow_lint,
            workflow_test,
            docker,
            helm,
            helm_chart_name,
            dev,
        )

    if workflow:
        repository.sync_workflow(
            package_name,
            language,
            versions,
            binary_platforms,
            workflow_lint,
            workflow_test,
            workflow_package,
            workflow_documentation,
            workflow_changelog,
            docker,
            docker_platforms,
        )
