import os
from typing import Mapping, Awaitable, Any, Dict, List
from jinja2 import Environment, FileSystemLoader

import yaml
import pulumi
from pulumi.output import Output
import pulumi_github as github


env = Environment(loader=FileSystemLoader("templates"))


class GitRepositoryComponent(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        author_fullname: str,
        author_email: str,
        props: Mapping[str, Any | Awaitable[Any] | Output[Any]] | None = None,
        opts: pulumi.ResourceOptions | None = None,
        dependency: bool = False,
    ) -> None:
        self.author_fullname = author_fullname
        self.author_email = author_email

        # By calling super(), we ensure any instantiation of this class inherits from the ComponentResource class so we don't have to declare all the same things all over again.
        super().__init__(
            "my:modules:GitRepositoryComponent", name, props, opts, dependency
        )
        # This definition ensures the new component resource acts like anything else in the Pulumi ecosystem when being called in code.
        child_opts = pulumi.ResourceOptions(parent=self)  # noqa #F841

        self.repository = github.get_repository(full_name=name)

        self.register_outputs({})

    def _repository_file(
        self, ressource_name_type: str, file: str, content: str
    ) -> github.RepositoryFile:
        return github.RepositoryFile(
            f"{self.repository.full_name}_{file}",
            repository=self.repository.name,
            branch="main",
            file=file,
            content=content,
            commit_message=f"""\
chore(pulumi): auto-applied {ressource_name_type}

this file was auto-applied from pulumi
located here:
    - https://github.com/{self.repository.full_name}/.github

Signed-off-by: {self.author_fullname} <{self.author_email}>""",
            commit_author=self.author_fullname,
            commit_email=self.author_email,
            overwrite_on_create=True,
        )

    def sync_licence(self, licence_name: str):
        license_dir = os.path.join("license", licence_name)
        license_files = os.listdir(license_dir)
        for license_file in license_files:
            with open(os.path.join(license_dir, license_file)) as file:
                license_content = file.read()
            self._repository_file("license", license_file, license_content)

    def sync_funding(self, fundings: Dict[str, str]):
        template = env.get_template(os.path.join("misc", "FUNDING.yml.j2"))

        self._repository_file(
            "funding", ".github/FUNDING.yml", template.render(fundings=fundings)
        )

    def sync_pull_request_template(self):
        with open(os.path.join("misc", "pull_request_template.md")) as file:
            file_content = file.read()

        self._repository_file(
            "pull_request_template",
            ".github/pull_request_template.md",
            file_content,
        )

    def sync_issue_template(self):
        issue_dir = os.path.join("issue")
        issue_files = os.listdir(issue_dir)
        for issue_file in issue_files:
            with open(os.path.join(issue_dir, issue_file)) as file:
                file_content = file.read()
            self._repository_file(
                "issue_template", f".github/ISSUE_TEMPLATE/{issue_file}", file_content
            )

    def sync_code_of_conduct(self, contact_email: str):
        template = env.get_template(os.path.join("misc", "CODE_OF_CONDUCT.md.j2"))

        self._repository_file(
            "code_of_conduct",
            ".github/CODE_OF_CONDUCT.md",
            template.render(contact_email=contact_email),
        )

    def sync_codeowner(self, owner: str):
        template = env.get_template(os.path.join("misc", "CODEOWNERS.j2"))

        self._repository_file("codeowners", "CODEOWNERS", template.render(owner=owner))

    def sync_security(self, security_email: str):
        template = env.get_template(os.path.join("misc", "SECURITY.md.j2"))

        self._repository_file(
            "security",
            ".github/SECURITY.md",
            template.render(security_email=security_email),
        )

    def sync_label(self, label_files: List[str]):
        labels = []

        for label_file in label_files:
            with open(os.path.join("label", f"{label_file}.yaml")) as file:
                labels += yaml.safe_load(file.read())

        github.IssueLabels(
            f"{self.repository.full_name}_label",
            repository=self.repository.name,
            labels=[
                github.IssueLabelsLabelArgs(
                    name=label["name"],
                    description=label["description"],
                    color=label["color"],
                )
                for label in labels
            ],
        )

    def sync_dependabot(self, owner: str, configs: List[str]):
        template = env.get_template(os.path.join("dependabot", "dependabot.yml.j2"))

        self._repository_file(
            "dependabot",
            ".github/dependabot.yml",
            template.render(owner=owner, configs=configs),
        )

    def sync_logo(self, logo: str):
        with open(os.path.join("logo", logo)) as file:
            file_content = file.read()

        self._repository_file("logo", "docs/assets/logo.svg", file_content)

    def sync_readme(
        self,
        repository_title: str,
        repository_description: str,
        logo: bool,
        workflow_type: str,
        package_name: str = None,
    ):
        template = env.get_template(os.path.join("readme", "readme.md.j2"))

        self._repository_file(
            "readme",
            "README.md",
            template.render(
                documentation_url=self.repository.homepage_url,
                repository_full_name=self.repository.full_name,
                repository_title=repository_title,
                repository_description=repository_description,
                logo=logo,
                workflow_type=workflow_type,
                package_name=package_name,
            ),
        )

    def sync_workflow(self, workflow: Dict[str, str], changelog: bool):
        if changelog:
            with open(os.path.join("git-cliff", "cliff.toml")) as file:
                cliff_config = file.read()

            self._repository_file("changelog", ".github/cliff.toml", cliff_config)

        if workflow["type"] in ["python"]:
            template = env.get_template(os.path.join("workflow", "lint.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/lint.yml",
                template.render(type=workflow["type"]),
            )

        if workflow["type"] in ["python"]:
            template = env.get_template(os.path.join("workflow", "test.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/test.yml",
                template.render(type=workflow["type"]),
            )

        if workflow["type"] in ["python", "go"]:
            template = env.get_template(os.path.join("workflow", "release.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/release.yml",
                template.render(type=workflow["type"], changelog=changelog),
            )
