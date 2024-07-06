import pulumi

from GitRepositoryComponent import GitRepositoryComponent


config = pulumi.Config()

author = config.get_object("author")

for repository_config in config.get_object("repositories"):
    repository = GitRepositoryComponent(
        owner=pulumi.Config("github").require("owner"),
        name=repository_config["name"],
        description=repository_config["description"],
        author_fullname=author["fullname"],
        author_email=author["email"],
        homepage_url=repository_config["homepage_url"]
        if "homepage_url" in repository_config
        else None,
        topics=repository_config["topics"] if "topics" in repository_config else None,
        pages=repository_config["pages"] if "pages" in repository_config else None,
    )

    # repository.sync_repository_ruleset()

    if "license" in repository_config and repository_config["license"]:
        repository.sync_licence(repository_config["license"])

    if config.get_object("funding"):
        repository.sync_funding(config.get_object("funding"))

    repository.sync_pull_request_template()

    repository.sync_contributing()

    repository.sync_issue_template()

    repository.sync_codeowner(author["username"])

    if config.get("contact_email"):
        repository.sync_code_of_conduct(config.get("contact_email"))

    if config.get("security_email"):
        repository.sync_security(config.get("security_email"))

    if "label" in repository_config and repository_config["label"]:
        repository.sync_label(repository_config["label"])

    if "dependabot" in repository_config and repository_config["dependabot"]:
        repository.sync_dependabot(author["username"], repository_config["dependabot"])

    if "logo" in repository_config and bool(repository_config["logo"]):
        repository.sync_logo(repository_config["logo"])

    if "readme" in repository_config and repository_config["readme"]:
        repository.sync_readme(
            repository_config["title"],
            repository_config["description"],
            repository_config["homepage_url"]
            if "homepage_url" in repository_config
            else None,
            "logo" in repository_config and repository_config["logo"],
            repository_config["workflow"] if "workflow" in repository_config else None,
        )

    if "workflow" in repository_config and repository_config["workflow"]:
        repository.sync_workflow(
            repository_config["workflow"],
            "changelog" in repository_config and repository_config["changelog"],
        )
