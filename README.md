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
export GITHUB_TOKEN=YYYYYYYYYYYYYY
export PULUMI_CONFIG_PASSPHRASE=XXXXXXXXXXX
pulumi login --local
pulumi stack select <dev|prod>
pulumi refresh
pulumi up
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

In `settings > actions`:  
    - `Approval for running fork pull request workflows from contributors` must be set to `Require approval for all external contributors`  
    - In `Workflow permissions`, `Allow GitHub Actions to create and approve pull requests` must be ticked ([Github PR](https://github.com/integrations/terraform-provider-github/pull/2309))
