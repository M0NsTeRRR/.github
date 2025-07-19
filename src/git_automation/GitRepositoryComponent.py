import os
from importlib import resources
from typing import Mapping, Awaitable, Any, Dict, List, Optional
import re

import requests
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
        description: str,
        author_fullname: str,
        author_email: str,
        branch_name: Optional[str] = None,
        homepage_url: Optional[str] = None,
        topics: Optional[List[str]] = None,
        pages: Optional[Dict[str, str]] = None,
        props: Mapping[str, Any | Awaitable[Any] | Output[Any]] | None = None,
        opts: pulumi.ResourceOptions | None = None,
        dependency: bool = False,
    ) -> None:
        """Repository component used to managed github repository

        :param owner: Git owner
        :param name: Repository name
        :param default_branch_name: Repository default branch
        :param description: Repository description
        :param author_fullname: Fullname used by pulumi to commit
        :param author_email: Email used by pulumi to commit
        :param branch_name: Repository branch used by pulumi
        :param homepage_url: Repository homepage
        :param topics: Repository topics
        :param pages: Repository pages
        """

        self.owner = owner
        self.name = name
        self.default_branch_name = default_branch_name
        self.author_fullname = author_fullname
        self.author_email = author_email
        self.branch_name = branch_name

        super().__init__(
            "pkg:index:GitRepositoryComponent", name, props, opts, dependency
        )

        if pages:
            gh_pages = github.RepositoryPagesArgs(
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
            security_and_analysis=github.RepositorySecurityAndAnalysisArgs(
                secret_scanning=github.RepositorySecurityAndAnalysisSecretScanningArgs(
                    status="enabled"
                ),
                secret_scanning_push_protection=github.RepositorySecurityAndAnalysisSecretScanningPushProtectionArgs(
                    status="enabled"
                ),
            ),
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

    def regenerate_readme_template(self, readme_contents: str) -> str:
        pattern = r"<!-- template:begin:(.*?) -->(.*?)<!-- template:end:\1 -->"
        matches = re.findall(pattern, readme_contents, re.DOTALL)

        for template_name, section_contents in matches:
            actual_contents = f"<!-- template:begin:{template_name} -->{section_contents}<!-- template:end:{template_name} -->"

            new_contents = f"{{% include 'readme/sections/{template_name}.md.j2' %}}"

            readme_contents = readme_contents.replace(actual_contents, new_contents)

        return readme_contents

    def is_pr_mode(self) -> bool:
        return bool(self.branch_name and self.branch_name != self.default_branch_name)

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
chore(git-sync): auto-applied {ressource_name_type}

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
        license_dir = resources.files(PACKAGE_NAME).joinpath("license", licence_name)
        for license_file in license_dir.iterdir():
            with license_file.open() as file:
                license_content = file.read()
            self._repository_file("license", license_file.name, license_content)

    def sync_funding(self, fundings: Dict[str, str]):
        template = env.get_template(os.path.join("misc", "FUNDING.yml.j2"))

        self._repository_file(
            "funding", ".github/FUNDING.yml", template.render(fundings=fundings)
        )

    def sync_contributing(self):
        with (
            resources.files(PACKAGE_NAME)
            .joinpath("misc", "CONTRIBUTING.md")
            .open() as file
        ):
            file_content = file.read()

        self._repository_file(
            "contributing",
            ".github/CONTRIBUTING.md",
            file_content,
        )

    def sync_support(self):
        with (
            resources.files(PACKAGE_NAME).joinpath("misc", "SUPPORT.md").open() as file
        ):
            file_content = file.read()

        self._repository_file(
            "support",
            ".github/SUPPORT.md",
            file_content,
        )

    def sync_pull_request_template(self):
        with (
            resources.files(PACKAGE_NAME)
            .joinpath("misc", "pull_request_template.md")
            .open() as file
        ):
            file_content = file.read()

        self._repository_file(
            "pull_request_template",
            ".github/pull_request_template.md",
            file_content,
        )

    def sync_issue_template(self):
        issue_dir = resources.files(PACKAGE_NAME).joinpath("issue")
        for issue_file in issue_dir.iterdir():
            with issue_file.open() as file:
                file_content = file.read()
            self._repository_file(
                "issue_template",
                f".github/ISSUE_TEMPLATE/{issue_file.name}",
                file_content,
            )

    def sync_code_of_conduct(self, contact_email: str):
        template = env.get_template(os.path.join("misc", "CODE_OF_CONDUCT.md.j2"))

        self._repository_file(
            "code_of_conduct",
            ".github/CODE_OF_CONDUCT.md",
            template.render(contact_email=contact_email),
        )

    def sync_codeowner(self):
        template = env.get_template(os.path.join("misc", "CODEOWNERS.j2"))

        self._repository_file(
            "codeowners", ".github/CODEOWNERS", template.render(owner=self.owner)
        )

    def sync_vscode_config(self, language: str):
        vscode_config_dir = resources.files(PACKAGE_NAME).joinpath(
            "templates", "vscode"
        )
        for vscode_file in vscode_config_dir.iterdir():
            template = env.get_template(os.path.join("vscode", vscode_file.name))
            filename = os.path.splitext(vscode_file.name)[0]

            self._repository_file(
                filename,
                f".vscode/{filename}",
                template.render(language=language),
            )

    def sync_editorconfig(self, language: str):
        template = env.get_template(os.path.join("misc", "editorconfig.j2"))

        self._repository_file(
            "editorconfig", ".editorconfig", template.render(language=language)
        )

    def sync_gitattributes(self):
        with (
            resources.files(PACKAGE_NAME)
            .joinpath("misc", "gitattributes")
            .open() as file
        ):
            file_content = file.read()

        self._repository_file("gitattributes", ".gitattributes", file_content)

    def sync_gitignore(self, language: str, helm: bool):
        template = env.get_template(os.path.join("misc", "gitignore.j2"))

        self._repository_file(
            "gitignore", ".gitignore", template.render(language=language, helm=helm)
        )

    def sync_security(self, security_email: str):
        template = env.get_template(os.path.join("misc", "SECURITY.md.j2"))

        self._repository_file(
            "security",
            ".github/SECURITY.md",
            template.render(
                repository_name=f"{self.owner}/{self.name}",
                security_email=security_email,
            ),
        )

    def sync_label(self, label_files: List[str]):
        labels = []

        for label_file in label_files:
            ressource_path = resources.files(PACKAGE_NAME).joinpath(
                "label", f"{label_file}.yml"
            )
            with ressource_path.open() as file:
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
        schedule: str,
        language: str,
        configs: List[str],
        additionnal_configs: List[str],
    ):
        template = env.get_template(os.path.join("renovatebot", "renovate.json5.j2"))

        self._repository_file(
            "renovate",
            ".github/renovate.json5",
            template.render(
                repository_name=f"{self.owner}/{self.name}",
                schedule=schedule,
                configs=configs,
                additionnal_configs=additionnal_configs,
            ),
        )

        renovatebot_config_dir = (
            resources.files(PACKAGE_NAME) / "templates" / "renovatebot" / "config"
        )

        renovatebot_config_dir = resources.files(PACKAGE_NAME).joinpath(
            "templates", "renovatebot", "config"
        )
        for renovatebot_file in renovatebot_config_dir.iterdir():
            template = env.get_template(
                os.path.join("renovatebot", "config", renovatebot_file.name)
            )
            filename = os.path.splitext(renovatebot_file.name)[0]

            self._repository_file(
                filename,
                f".github/renovate/{filename}",
                template.render(
                    language=language,
                    configs=configs,
                    additionnal_configs=additionnal_configs,
                ),
            )

    def sync_logo(self, logo: str):
        with resources.files(PACKAGE_NAME).joinpath("logo", logo).open() as file:
            file_content = file.read()

        self._repository_file("logo", "docs/assets/logo.svg", file_content)

    def sync_readme(
        self,
        repository_title: str,
        repository_description: str,
        documentation_url: str,
        logo: bool,
        language: str,
        package_name: str,
        package: bool,
        changelog: bool,
        lint: bool,
        test: bool,
        docker: bool,
        helm: bool,
        dev: List[str],
    ):
        # check if a readme already exist
        r = requests.get(
            f"https://api.github.com/repos/{self.owner.lower()}/{self.name.lower()}/contents/README.md",
            headers={
                "Accept": "application/vnd.github.raw+json",
                "Authorization": f"{os.environ['GITHUB_TOKEN']}",
            },
        )
        if r.status_code == 200:
            template = env.from_string(self.regenerate_readme_template(r.text))
        else:
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
                package_name=package_name,
                package=package,
                changelog=changelog,
                lint=lint,
                test=test,
                docker=docker,
                helm=helm,
                dev=dev,
            ),
        )

    def sync_workflow(
        self,
        language: str,
        versions: List[str],
        lint: bool,
        test: bool,
        package: bool,
        documentation: bool,
        changelog: bool,
        docker: bool,
    ):
        template = env.get_template(os.path.join("workflow", "lint-pr.yml.j2"))
        self._repository_file(
            "workflow",
            ".github/workflows/lint-pr.yml",
            template.render(),
        )

        template = env.get_template(os.path.join("workflow", "scorecard.yml.j2"))
        self._repository_file(
            "workflow",
            ".github/workflows/scorecard.yml",
            template.render(),
        )

        template = env.get_template(os.path.join("workflow", "codeql.yml.j2"))
        self._repository_file(
            "workflow",
            ".github/workflows/codeql.yml",
            template.render(language=language),
        )

        template = env.get_template(os.path.join("workflow", "dependency-review.yml.j2"))
        self._repository_file(
            "workflow",
            ".github/workflows/dependency-review.yml",
            template.render(language=language),
        )

        if self.is_pr_mode():
            template = env.get_template(
                os.path.join("workflow", "automation-sync-pr.yml.j2")
            )

            self._repository_file(
                "workflow",
                ".github/workflows/automation-sync-pr.yml",
                template.render(
                    default_branch_name=self.default_branch_name,
                    branch_name=self.branch_name,
                ),
            )

        if lint:
            template = env.get_template(os.path.join("workflow", "lint.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/lint.yml",
                template.render(language=language),
            )

        if test:
            template = env.get_template(os.path.join("workflow", "test.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/test.yml",
                template.render(language=language, versions=versions),
            )

        if changelog:
            with (
                resources.files(PACKAGE_NAME)
                .joinpath("git-cliff", "cliff.toml")
                .open() as file
            ):
                cliff_config = file.read()

            self._repository_file("changelog", ".github/cliff.toml", cliff_config)

        if package or changelog:
            template = env.get_template(os.path.join("workflow", "release.yml.j2"))

            self._repository_file(
                "workflow",
                ".github/workflows/release.yml",
                template.render(
                    language=language,
                    package=package,
                    documentation=documentation,
                    changelog=changelog,
                    docker=docker,
                ),
            )

    def sync_repository_ruleset(
        self, language: str, versions: List[str], lint: bool, test: bool
    ):
        required_checks = [
            github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                context="DCO"
            ),
            github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                context="Validate PR title", integration_id=15368
            ),
            github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                context="Analyze (actions)", integration_id=15368
            ),
            github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                context=f"Analyze ({language})", integration_id=15368
            ),
        ]

        if lint:
            required_checks.append(
                github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                    context="Lint", integration_id=15368
                )
            )
        if test:
            for version in versions:
                required_checks.append(
                    github.RepositoryRulesetRulesRequiredStatusChecksRequiredCheckArgs(
                        context=f"Test ({version})", integration_id=15368
                    ),
                )

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
                non_fast_forward=True,
                required_linear_history=True,
                required_signatures=True,
                pull_request=github.RepositoryRulesetRulesPullRequestArgs(
                    required_approving_review_count=1,
                    dismiss_stale_reviews_on_push=True,
                    require_code_owner_review=True,
                    require_last_push_approval=True,
                    required_review_thread_resolution=True,
                ),
                required_status_checks=github.RepositoryRulesetRulesRequiredStatusChecksArgs(
                    required_checks=required_checks,
                    strict_required_status_checks_policy=False,
                ),
                required_code_scanning=github.RepositoryRulesetRulesRequiredCodeScanningArgs(
                    required_code_scanning_tools=[
                        github.RepositoryRulesetRulesRequiredCodeScanningRequiredCodeScanningToolArgs(
                            alerts_threshold="errors_and_warnings",
                            security_alerts_threshold="medium_or_higher",
                            tool="CodeQL",
                        )
                    ]
                ),
            ),
            opts=pulumi.ResourceOptions(depends_on=[self.repository], parent=self),
        )

    def sync_app_installation(
        self, renovatebot: bool, app_installation_ids: Dict[str, str]
    ):
        for k, v in app_installation_ids:
            if k == "renovatebot" and not renovatebot:
                continue

            github.AppInstallationRepository(
                f"{self.name}-{k}", installation_id=f"{v}", repository=self.name
            )
