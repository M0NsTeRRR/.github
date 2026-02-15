## Requirements

- uv or devcontainer

Create a PAT GitHub token with permissions for all repositories or some specific repositories with the following permissions:

- repo
- workflow

To prevents accidental deletion of Github repository, this ressource is marked as protected and require a manual deletion.
PAT Github token is required for https://docs.github.com/en/rest/apps/installations?apiVersion=2022-11-28#add-a-repository-to-an-app-installation.

## Run

```sh
export GITHUB_TOKEN=xxxx
export PULUMI_CONFIG_PASSPHRASE=xxxx
export AWS_ACCESS_KEY_ID=xxxx
export AWS_SECRET_ACCESS_KEY=xxxx
export AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
pulumi login 's3://pulumi?region=eu-west-1&endpoint=https://nas.unicornafk.fr:30292&s3ForcePathStyle=true'
pulumi stack select prod
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

In `Advanced Security`:
- `Dependabot > Dependabot alerts` must be enabled ([Github issue](https://github.com/integrations/terraform-provider-github/issues/2043))

In `settings`:
- `Releases > Enable release immutability Loading` must be checked ([Github issue](https://github.com/integrations/terraform-provider-github/issues/2746))

In `settings > actions`:
- `Approval for running fork pull request workflows from contributors` must be set to `Require approval for all external contributors`
