import pulumi

from git_automation.GitRepositoryComponent import GitRepositoryComponent


config = pulumi.Config()

author = config.get_object("author")
owner = pulumi.Config("github").require("owner")

for repository_config in config.get_object("repositories"):
    if "workflow" in repository_config:
        workflow = {
            "lint": "lint" not in repository_config["workflow"]
            or repository_config["workflow"]["lint"],
            "test": "test" not in repository_config["workflow"]
            or repository_config["workflow"]["test"],
            "package": "package" not in repository_config["workflow"]
            or repository_config["workflow"]["package"],
        }
    else:
        workflow = None

    changelog = repository_config.get("changelog", None)

    devcontainer = repository_config.get("devcontainer", False)
    helm = repository_config.get("helm", False)
    docker = repository_config.get("docker", False)
    language = repository_config.get("language", None)

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

    repository.sync_repository_ruleset()

    if "license" in repository_config and repository_config["license"]:
        repository.sync_licence(repository_config["license"])

    if config.get_object("funding"):
        repository.sync_funding(config.get_object("funding"))

    repository.sync_pull_request_template()

    repository.sync_contributing()

    repository.sync_issue_template()

    repository.sync_codeowner(owner)

    if config.get("contact_email"):
        repository.sync_code_of_conduct(config.get("contact_email"))

    if config.get("security_email"):
        repository.sync_security(config.get("security_email"))

    if "label" in repository_config and repository_config["label"]:
        repository.sync_label(repository_config["label"])

    if "renovatebot" in repository_config and repository_config["renovatebot"]:
        renovatebot_configs = repository_config["renovatebot"].get("configs", [])

        if devcontainer and "devcontainer" not in renovatebot_configs:
            renovatebot_configs.append("devcontainer")
        if helm and "helm" not in renovatebot_configs:
            renovatebot_configs.append("helm")
        if docker and "docker" not in renovatebot_configs:
            renovatebot_configs.append("docker")

        repository.sync_renovatebot(
            owner,
            repository_config["renovatebot"].get("schedule", None),
            renovatebot_configs,
            repository_config["renovatebot"].get("additionnal_configs", []),
        )

    if "logo" in repository_config and bool(repository_config["logo"]):
        repository.sync_logo(repository_config["logo"])

    if "readme" in repository_config and repository_config["readme"]:
        dev = []

        if devcontainer and "devcontainer":
            dev.append("devcontainer")

        usage = []

        if helm and "helm":
            usage.append("helm")
        if docker and "docker":
            usage.append("docker")

        repository.sync_readme(
            repository_config["title"],
            repository_config["description"],
            repository_config.get("documentation_url", None),
            "logo" in repository_config and repository_config["logo"],
            changelog,
            language,
            workflow,
            repository_config.get("package_name", None),
            dev,
            usage,
        )

    if workflow or changelog:
        repository.sync_workflow(
            language,
            workflow,
            changelog,
        )
