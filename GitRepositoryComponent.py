import os
from typing import Mapping, Awaitable, Any, Dict, List
from jinja2 import Environment, FileSystemLoader

import yaml
import pulumi
from pulumi.output import Output
import pulumi_github as github


env = Environment(loader=FileSystemLoader("templates"))


class GitRepositoryComponent(pulumi.ComponentResource):
    DEFAULT_BRANCH_NAME = "main"

    def __init__(
        self,
        owner: str,
        name: str,
        description: str,
        author_fullname: str,
        author_email: str,
        homepage_url: str = None,
        topics: List[str] = None,
        pages: Dict[str, str] = None,
        props: Mapping[str, Any | Awaitable[Any] | Output[Any]] | None = None,
        opts: pulumi.ResourceOptions | None = None,
        dependency: bool = False,
    ) -> None:
        self.owner = owner
        self.name = name
        self.author_fullname = author_fullname
        self.author_email = author_email

        super().__init__(
            "pkg:index:GitRepositoryComponent", name, props, opts, dependency
        )

        if pages:
            gh_pages = pages = github.RepositoryPagesArgs(
                source=github.RepositoryPagesSourceArgs(
                    branch=pages["branch"],
                    path=pages["path"],
                ),
                cname=pages["cname"],
            )
        else:
            gh_pages = None

        self.repository = github.Repository(
            f"{self.name}",
            auto_init=True,
            allow_auto_merge=True,
            allow_merge_commit=False,
            allow_rebase_merge=True,
            allow_squash_merge=True,
            allow_update_branch=True,
            delete_branch_on_merge=True,
            description=description,
            has_discussions=False,
            has_issues=True,
            has_projects=False,
            has_wiki=False,
            homepage_url=homepage_url,
            is_template=False,
            name=name,
            pages=gh_pages,
            squash_merge_commit_message="PR_BODY",
            squash_merge_commit_title="PR_TITLE",
            topics=topics,
            visibility="public",
            vulnerability_alerts=True,
            web_commit_signoff_required=True,
            opts=pulumi.ResourceOptions(protect=True, parent=self),
        )

        default_branch = github.Branch(
            f"{self.name}-branch-{self.DEFAULT_BRANCH_NAME}",
            repository=self.name,
            branch=self.DEFAULT_BRANCH_NAME,
            opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
        )

        github.BranchDefault(
            f"{self.name}-default_branch",
            repository=self.name,
            branch=default_branch.branch,
            opts=pulumi.ResourceOptions(depends_on=[default_branch], parent=self),
        )

        self.register_outputs({"repository": self.repository.full_name})

    def _repository_file(
        self, ressource_name_type: str, file: str, content: str
    ) -> github.RepositoryFile:
        return github.RepositoryFile(
            f"{self.name}-{file}",
            repository=self.name,
            branch="main",
            file=file,
            content=content,
            commit_message=f"""\
chore(pulumi): auto-applied {ressource_name_type}

this file was auto-applied from pulumi
located here:
    - https://github.com/{self.name}/.github

Signed-off-by: {self.author_fullname} <{self.author_email}>""",
            commit_author=self.author_fullname,
            commit_email=self.author_email,
            overwrite_on_create=True,
            opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
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

    def sync_contributing(self):
        with open(os.path.join("misc", "CONTRIBUTING.md")) as file:
            file_content = file.read()

        self._repository_file(
            "contributing",
            ".github/CONTRIBUTING.md",
            file_content,
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

        self._repository_file(
            "codeowners", ".github/CODEOWNERS", template.render(owner=owner)
        )

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
            f"{self.name}-labels",
            repository=self.name,
            labels=[
                github.IssueLabelsLabelArgs(
                    name=label["name"],
                    description=label["description"],
                    color=label["color"],
                )
                for label in labels
            ],
            opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
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
        documentation_url: str,
        logo: bool,
        workflow: Dict[str, Any],
        changelog: bool,
        package_name: str = None,
    ):
        template = env.get_template(os.path.join("readme", "readme.md.j2"))

        self._repository_file(
            "readme",
            "README.md",
            template.render(
                documentation_url=documentation_url,
                repository_name=f"{self.owner}/{self.name}",
                repository_title=repository_title,
                repository_description=repository_description,
                logo=logo,
                workflow=workflow,
                changelog=changelog,
                package_name=package_name,
            ),
        )

    def sync_workflow(self, workflow: Dict[str, str], changelog: bool):
        template = env.get_template(os.path.join("workflow", "lint_pr.yml.j2"))

        self._repository_file(
            "workflow", ".github/workflows/lint_pr.yml", template.render()
        )

        if workflow["lint"] and workflow["type"] in ["python"]:
            template = env.get_template(os.path.join("workflow", "lint.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/lint.yml",
                template.render(workflow=workflow),
            )

        if workflow["test"] and workflow["type"] in ["python"]:
            template = env.get_template(os.path.join("workflow", "test.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/test.yml",
                template.render(workflow=workflow),
            )

        if changelog:
            with open(os.path.join("git-cliff", "cliff.toml")) as file:
                cliff_config = file.read()

            self._repository_file("changelog", ".github/cliff.toml", cliff_config)

        if workflow["package"] or changelog:
            template = env.get_template(os.path.join("workflow", "release.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/release.yml",
                template.render(workflow=workflow, changelog=changelog),
            )

    def sync_repository_ruleset(self):
        github.RepositoryRuleset(
            f"{self.name}-ruleset",
            name="main",
            repository=self.name,
            target="branch",
            enforcement="active",
            conditions=github.RepositoryRulesetConditionsArgs(
                ref_name=github.RepositoryRulesetConditionsRefNameArgs(
                    includes=["~DEFAULT_BRANCH"], excludes=[]
                ),
            ),
            bypass_actors=[
                github.RepositoryRulesetBypassActorArgs(
                    actor_id=1,
                    actor_type="OrganizationAdmin",
                    bypass_mode="always",
                )
            ],
            rules=github.RepositoryRulesetRulesArgs(
                creation=False,
                update=False,
                deletion=True,
                required_linear_history=True,
                required_signatures=True,
                pull_request=github.RepositoryRulesetRulesPullRequestArgs(
                    required_approving_review_count=1,
                    dismiss_stale_reviews_on_push=False,
                    require_code_owner_review=True,
                    require_last_push_approval=False,
                    required_review_thread_resolution=True,
                ),
                required_status_checks=github.RepositoryRulesetRulesRequiredStatusChecksArgs(
                    required_checks=[
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="DCO"
                        ),
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="lint_pr"
                        ),
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="lint"
                        ),
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="test"
                        ),
                    ],
                    strict_required_status_checks_policy=False,
                ),
            ),
            opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
        )
