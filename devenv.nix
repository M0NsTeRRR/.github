{
  pkgs,
  lib,
  config,
  ...
}:
{
  env = {
    AWS_CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt";
    AWS_ACCESS_KEY_ID = config.secretspec.secrets.AWS_ACCESS_KEY_ID or "";
    AWS_SECRET_ACCESS_KEY = config.secretspec.secrets.AWS_SECRET_ACCESS_KEY or "";
    GITHUB_TOKEN = config.secretspec.secrets.GITHUB_TOKEN or "";
    PULUMI_CONFIG_PASSPHRASE = config.secretspec.secrets.PULUMI_CONFIG_PASSPHRASE or "";
  };

  packages = [
    pkgs.secretspec
    pkgs.pulumi
  ];

  languages.python = {
    enable = true;
    version = lib.strings.trim (builtins.readFile ./.python-version);
    venv.enable = true;
    uv = {
      enable = true;
      sync = {
        enable = true;
        allExtras = true;
      };
    };
  };

  tasks = {
    "pulumi:setup" = {
      exec = "
        pulumi login 's3://pulumi?region=eu-west-1&endpoint=https://nas.unicornafk.fr:30292&s3ForcePathStyle=true'
        pulumi stack select prod
      ";
    };
    "devenv:enterShell".after = [ "pulumi:setup" ];
  };
}
