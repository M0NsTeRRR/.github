import pulumi

from GitRepositoryComponent import GitRepositoryComponent


config = pulumi.Config()

author = config.get_object("author")

for repository_config in config.get_object("repositories"):
    repository = GitRepositoryComponent(
        name=repository_config["name"],
        author_fullname=author["fullname"],
        author_email=author["email"],
    )

    if "license" in repository_config and repository_config["license"]:
        repository.sync_licence(repository_config["license"])

    if config.get_object("funding"):
        repository.sync_funding(config.get_object("funding"))

    repository.sync_pull_request_template()

    repository.sync_issue_template()

    repository.sync_codeowner(config.get("github:owner"))

    if config.get("contact_email"):
        repository.sync_code_of_conduct(config.get("contact_email"))

    if config.get("security_email"):
        repository.sync_security(config.get("security_email"))

    if "label" in repository_config and repository_config["label"]:
        repository.sync_label(repository_config["label"])

    if "dependabot" in repository_config and repository_config["dependabot"]:
        repository.sync_dependabot(
            config.get("github:owner"), repository_config["dependabot"]
        )

    if "logo" in repository_config and bool(repository_config["logo"]):
        repository.sync_logo(repository_config["logo"])

    if "readme" in repository_config and repository_config["readme"]:
        repository.sync_readme(
            repository_config["title"],
            repository_config["description"],
            "logo" in repository_config and repository_config["logo"],
            repository_config["workflow"]["type"]
            if "workflow" in repository_config
            else None,
        )

    if "workflow" in repository_config and repository_config["workflow"]:
        repository.sync_workflow(
            repository_config["workflow"],
            "changelog" in repository_config and repository_config["changelog"],
        )
