import os
from importlib import resources
from typing import Mapping, Awaitable, Any, Dict, List

from jinja2 import Environment, PackageLoader
import yaml
import pulumi
from pulumi.output import Output
import pulumi_github as github


PACKAGE_NAME = __name__.split(".")[0]

env = Environment(loader=PackageLoader(PACKAGE_NAME, "templates"))


class GitRepositoryComponent(pulumi.ComponentResource):
    def __init__(
        self,
        owner: str,
        name: str,
        default_branch_name: str,
        branch_name: str,
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
        """Repository component used to managed github repository

        :param owner: Git owner
        :param name: Repository name
        :param default_branch_name: Repository default branch
        :param branch_name: Repository branch used by pulumi
        :param description: Repository description
        :param author_fullname: Fullname used by pulumi to commit
        :param author_email: Email used by pulumi to commit
        :param homepage_url: Repository homepage
        :param topics: Repository topics
        :param pages: Repository pages
        """

        self.owner = owner
        self.name = name
        self.branch_name = branch_name
        self.default_branch_name = default_branch_name
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

        # configure default branch
        self.default_branch = github.Branch(
            f"{self.name}-branch-{self.default_branch_name}",
            repository=self.name,
            branch=self.default_branch_name,
            opts=pulumi.ResourceOptions(
                protect=True, depends_on=[self.repository], parent=self
            ),
        )

        github.BranchDefault(
            f"{self.name}-default_branch",
            repository=self.name,
            branch=self.default_branch.branch,
            opts=pulumi.ResourceOptions(depends_on=[self.default_branch], parent=self),
        )

        # create sync branch if not on DEFAULT_BRANCH_NAME
        if branch_name and branch_name != default_branch_name:
            self.branch = github.Branch(
                f"{self.name}-branch-{self.branch_name}",
                repository=self.name,
                branch=self.branch_name,
                opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
            )

        self.register_outputs({"repository": self.repository.full_name})

    def is_pr_mode(self) -> bool:
        return self.branch_name and self.branch_name != self.default_branch_name

    def get_working_branch(self) -> github.Branch:
        if self.is_pr_mode():
            return self.branch
        else:
            return self.default_branch

    def _repository_file(
        self, ressource_name_type: str, file: str, content: str
    ) -> github.RepositoryFile:
        return github.RepositoryFile(
            f"{self.name}-{file}",
            repository=self.name,
            branch=self.get_working_branch().branch,
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
            opts=pulumi.ResourceOptions(
                depends_on=[self.repository, self.branch], parent=self
            ),
        )

    def sync_licence(self, licence_name: str):
        license_dir = resources.files(PACKAGE_NAME) / "license" / licence_name
        license_files = os.listdir(license_dir)
        for license_file in license_files:
            with open(license_dir / license_file) as file:
                license_content = file.read()
            self._repository_file("license", license_file, license_content)

    def sync_funding(self, fundings: Dict[str, str]):
        template = env.get_template(os.path.join("misc", "FUNDING.yml.j2"))

        self._repository_file(
            "funding", ".github/FUNDING.yml", template.render(fundings=fundings)
        )

    def sync_contributing(self):
        with open(resources.files(PACKAGE_NAME) / "misc" / "CONTRIBUTING.md") as file:
            file_content = file.read()

        self._repository_file(
            "contributing",
            ".github/CONTRIBUTING.md",
            file_content,
        )

    def sync_pull_request_template(self):
        with open(
            resources.files(PACKAGE_NAME) / "misc" / "pull_request_template.md"
        ) as file:
            file_content = file.read()

        self._repository_file(
            "pull_request_template",
            ".github/pull_request_template.md",
            file_content,
        )

    def sync_issue_template(self):
        issue_dir = resources.files(PACKAGE_NAME) / "issue"
        issue_files = os.listdir(issue_dir)
        for issue_file in issue_files:
            with open(issue_dir / issue_file) as file:
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

    def sync_editorconfig(self, language: str):
        template = env.get_template(os.path.join("misc", "editorconfig.j2"))

        self._repository_file(
            "codeowners", ".editorconfig", template.render(language=language)
        )

    def sync_gitattributes(self):
        template = env.get_template(os.path.join("misc", "gitattributes.j2"))

        self._repository_file("codeowners", ".gitattributes", template.render())

    def sync_gitignore(self, language: str, helm: bool):
        template = env.get_template(os.path.join("misc", "gitignore.j2"))

        self._repository_file(
            "codeowners", ".gitignore", template.render(language=language, helm=helm)
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
            with open(
                resources.files(PACKAGE_NAME) / "label" / f"{label_file}.yml"
            ) as file:
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

    def sync_renovatebot(
        self,
        owner: str,
        schedule: str,
        configs: List[str],
        additionnal_configs: List[str],
    ):
        template = env.get_template(os.path.join("renovatebot", "renovatebot.json5.j2"))

        self._repository_file(
            "renovatebot",
            ".github/renovatebot.json5",
            template.render(
                owner=owner,
                schedule=schedule,
                configs=configs,
                additionnal_configs=additionnal_configs,
            ),
        )

        renovatebot_dir = (
            resources.files(PACKAGE_NAME) / "templates" / "renovatebot" / "config"
        )
        renovatebot_files = os.listdir(renovatebot_dir)
        for renovatebot_file in renovatebot_files:
            with open(renovatebot_dir / renovatebot_file) as file:
                renovatebot_content = file.read()
            self._repository_file(
                os.path.splitext(renovatebot_file)[0],
                f".github/renovatebot/{renovatebot_file}",
                renovatebot_content,
            )

    def sync_logo(self, logo: str):
        with open(resources.files(PACKAGE_NAME) / "logo" / logo) as file:
            file_content = file.read()

        self._repository_file("logo", "docs/assets/logo.svg", file_content)

    def sync_readme(
        self,
        repository_title: str,
        repository_description: str,
        documentation_url: str,
        logo: bool,
        language: str,
        workflow: Dict[str, Any],
        changelog: bool,
        docker: bool,
        helm: bool,
        package: str,
        library: bool,
        lint: bool,
        test: bool,
        dev: List[str],
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
                language=language,
                workflow=workflow,
                changelog=changelog,
                docker=docker,
                helm=helm,
                package=package,
                library=library,
                lint=lint,
                test=test,
                dev=dev,
            ),
        )

    def sync_workflow(
        self,
        language: str,
        workflow: Dict[str, str],
        changelog: bool,
        package: bool,
        docker: bool,
    ):
        template = env.get_template(os.path.join("workflow", "lint_pr.yml.j2"))

        self._repository_file(
            "workflow",
            ".github/workflows/lint_pr.yml",
            template.render(repository_name=f"{self.owner}/{self.name}"),
        )

        if self.is_pr_mode():
            template = env.get_template(
                os.path.join("workflow", "automation-sync-pr.j2")
            )

            self._repository_file(
                "workflow",
                ".github/workflows/automation-sync-pr.yml",
                template.render(
                    default_branch_name=self.default_branch_name,
                    branch_name=self.branch_name,
                ),
            )

        if workflow["lint"]:
            template = env.get_template(os.path.join("workflow", "lint.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/lint.yml",
                template.render(language=language, workflow=workflow),
            )

        if workflow["test"]:
            template = env.get_template(os.path.join("workflow", "test.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/test.yml",
                template.render(language=language, workflow=workflow),
            )

        if changelog:
            with open(
                resources.files(PACKAGE_NAME) / "git-cliff" / "cliff.toml"
            ) as file:
                cliff_config = file.read()

            self._repository_file("changelog", ".github/cliff.toml", cliff_config)

        if package or changelog:
            template = env.get_template(os.path.join("workflow", "release.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/release.yml",
                template.render(
                    language=language,
                    workflow=workflow,
                    changelog=changelog,
                    package=package,
                    docker=docker,
                ),
            )

    def sync_repository_ruleset(self):
        github.RepositoryRuleset(
            f"{self.name}-ruleset",
            name="automation-sync",
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
                    actor_id=5,
                    actor_type="RepositoryRole",
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
                            context="GitGuardian"
                        ),
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="Validate PR title", integration_id=15368
                        ),
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="Lint", integration_id=15368
                        ),
                        github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                            context="Test", integration_id=15368
                        ),
                    ],
                    strict_required_status_checks_policy=False,
                ),
            ),
            opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
        )
