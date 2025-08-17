## Requirements

- uv or devcontainer

Create a fine-grained GitHub token with permissions for all repositories or some specific repositories with the following permissions:

- Administration (Read/Write)
- Contents (Read/Write)
- Issues (Read/Write) for labels
- Workflows (Read/Write) for GitHub actionss

To prevents accidental deletion of Github repository, this ressource is marked as protected and require a manual deletion.

## Run

```sh
export GITHUB_TOKEN=xxxx
export PULUMI_CONFIG_PASSPHRASE=xxxx
export AWS_ACCESS_KEY_ID=xxxx
export AWS_SECRET_ACCESS_KEY=xxxx
export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
pulumi login 's3://pulumi?region=eu-west-1&endpoint=https://nas.unicornafk.fr:9000&s3ForcePathStyle=true'
pulumi stack select <dev|prod>
pulumi refresh
pulumi up
```

### Create a stack

```sh
pulumi stack init <name>
```

### Import an existing repository

```sh
pulumi import github:index/repository:Repository <repository_name> <repository_name> --parent urn:pulumi:prod::.github::pkg:index:GitRepositoryComponent::<repository_name>
```

### Delete a ressource

```sh
pulumi stack -u
pulumi state delete 'urn:XXXXXXXX'
```

# WIP

It's currently not possible to set some repository settings

In `Code security`:
- `Dependabot > Dependabot alerts` must be enabled
- `Dependabot > Dependabot security updates` must be disabled

In `settings > actions`:
- `Approval for running fork pull request workflows from contributors` must be set to `Require approval for all external contributors`
- In `Workflow permissions`, `Allow GitHub Actions to create and approve pull requests` must be ticked ([Github PR](https://github.com/integrations/terraform-provider-github/pull/2309))
- `Require actions to be pinned to a full-length commit SHA` must be checked

In `settings > Rules > Rulesets > automation-sync`:
- `Require status checks to pass > Require branches to be up to date before merging` must be checked

It's currently not possible to set some user settings

In `settings > installations`
- Add the needed Github apps to your repositories ([Github PR](https://github.com/integrations/terraform-provider-github/pull/2469))
